const http = require('http');

function postJSON(urlPath, data) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(data);
    const req = http.request({
      hostname: 'localhost',
      port: 3001,
      path: urlPath,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, raw: body });
        }
      });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

function getJSON(urlPath) {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: 'localhost',
      port: 3001,
      path: urlPath,
      method: 'GET'
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, raw: body });
        }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

async function runTests() {
  console.log('--- بدء اختبارات الفصل المعماري والأمان الصارم لمتجر هيبة السلطان ---');

  // Test 1: Register a new customer
  const randomSuffix = Math.floor(Math.random() * 10000);
  const customerUser = `client_${randomSuffix}`;
  const customerPhone = `+97150${Math.floor(1000000 + Math.random() * 9000000)}`;

  console.log(`\n1. تسجيل عميل متجر جديد (${customerUser})...`);
  const regRes = await postJSON('/api/auth/customer/register', {
    username: customerUser,
    password: 'Password123!',
    full_name: 'أحمد الشيخ',
    phone: customerPhone,
    email: `${customerUser}@gmail.com`
  });
  console.log(`الحالة: ${regRes.status}`, regRes.data);
  if (regRes.status !== 201) throw new Error('Customer registration failed');

  // Test 2: Customer logs in via customer portal
  console.log('\n2. تسجيل دخول العميل عبر واجهة المتجر...');
  const custLoginRes = await postJSON('/api/auth/customer/login', {
    identifier: customerUser,
    password: 'Password123!'
  });
  console.log(`الحالة: ${custLoginRes.status}`, custLoginRes.data.user);
  if (custLoginRes.status !== 200 || !custLoginRes.data.token) throw new Error('Customer login failed');

  // Test 3: Customer attempts to log into Admin Portal (/admin)
  console.log('\n3. محاولة العميل الدخول عبر بوابة الإدارة والموظفين (/admin)...');
  const adminBreachAttempt = await postJSON('/api/auth/admin/login', {
    identifier: customerUser,
    password: 'Password123!'
  });
  console.log(`الحالة: ${adminBreachAttempt.status}`);
  console.log(`الرد الأمني:`, adminBreachAttempt.data);

  if (adminBreachAttempt.status === 403 && adminBreachAttempt.data.error.includes('عملاء')) {
    console.log('✅ نجاح الحماية: تم رفض العميل فوراً بكود 403 ومنعه من دخول لوحة الإدارة ونقاط البيع!');
  } else {
    throw new Error('SECURITY VIOLATION: Customer was able to bypass admin gate or did not get 403 Forbidden!');
  }

  // Test 4: Staff/Owner logs into Admin Portal (/admin)
  console.log('\n4. تسجيل دخول المالك/الموظف المصرح (owner)...');
  const staffLoginRes = await postJSON('/api/auth/admin/login', {
    identifier: 'owner',
    password: 'Haybat@2026!Master'
  });
  console.log(`الحالة: ${staffLoginRes.status}`, {
    full_name: staffLoginRes.data?.user?.full_name,
    role: staffLoginRes.data?.user?.role
  });
  if (staffLoginRes.status !== 200 || staffLoginRes.data?.user?.role !== 'OWNER') {
    throw new Error('Staff login failed');
  }
  console.log('✅ نجاح تسجيل دخول الموظف المصرح.');

  // Test 5: Verify products and test online checkout
  console.log('\n5. جلب المعروضات المتاحة وإجراء طلب شراء أونلاين...');
  const productsRes = await getJSON('/api/products?status=AVAILABLE');
  if (productsRes.data.length === 0) {
    console.log('لا يوجد منتجات متاحة للاختبار، تم تخطي الشراء.');
  } else {
    const targetProduct = productsRes.data[0];
    console.log(`القطعة المختارة: ${targetProduct.name_ar} (ID: ${targetProduct.id}, السعر: ${targetProduct.selling_price} AED)`);

    const checkoutRes = await postJSON('/api/orders/checkout', {
      product_id: targetProduct.id,
      customer_name: 'أحمد الشيخ',
      customer_phone: customerPhone,
      customer_email: `${customerUser}@gmail.com`,
      city: 'أبوظبي',
      address: 'شارع الكورنيش - برج النخيل',
      notes: 'تغليف فاخر إضافي للهدايا',
      payment_method: 'CASH_ON_DELIVERY'
    });
    console.log(`حالة الطلب: ${checkoutRes.status}`, checkoutRes.data);
    if (checkoutRes.status !== 201) throw new Error('Checkout failed');

    // Test 6: Verify anti-double selling: the same product cannot be purchased again
    console.log('\n6. التحقق من منع الازدواج والبيع المكرر (Anti-Double-Selling)...');
    const secondBuyAttempt = await postJSON('/api/orders/checkout', {
      product_id: targetProduct.id,
      customer_name: 'عميل آخر',
      customer_phone: '+971509999999',
      city: 'دبي'
    });
    console.log(`حالة محاولة الشراء الثانية: ${secondBuyAttempt.status}`, secondBuyAttempt.data);
    if (secondBuyAttempt.status === 400 && (secondBuyAttempt.data.error.includes('مباعة') || secondBuyAttempt.data.error.includes('اقتناء'))) {
      console.log('✅ نجاح حماية الحصرية: تم منع البيع المكرر للقطعة بنجاح ومنع الازدواج المالي!');
    } else {
      throw new Error('Anti-double selling failed: sold item was sold again!');
    }

    // Test 7: Verify customer orders list
    console.log('\n7. جلب طلبات العميل من حسابه...');
    const myOrdersRes = await getJSON(`/api/customer/my-orders?phone=${encodeURIComponent(customerPhone)}`);
    console.log(`عدد طلبات العميل: ${myOrdersRes.data?.length || 0}`);
    if (myOrdersRes.data?.length > 0) {
      console.log(`رقم الطلب المرجعي: ${myOrdersRes.data[0].reference}`);
    }
  }

  console.log('\n======================================================');
  console.log('🎉 كافة اختبارات الفصل والأمان الصارم والواجهات تمت بنجاح 100%!');
  console.log('======================================================');
}

runTests().catch(err => {
  console.error('❌ حدث خطأ أثناء الاختبار:', err);
  process.exit(1);
});
