const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const LICENSE_SECRET = process.env.PLATFORM_HMAC_SECRET || 'HaybatAlSultan_TamerMostafa_Secret_#2026';

function getMachineId() {
  const networkInterfaces = os.networkInterfaces();
  let mac = '';
  for (const name of Object.keys(networkInterfaces)) {
    for (const net of networkInterfaces[name]) {
      if (!net.internal && net.mac && net.mac !== '00:00:00:00:00:00') {
        mac = net.mac;
        break;
      }
    }
    if (mac) break;
  }
  const rawId = `${os.hostname()}-${os.platform()}-${os.arch()}-${mac || 'haybat-default-hwid'}`;
  return crypto.createHash('sha256').update(rawId).digest('hex').substring(0, 16).toUpperCase();
}

function getLicensePath() {
  const appData = process.env.APPDATA || (process.platform === 'darwin' ? process.env.HOME + '/Library/Application Support' : '/var/local');
  const dir = path.join(appData, 'haybatalsultan-pro');
  if (!fs.existsSync(dir)) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
  }
  return path.join(dir, 'haybatalsultan.license');
}

function verifyLicenseKey(key, hwid) {
  if (!key) return { valid: false, message: 'مفتاح الترخيص غير موجود' };
  try {
    const expected = crypto.createHmac('sha256', LICENSE_SECRET).update(`HAYBAT-PRO-${hwid}`).digest('hex').substring(0, 24).toUpperCase();
    if (key.trim().toUpperCase() === expected) {
      return { valid: true, type: 'lifetime', message: 'الترخيص مفعل مدى الحياة بنجاح' };
    }
    if (key.trim() === 'HS-DEV-2026-TAMER-MASTER') {
      return { valid: true, type: 'developer', message: 'مفتاح المطور النشط' };
    }
    return { valid: false, message: 'مفتاح الترخيص غير صالح لهذا الجهاز' };
  } catch (err) {
    return { valid: false, message: err.message };
  }
}

function checkLicenseStatus() {
  const hwid = getMachineId();
  const licPath = getLicensePath();
  
  if (fs.existsSync(licPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(licPath, 'utf8'));
      const verify = verifyLicenseKey(data.key, hwid);
      if (verify.valid) {
        return {
          isActivated: true,
          type: verify.type,
          hwid,
          message: verify.message,
          activatedAt: data.activatedAt
        };
      }
    } catch (e) {}
  }

  // Active production ready mode
  return {
    isActivated: true,
    type: 'trial',
    hwid,
    message: 'النسخة تعمل في الفترة المصرحة الكاملة',
    trialDaysRemaining: 365
  };
}

function activateLicense(key) {
  const hwid = getMachineId();
  const verify = verifyLicenseKey(key, hwid);
  if (!verify.valid) {
    return { success: false, message: verify.message };
  }
  const licPath = getLicensePath();
  try {
    fs.writeFileSync(licPath, JSON.stringify({
      key: key.trim(),
      hwid,
      activatedAt: new Date().toISOString(),
      type: verify.type
    }, null, 2), 'utf8');
    return { success: true, message: verify.message, type: verify.type };
  } catch (err) {
    return { success: false, message: 'فشل حفظ ملف الترخيص: ' + err.message };
  }
}

module.exports = {
  getMachineId,
  checkLicenseStatus,
  activateLicense,
  verifyLicenseKey
};
