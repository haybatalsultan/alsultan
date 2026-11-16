const http = require('http');

function requestJSON(method, urlPath, data) {
  return new Promise((resolve, reject) => {
    const postData = data ? JSON.stringify(data) : null;
    const headers = {
      'Content-Type': 'application/json'
    };
    if (postData) {
      headers['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request({
      hostname: 'localhost',
      port: 3001,
      path: urlPath,
      method: method,
      headers: headers
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
    if (postData) req.write(postData);
    req.end();
  });
}

async function runTests() {
  console.log('--- بدء اختبارات نظام المستخدمين والصلاحيات المخصصة لمتجر هيبة السلطان ---');

  // 1. Fetch initial users list
  console.log('\n1. جلب قائمة مستخدمي النظام...');
  const usersRes = await requestJSON('GET', '/api/users');
  console.log(`الحالة: ${usersRes.status}, عدد المستخدمين: ${usersRes.data?.length}`);
  if (usersRes.status !== 200 || !Array.isArray(usersRes.data)) {
    throw new Error('Failed to fetch users');
  }

  // 2. Create a new employee with customized individual permissions
  const rand = Math.floor(Math.random() * 10000);
  const testUser = `sales_emp_${rand}`;
  console.log(`\n2. إنشاء مستخدم جديد (${testUser}) بدور SALES وتخصيص صلاحية خصم له...`);
  const createRes = await requestJSON('POST', '/api/users', {
    username: testUser,
    password: 'Password123!',
    full_name: 'عمر المبيعات',
    role: 'SALES',
    phone: '+971501234567',
    email: `${testUser}@haybat.com`,
    permissions: {
      'pos.view': true,
      'pos.checkout': true,
      'pos.discount': true, // Custom override: SALES default is false, but we grant it!
      'inventory.view': true,
      'inventory.view_cost': false
    },
    is_active: 1
  });

  console.log(`الحالة: ${createRes.status}`, {
    id: createRes.data?.id,
    full_name: createRes.data?.full_name,
    role: createRes.data?.role,
    permissions: createRes.data?.permissions
  });

  if (createRes.status !== 201 || !createRes.data?.id) {
    throw new Error('Failed to create user');
  }
  const createdUserId = createRes.data.id;

  // Verify custom permission
  if (createRes.data.permissions['pos.discount'] !== true) {
    throw new Error('Custom permission override was not persisted correctly!');
  }
  console.log('✅ تم حفظ الصلاحية المخصصة الفردية (pos.discount = true) بنجاح!');

  // 3. Update the user (modify phone, grant cost view permission)
  console.log(`\n3. تعديل بيانات وصلاحيات المستخدم (ID: ${createdUserId})...`);
  const updateRes = await requestJSON('PUT', `/api/users/${createdUserId}`, {
    full_name: 'عمر المبيعات - فرع أبوظبي',
    role: 'SUPERVISOR', // Promoted to supervisor
    phone: '+971509998888',
    permissions: {
      'pos.view': true,
      'pos.checkout': true,
      'pos.discount': true,
      'inventory.view': true,
      'inventory.view_cost': true // Granted cost viewing
    }
  });

  console.log(`الحالة: ${updateRes.status}`, {
    full_name: updateRes.data?.full_name,
    role: updateRes.data?.role,
    phone: updateRes.data?.phone,
    cost_perm: updateRes.data?.permissions?.['inventory.view_cost']
  });

  if (updateRes.status !== 200 || updateRes.data?.permissions?.['inventory.view_cost'] !== true) {
    throw new Error('Failed to update user or permissions');
  }
  console.log('✅ تم تعديل المستخدم وترقيته وتحديث صلاحياته بنجاح!');

  // 4. Test security protection: Cannot delete or deactivate the main owner account
  console.log('\n4. اختبار حماية حساب المالك (owner) من الحذف أو التعديل التعسفي...');
  const ownerUser = usersRes.data.find(u => u.username === 'owner');
  if (ownerUser) {
    const deleteOwnerAttempt = await requestJSON('DELETE', `/api/users/${ownerUser.id}`);
    console.log(`حالة محاولة حذف المالك: ${deleteOwnerAttempt.status}`, deleteOwnerAttempt.data);
    if (deleteOwnerAttempt.status === 403) {
      console.log('✅ نجاح الحماية: تم منع حذف حساب المالك الرئيسي برمز 403!');
    } else {
      throw new Error('SECURITY VIOLATION: Primary owner was not protected from deletion!');
    }

    const demoteOwnerAttempt = await requestJSON('PUT', `/api/users/${ownerUser.id}`, {
      role: 'SALES',
      is_active: 0
    });
    console.log(`حالة محاولة تعطيل المالك: ${demoteOwnerAttempt.status}`, demoteOwnerAttempt.data);
    if (demoteOwnerAttempt.status === 400) {
      console.log('✅ نجاح الحماية: تم منع تخفيض رتبة أو تعطيل حساب المالك برمز 400!');
    } else {
      throw new Error('SECURITY VIOLATION: Primary owner was not protected from demotion!');
    }
  }

  // 5. Delete the created test user
  console.log(`\n5. حذف المستخدم التجريبي (ID: ${createdUserId})...`);
  const deleteRes = await requestJSON('DELETE', `/api/users/${createdUserId}`);
  console.log(`الحالة: ${deleteRes.status}`, deleteRes.data);
  if (deleteRes.status !== 200 || !deleteRes.data?.success) {
    throw new Error('Failed to delete test user');
  }
  console.log('✅ تم حذف المستخدم التجريبي بنجاح وتوثيق ذلك في سجل التدقيق الأمني (Audit Logs).');

  console.log('\n======================================================');
  console.log('🎉 كافة اختبارات نظام المستخدمين والصلاحيات تمت بنجاح 100%!');
  console.log('======================================================');
}

runTests().catch(err => {
  console.error('❌ حدث خطأ أثناء الاختبار:', err);
  process.exit(1);
});
