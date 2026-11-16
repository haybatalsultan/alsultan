const http = require('http');
const path = require('path');
const { createClient } = require('@libsql/client');

function request(method, path, data = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const payload = data ? JSON.stringify(data) : null;
    const reqHeaders = {
      ...headers,
      ...(payload ? {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      } : {})
    };

    const req = http.request({
      hostname: 'localhost',
      port: 3001,
      path,
      method,
      headers: reqHeaders
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        let parsed = null;
        try {
          parsed = JSON.parse(body);
        } catch (e) {
          parsed = body;
        }
        resolve({ status: res.statusCode, data: parsed, headers: res.headers });
      });
    });

    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

async function runTests() {
  console.log('🚀 Starting Comprehensive B2B Hybrid System Verification...\n');

  try {
    // Ensure test catalog has available products
    const db = createClient({ url: 'file:' + path.join(__dirname, '..', 'data', 'haybatalsultan.db') });
    await db.execute("UPDATE products SET status = 'AVAILABLE', stock_quantity = 50, sales_channel = 'both', b2b_moq = 5, price_b2b = 3500 WHERE id = 1");

    // 1. Anti-Bot Honeypot Trap Test
    console.log('1️⃣ Testing Anti-Bot Honeypot Protection...');
    const botPayload = {
      username: 'spambot_' + Date.now(),
      company_name: 'Bot Enterprises',
      commercial_register: 'CR-BOT-000',
      tax_id: 'TRN-BOT-999',
      full_name: 'Robot Spammer',
      email: 'bot@spam.com',
      phone: '+971500000000',
      password: 'SpamPassword123!',
      website_hp: 'https://spam-link.ru' // Honeypot filled!
    };
    const botRes = await request('POST', '/api/auth/b2b/register', botPayload);
    if ((botRes.status === 200 || botRes.status === 201) && botRes.data.status === 'b2b_pending') {
      console.log('   ✅ Honeypot caught bot silently and returned dummy pending response.');
    } else {
      throw new Error(`Bot honeypot failed: ${JSON.stringify(botRes)}`);
    }

    // 2. Legitimate Wholesale Registration
    console.log('\n2️⃣ Testing Legitimate B2B Merchant Registration...');
    const rand = Math.floor(Math.random() * 9000 + 1000);
    const validMerchant = {
      username: `al_sultan_trading_${rand}`,
      company_name: `شركة قصر الياقوت لتجارة التحف ${rand}`,
      commercial_register: `CR-DXB-${rand}`,
      tax_id: `100${rand}992830003`,
      full_name: `سعيد عبد الرحمن بن هلال`,
      email: `saeed_${rand}@qasralyaqoot.ae`,
      phone: `+97150${rand}123`,
      password: `Merchant@Pass${rand}!`,
      website_hp: '' // Empty honeypot
    };
    const regRes = await request('POST', '/api/auth/b2b/register', validMerchant);
    if (regRes.status !== 201 || regRes.data.status !== 'b2b_pending') {
      throw new Error(`B2B registration failed: ${JSON.stringify(regRes)}`);
    }
    console.log(`   ✅ Merchant registered with status 'b2b_pending'`);

    // 3. Verify Admin Access Security Lockdown
    console.log('\n3️⃣ Verifying Security Isolation (B2B User attempting Admin Login)...');
    const adminBreachAttempt = await request('POST', '/api/auth/admin/login', {
      username: validMerchant.email,
      password: validMerchant.password
    });
    if (adminBreachAttempt.status === 403) {
      console.log('   🔒 Security check passed: Wholesale merchant is strictly blocked from Admin portal (403 Forbidden).');
    } else {
      throw new Error(`Admin lockdown failed, status: ${adminBreachAttempt.status}`);
    }

    // 4. Customer Login for Merchant
    console.log('\n4️⃣ Testing Merchant Login via Customer/B2B Auth...');
    const loginRes = await request('POST', '/api/auth/customer/login', {
      identifier: validMerchant.email,
      password: validMerchant.password
    });
    if (loginRes.status !== 200 || loginRes.data.user.role !== 'b2b_pending') {
      throw new Error(`Merchant login failed: ${JSON.stringify(loginRes)}`);
    }
    const merchantId = loginRes.data.user.id;
    const merchantToken = loginRes.data.token;
    console.log(`   ✅ Merchant logged in (ID: ${merchantId}). Token acquired.`);

    // 5. Verify Pending Merchant Cannot Access Wholesale Products or Place Wholesale Order
    console.log('\n5️⃣ Testing Pending Merchant Authorization Guard...');
    const b2bProdPending = await request('GET', '/api/b2b/products', null, {
      'Authorization': `Bearer ${merchantToken}`
    });
    if (b2bProdPending.status === 403) {
      console.log('   🔒 Access denied for unapproved merchant: Products restricted until approval.');
    } else {
      throw new Error(`Pending merchant should not access wholesale catalog: ${b2bProdPending.status}`);
    }

    // 6. Admin Approval Flow
    console.log('\n6️⃣ Testing Admin Review & Approval Flow...');
    // Admin login
    const adminLogin = await request('POST', '/api/auth/admin/login', {
      username: 'owner',
      password: 'Haybat@2026!Master'
    });
    if (adminLogin.status !== 200) {
      throw new Error(`Admin login failed: ${JSON.stringify(adminLogin)}`);
    }
    const adminToken = adminLogin.data.token;

    // Fetch merchants list
    const merchantsList = await request('GET', '/api/admin/b2b/merchants', null, {
      'Authorization': `Bearer ${adminToken}`
    });
    const list = Array.isArray(merchantsList.data) ? merchantsList.data : (merchantsList.data.merchants || []);
    const foundMerchant = list.find(m => m.id === merchantId);
    if (!foundMerchant || foundMerchant.role !== 'b2b_pending') {
      throw new Error('Merchant not found in admin review list');
    }
    console.log(`   📋 Admin retrieved merchant (${foundMerchant.company_name}) for review.`);

    // Approve merchant
    const approveRes = await request('POST', `/api/admin/b2b/approve/${merchantId}`, null, {
      'Authorization': `Bearer ${adminToken}`
    });
    if (approveRes.status !== 200 || !approveRes.data.success) {
      throw new Error(`Approval failed: ${JSON.stringify(approveRes)}`);
    }
    console.log('   🎉 Admin successfully approved merchant (role -> b2b_approved).');

    // 7. Verify Retail Data Isolation (Price Hiding)
    console.log('\n7️⃣ Testing Data Isolation & Catalog Segregation...');
    const retailProducts = await request('GET', '/api/products');
    const sampleRetailItem = retailProducts.data[0];
    if (sampleRetailItem && ('price_b2b' in sampleRetailItem || 'cost_price' in sampleRetailItem)) {
      throw new Error(`CRITICAL: Wholesale price or internal cost leaked in retail API! ${JSON.stringify(sampleRetailItem)}`);
    }
    console.log('   🛡️ Retail API verified: price_b2b and cost_price are strictly hidden from consumers.');

    // 8. Approved Merchant Access Wholesale Catalog
    console.log('\n8️⃣ Testing Approved Wholesale Merchant Catalog Access...');
    const b2bProdApproved = await request('GET', '/api/b2b/products', null, {
      'Authorization': `Bearer ${merchantToken}`
    });
    if (b2bProdApproved.status !== 200 || !Array.isArray(b2bProdApproved.data) || b2bProdApproved.data.length === 0) {
      throw new Error(`Failed to load B2B products: ${JSON.stringify(b2bProdApproved)}`);
    }
    const testWholesaleItem = b2bProdApproved.data[0];
    console.log(`   💎 Wholesale Catalog Loaded (${b2bProdApproved.data.length} items).`);
    console.log(`      Sample Item: "${testWholesaleItem.name_ar}" | B2B Price: ${testWholesaleItem.price_b2b} AED | MOQ: ${testWholesaleItem.b2b_moq} pcs`);

    // 9. Enforce MOQ Validation
    console.log('\n9️⃣ Testing MOQ (Minimum Order Quantity) Enforcement...');
    const subMoqOrder = {
      company_name: validMerchant.company_name,
      commercial_register: validMerchant.commercial_register,
      tax_id: validMerchant.tax_id,
      contact_name: validMerchant.full_name,
      phone: validMerchant.phone,
      payment_method: 'BANK_TRANSFER',
      items: [
        {
          id: testWholesaleItem.id,
          name: testWholesaleItem.name_ar,
          sku: testWholesaleItem.sku,
          quantity: Math.max(1, (testWholesaleItem.b2b_moq || 5) - 1), // Below MOQ
          unit_price: testWholesaleItem.price_b2b,
          b2b_moq: testWholesaleItem.b2b_moq || 5
        }
      ]
    };
    const subMoqRes = await request('POST', '/api/b2b/checkout', subMoqOrder, {
      'Authorization': `Bearer ${merchantToken}`
    });
    if (subMoqRes.status === 400 && subMoqRes.data.error.includes('أقل من الحد الأدنى')) {
      console.log(`   ⛔ MOQ validation verified: Order with quantity < ${testWholesaleItem.b2b_moq} was blocked with descriptive Arabic error.`);
    } else {
      throw new Error(`Order below MOQ was unexpectedly accepted: ${JSON.stringify(subMoqRes)}`);
    }

    // 10. Valid Wholesale Purchase Order Placement
    console.log('\n🔟 Testing Valid Wholesale Purchase Order (PO) Placement...');
    const validMoqOrder = {
      company_name: validMerchant.company_name,
      commercial_register: validMerchant.commercial_register,
      tax_id: validMerchant.tax_id,
      contact_name: validMerchant.full_name,
      phone: validMerchant.phone,
      payment_method: 'CREDIT_TERMS',
      shipping_address: 'دبي، شارع الشيخ زايد، برج الصفا، الطابق 14',
      notes: 'شحنة فاخرة لفرع المعرض - يرجى إرفاق شهادات الفحص الأصلية',
      items: [
        {
          id: testWholesaleItem.id,
          name: testWholesaleItem.name_ar,
          sku: testWholesaleItem.sku,
          quantity: (testWholesaleItem.b2b_moq || 5) + 2, // Valid MOQ
          unit_price: testWholesaleItem.price_b2b,
          b2b_moq: testWholesaleItem.b2b_moq || 5
        }
      ]
    };
    const poRes = await request('POST', '/api/b2b/checkout', validMoqOrder, {
      'Authorization': `Bearer ${merchantToken}`
    });
    if (poRes.status !== 201 || !poRes.data.order?.order_number?.startsWith('PO-')) {
      throw new Error(`Wholesale PO checkout failed: ${JSON.stringify(poRes)}`);
    }
    console.log(`   ✨ Wholesale Purchase Order successfully issued: ${poRes.data.order.order_number}`);
    console.log(`      Total Amount: ${poRes.data.order.total_amount} AED | Method: ${poRes.data.order.payment_method}`);
    console.log(`      Order Status: ${poRes.data.order.status}`);

    console.log('\n======================================================');
    console.log('🏆 ALL 10 HYBRID B2B / B2C SYSTEM TESTS PASSED SUCCESSFULLY!');
    console.log('======================================================');
  } catch (err) {
    console.error('\n❌ Test Suite Failed:', err.message || err);
    process.exit(1);
  }
}

runTests();
