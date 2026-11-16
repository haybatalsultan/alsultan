const fs = require('fs');
const path = require('path');

/**
 * Haybat Al Sultan PRO - مدير إعدادات سحابة Turso وقاعدة البيانات الموزعة
 */

function getCloudConfigDir() {
  if (process.env.HAYBAT_CONFIG_DIR) {
    return process.env.HAYBAT_CONFIG_DIR;
  }
  if (__dirname.includes('app.asar')) {
    const appData = process.env.APPDATA || (process.platform === 'darwin' ? process.env.HOME + '/Library/Application Support' : '/var/local');
    return path.join(appData, 'haybatalsultan-pro');
  }
  return __dirname;
}

function getCloudConfigPath() {
  const dir = getCloudConfigDir();
  try {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  } catch (e) {}
  return path.join(dir, 'turso_cloud_config.json');
}

const DEFAULT_CONFIG = {
  turso_url: '',
  turso_auth_token: '',
  sync_interval: '5m',
  last_sync_time: null,
  last_sync_status: 'disconnected',
  last_sync_error: null,
  is_active: false
};

function getCloudConfig() {
  const filePath = getCloudConfigPath();
  try {
    if (fs.existsSync(filePath)) {
      const raw = fs.readFileSync(filePath, 'utf8');
      const parsed = JSON.parse(raw);
      return {
        ...DEFAULT_CONFIG,
        ...parsed
      };
    }
  } catch (err) {
    console.error('❌ [CloudConfig] Error reading config file:', err.message);
  }
  return { ...DEFAULT_CONFIG };
}

function saveCloudConfig(newConfig) {
  const filePath = getCloudConfigPath();
  try {
    const current = getCloudConfig();
    const merged = { ...current, ...newConfig };
    fs.writeFileSync(filePath, JSON.stringify(merged, null, 2), 'utf8');
    return { success: true, config: merged };
  } catch (err) {
    console.error('❌ [CloudConfig] Error saving config file:', err.message);
    return { success: false, error: err.message };
  }
}

module.exports = {
  getCloudConfig,
  saveCloudConfig,
  getCloudConfigPath
};
