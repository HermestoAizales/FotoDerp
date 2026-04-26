const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');

let mainWindow;
let backendProcess = null;
const BACKEND_PORT = 8765;
const BACKEND_HOST = '127.0.0.1';

// --- Backend-Pfad ermitteln (Dev vs. Bundled) ---

function getBackendBinary() {
  // In bundled mode: electron-builder packt backend/dist/<platform>/fotoerp-backend
  // ins App-Verzeichnis. Pfad je nach Plattform:
  const appPath = app.getAppPath();
  const platform = process.platform;

  if (platform === 'win32') {
    const candidates = [
      path.join(appPath, 'backend', 'windows', 'fotoerp-backend.exe'),
      path.join(appPath, 'backend', 'fotoerp-backend.exe'),
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) return c;
    }
  } else if (platform === 'darwin') {
    const candidates = [
      path.join(appPath, 'backend', 'darwin-arm64', 'fotoerp-backend'),
      path.join(appPath, 'backend', 'darwin-x86_64', 'fotoerp-backend'),
      path.join(appPath, 'backend', 'fotoerp-backend'),
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) return c;
    }
  } else {
    const candidates = [
      path.join(appPath, 'backend', 'linux', 'fotoerp-backend'),
      path.join(appPath, 'backend', 'fotoerp-backend'),
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) return c;
    }
  }

  // Fallback: Dev-Modus — python3 + uvicorn
  return null;
}

function isDevMode() {
  return process.env.NODE_ENV === 'development' || !getBackendBinary();
}

// --- Backend starten ---

function checkBackend() {
  return new Promise((resolve) => {
    const req = http.get(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => { req.destroy(); resolve(false); });
  });
}

async function startBackend() {
  // Prüfen ob bereits laeufig
  const ready = await checkBackend();
  if (ready) {
    console.log('[FotoDerp] Backend already running');
    return;
  }

  console.log('[FotoDerp] Starting backend...');

  let binary = getBackendBinary();

  if (binary && !isDevMode()) {
    // --- Bundled Mode: Nuitka-compiled Binary ---
    console.log(`[FotoDerp] Using bundled backend: ${binary}`);

    backendProcess = spawn(binary, [], {
      stdio: 'pipe',
      detached: false,
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`[Backend] Process exited with code ${code}`);
      backendProcess = null;
    });

  } else {
    // --- Dev Mode: Python + uvicorn ---
    console.log('[FotoDerp] Using dev backend (python3 + uvicorn)');

    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const backendDir = path.join(__dirname, '..', 'backend');

    backendProcess = spawn(pythonPath, [
      '-m', 'uvicorn', 'fotoerp_backend.main:app',
      '--host', '0.0.0.0',
      '--port', String(BACKEND_PORT),
      '--log-level', 'info',
    ], {
      cwd: backendDir,
      stdio: 'pipe',
      env: { ...process.env, PYTHONPATH: backendDir },
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`[Backend] Process exited with code ${code}`);
      backendProcess = null;
    });
  }

  // Auf Ready warten
  let attempts = 0;
  const maxAttempts = isDevMode() ? 60 : 30;
  while (attempts < maxAttempts) {
    await new Promise(r => setTimeout(r, 500));
    if (await checkBackend()) {
      console.log('[FotoDerp] Backend ready');
      return;
    }
    attempts++;
  }

  console.error('[FotoDerp] Backend failed to start');
}

// --- App Lifecycle ---

app.whenReady().then(async () => {
  await startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Backend stoppen beim Schliessen
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Backend sauber beenden
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
  }
});

// --- Window ---

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    frame: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html'));

  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// --- IPC Bridge: Electron <-> Backend API ---

ipcMain.handle('backend-request', async (_event, method, endpoint, data) => {
  const url = `http://${BACKEND_HOST}:${BACKEND_PORT}${endpoint}`;

  return new Promise((resolve, reject) => {
    const options = {
      method: data ? (method || 'POST') : 'GET',
      headers: { 'Content-Type': 'application/json' },
    };

    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch {
          resolve(body);
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
});

// --- App Info ---

ipcMain.handle('app:getVersion', () => app.getVersion());

// --- File Dialogs (sandboxed) ---

ipcMain.handle('dialog:selectFolder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });
  if (result.canceled) return null;
  return result.filePaths;
});

ipcMain.handle('dialog:openFile', async (_event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', ...(options?.multi ? ['multiSelections'] : [])],
    ...options,
  });
  if (result.canceled) return null;
  return result.filePaths;
});

// --- Image Blob URLs (serve local images to renderer) ---

ipcMain.handle('file:imageBlobUrl', async (_event, filePath) => {
  if (!fs.existsSync(filePath)) return null;
  try {
    const fileBuffer = fs.readFileSync(filePath);
    const ext = path.extname(filePath).replace('.', '');
    const mimeTypes = {
      jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
      gif: 'image/gif', webp: 'image/webp', bmp: 'image/bmp',
      tiff: 'image/tiff', tif: 'image/tiff', heic: 'image/heic',
      heif: 'image/heif', raw: 'application/octet-stream',
      cr2: 'application/octet-stream', nef: 'application/octet-stream',
      arw: 'application/octet-stream', dng: 'application/octet-stream',
    };
    const mimeType = mimeTypes[ext] || 'image/jpeg';
    const base64 = fileBuffer.toString('base64');
    return `data:${mimeType};base64,${base64}`;
  } catch {
    return null;
  }
});
