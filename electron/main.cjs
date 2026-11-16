const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let serverInstance = null;
const SERVER_PORT = parseInt(process.env.PORT || '3001', 10);

function getLogFilePath() {
  try {
    return path.join(app.getPath('userData'), 'haybatalsultan.log');
  } catch (e) {
    return path.join(__dirname, '..', 'haybatalsultan.log');
  }
}

function appLog(...args) {
  const line = `[${new Date().toISOString()}] ${args.map(a => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' ')}\n`;
  console.log(...args);
  try {
    fs.appendFileSync(getLogFilePath(), line, 'utf8');
  } catch (e) {}
}

process.on('uncaughtException', (err) => {
  appLog('❌ [Electron] Uncaught Exception:', err?.stack || err);
});
process.on('unhandledRejection', (reason) => {
  appLog('❌ [Electron] Unhandled Rejection:', reason?.stack || reason);
});

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  appLog('[Electron] Another instance is already running. Quitting.');
  app.quit();
  process.exit(0);
}

app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'هيبة السلطان برو - Haybat Al Sultan PRO',
    icon: path.join(__dirname, '..', 'public', 'favicon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
    autoHideMenuBar: true,
    show: false
  });

  const appUrl = `http://localhost:${SERVER_PORT}`;
  
  mainWindow.loadURL(appUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.maximize();
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startEmbeddedServer() {
  return new Promise((resolve) => {
    try {
      const serverScript = path.join(__dirname, '..', 'server_libsql.cjs');
      process.env.PORT = String(SERVER_PORT);
      process.env.ELECTRON_ENV = '1';
      require(serverScript);
      appLog(`[Electron] Embedded server started on port ${SERVER_PORT}`);
      setTimeout(resolve, 800);
    } catch (err) {
      appLog('❌ [Electron] Failed to start embedded server:', err);
      resolve();
    }
  });
}

app.whenReady().then(async () => {
  appLog('[Electron] App is ready. Initializing engine...');
  await startEmbeddedServer();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
