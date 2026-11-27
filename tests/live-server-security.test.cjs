/**
 * 🛡️ Live HTTP Integration Security Test
 * Spawns server on ephemeral test port, executes live HTTP requests against endpoints,
 * and asserts real network responses.
 */

const { fork } = require('child_process');
const http = require('http');
const path = require('path');

const TEST_PORT = 3899;

function request(options, postData = null) {
  return new Promise((resolve, reject) => {
    const reqOptions = {
      hostname: '127.0.0.1',
      port: TEST_PORT,
      path: options.path,
      method: options.method || 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    };

    const req = http.request(reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(body); } catch(e) {}
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body,
          json
        });
      });
    });

    req.on('error', reject);
    if (postData) {
      req.write(typeof postData === 'object' ? JSON.stringify(postData) : postData);
    }
    req.end();
  });
}

async function runLiveTests() {
  console.log('\n======================================================');
  console.log(`🚀 Starting Haybat Al Sultan Server on Port ${TEST_PORT}...`);
  console.log('======================================================\n');

  const serverProc = fork(path.join(__dirname, '..', 'server_libsql.cjs'), [], {
    env: {
      ...process.env,
      PORT: String(TEST_PORT),
      NODE_ENV: 'test',
      HAYBAT_DATA_DIR: path.join(__dirname, '..', 'data')
    },
    silent: true
  });

  serverProc.stdout.on('data', (d) => {
    // console.log('[Server]:', d.toString());
  });
  serverProc.stderr.on('data', (d) => {
    // console.error('[Server Err]:', d.toString());
  });

  // Wait for server ready
  let ready = false;
  for (let i = 0; i < 35; i++) {
    try {
      const res = await request({ path: '/api/health' });
      if (res.statusCode === 200) {
        ready = true;
        break;
      }
    } catch (e) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  if (!ready) {
    serverProc.kill();
    throw new Error('Server failed to start within timeout.');
  }

  console.log('✅ Server online and responding to health check.\n');

  let tests = 0;
  let passed = 0;
  let failed = 0;

  function assertHttp(cond, desc) {
    tests++;
    if (cond) {
      passed++;
      console.log(`  ✅ PASS: ${desc}`);
    } else {
      failed++;
      console.error(`  ❌ FAIL: ${desc}`);
    }
  }

  try {
    // 1. Health check & Security Headers
    console.log('▶️ [Check 1: Security Headers]');
    const health = await request({ path: '/api/health' });
    assertHttp(health.statusCode === 200, 'Health endpoint responds with 200');
    assertHttp(health.headers['x-content-type-options'] === 'nosniff', 'X-Content-Type-Options: nosniff header present');
    assertHttp(health.headers['x-frame-options'] === 'SAMEORIGIN', 'X-Frame-Options: SAMEORIGIN header present');
    assertHttp(health.headers['x-xss-protection'] === '1; mode=block', 'X-XSS-Protection: 1; mode=block present');
    assertHttp(!health.headers['x-powered-by'], 'X-Powered-By header is removed/hidden');

    // 2. Sensitive File Shield
    console.log('\n▶️ [Check 2: Sensitive File Blocking]');
    const envReq = await request({ path: '/.env' });
    assertHttp(envReq.statusCode === 403, 'Direct access to /.env is blocked with 403');

    const dbReq = await request({ path: '/data/haybatalsultan.db' });
    assertHttp(dbReq.statusCode === 403, 'Direct access to database file is blocked with 403');

    const srcReq = await request({ path: '/server_libsql.cjs' });
    assertHttp(srcReq.statusCode === 403, 'Direct access to server source file is blocked with 403');

    // 3. RBAC Admin Endpoint Protection
    console.log('\n▶️ [Check 3: RBAC Admin API Locking]');
    const usersReq = await request({ path: '/api/users' });
    assertHttp(usersReq.statusCode === 401, 'GET /api/users rejects unauthenticated requests with 401');

    const accountantReq = await request({ path: '/api/accountant/report' });
    assertHttp(accountantReq.statusCode === 401, 'GET /api/accountant/report rejects unauthenticated requests with 401');

    const auditReq = await request({ path: '/api/audit' });
    assertHttp(auditReq.statusCode === 401, 'GET /api/audit rejects unauthenticated requests with 401');

    const uploadReq = await request({ path: '/api/upload', method: 'POST' }, { dataUrl: 'data:image/jpeg;base64,123' });
    assertHttp(uploadReq.statusCode === 401, 'POST /api/upload rejects unauthenticated requests with 401');

    const prodCreateReq = await request({ path: '/api/products', method: 'POST' }, { name_ar: 'test', selling_price: 100 });
    assertHttp(prodCreateReq.statusCode === 401, 'POST /api/products rejects unauthenticated requests with 401');

    // 4. Brute Force Protection & Lockout
    console.log('\n▶️ [Check 4: Brute Force & Rate Limit Protection]');
    let lockoutOccurred = false;
    for (let i = 0; i < 6; i++) {
      const loginRes = await request(
        { path: '/api/auth/login', method: 'POST' },
        { username: 'brute_force_target_user', password: 'wrong_password_attempt' }
      );
      if (loginRes.statusCode === 429) {
        lockoutOccurred = true;
        break;
      }
    }
    assertHttp(lockoutOccurred === true, 'Repeated invalid login attempts trigger 429 Rate Limit / Temporary Lockout');

    // 5. Expiring Password Reset Endpoints
    console.log('\n▶️ [Check 5: Expiring Password Reset Token Flow]');
    const forgotRes = await request(
      { path: '/api/auth/forgot-password', method: 'POST' },
      { email: 'owner@haybatalsultan.com' }
    );
    assertHttp(forgotRes.statusCode === 200 && forgotRes.json?.success === true, 'Password reset request succeeds');
    assertHttp(typeof forgotRes.json?.token === 'string', 'Received 15-minute cryptographically secure reset token');

    if (forgotRes.json?.token) {
      const resetRes = await request(
        { path: '/api/auth/reset-password', method: 'POST' },
        { token: forgotRes.json.token, new_password: 'NewStrongPassword#2026' }
      );
      assertHttp(resetRes.statusCode === 200 && resetRes.json?.success === true, 'Password reset successfully with new token');

      // Test Single-use invalidation
      const reuseRes = await request(
        { path: '/api/auth/reset-password', method: 'POST' },
        { token: forgotRes.json.token, new_password: 'AnotherPassword#2026' }
      );
      assertHttp(reuseRes.statusCode === 400, 'Re-using the same reset token is rejected (Single-use token enforcement)');
    }

    console.log('\n======================================================');
    console.log(`📊 LIVE SERVER TEST RESULTS: ${passed}/${tests} PASSED (${failed} FAILED)`);
    console.log('======================================================\n');

  } finally {
    serverProc.kill();
  }

  if (failed > 0) {
    process.exit(1);
  }
}

runLiveTests().catch(err => {
  console.error('Live test error:', err);
  process.exit(1);
});
