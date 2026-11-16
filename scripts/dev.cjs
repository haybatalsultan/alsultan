const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Haybat Al Sultan PRO Services (Backend + Vite Frontend)...');

// 1. Start LibSQL Express Backend on port 3001
const server = spawn('node', ['server_libsql.cjs'], {
  stdio: 'inherit',
  shell: true
});

// 2. Start Vite Frontend on port 3000
const viteBin = process.platform === 'win32'
  ? path.resolve(__dirname, '..', 'node_modules', '.bin', 'vite.cmd')
  : path.resolve(__dirname, '..', 'node_modules', '.bin', 'vite');

const vite = spawn(`"${viteBin}"`, ['--port=3000', '--host=0.0.0.0'], {
  stdio: 'inherit',
  shell: true
});

server.on('error', (err) => {
  console.error('❌ Server process error:', err);
});

vite.on('error', (err) => {
  console.error('❌ Vite process error:', err);
});

function cleanup() {
  console.log('\n🛑 Shutting down Haybat Al Sultan services...');
  try { server.kill(); } catch (e) {}
  try { vite.kill(); } catch (e) {}
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
