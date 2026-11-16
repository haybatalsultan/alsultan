/**
 * HAYBAT AL SULTAN PRO - Build & Packaging Script
 * Generates an NSIS Windows installer setup.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const rootDir = path.resolve(__dirname, '..');
const packageJsonPath = path.join(rootDir, 'package.json');

function readPackageJson() {
  const content = fs.readFileSync(packageJsonPath, 'utf8');
  return JSON.parse(content);
}

function writePackageJson(data) {
  fs.writeFileSync(packageJsonPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function parseVersion(versionStr) {
  const parts = versionStr.split('.').map(n => parseInt(n, 10));
  if (parts.length !== 3 || parts.some(n => isNaN(n))) {
    return [1, 0, 0];
  }
  return parts;
}

function bumpPatch(versionStr) {
  const [major, minor, patch] = parseVersion(versionStr);
  return `${major}.${minor}.${patch + 1}`;
}

async function main() {
  const pkg = readPackageJson();
  const currentVersion = pkg.version || '1.0.0';
  const newVersion = bumpPatch(currentVersion);

  console.log(`\n\x1b[34m[1/3] Updating version: v${currentVersion} -> v${newVersion}...\x1b[0m`);
  pkg.version = newVersion;
  writePackageJson(pkg);

  console.log('\n\x1b[34m[2/3] Building frontend bundle (Vite Build)...\x1b[0m');
  const viteBuild = spawnSync('npm.cmd', ['run', 'build'], {
    cwd: rootDir,
    stdio: 'inherit',
    shell: true
  });

  if (viteBuild.status !== 0) {
    console.error('\x1b[31m[ERROR] Vite build failed.\x1b[0m');
    process.exit(1);
  }

  console.log('\n\x1b[34m[3/3] Creating Windows NSIS Installer...\x1b[0m');
  const electronBuilder = spawnSync('npx.cmd', ['electron-builder', '--win', 'nsis'], {
    cwd: rootDir,
    stdio: 'inherit',
    shell: true
  });

  if (electronBuilder.status !== 0) {
    console.error('\x1b[31m[ERROR] Electron packaging failed.\x1b[0m');
    process.exit(1);
  }

  console.log('\n\x1b[32m[SUCCESS] Windows Setup Created in release/ folder!\x1b[0m\n');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
