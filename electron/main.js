const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let backendProcess = null;
const BACKEND_PORT = 8765;
const BACKEND_HOST = '127.0.0.1';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    titleBarStyle: 'hiddenInset',  // macOS native look
    frame: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Load the frontend
  mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html'));

  // Open DevTools in dev mode
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function checkBackend() {
  return new Promise((resolve) => {
    const req = http.get(`http://${BACKEND_HOST}:${BACKEND_PORT}/health`, (res) => {
      if (res.statusCode === 200) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    req.on('error', () => resolve(false));
    req.setTimeout(3000, () => { req.destroy(); resolve(false); });
  });
}

async function startBackend() {
  // Check if backend is already running
  const ready = await checkBackend();
  if (ready) {
    console.log('[FotoDerp] Backend already running');
    return;
  }

  console.log('[FotoDerp] Starting backend...');
  
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

  // Wait for backend to be ready
  let attempts = 0;
  while (attempts < 30) {
    await new Promise(r => setTimeout(r, 1000));
    const ready = await checkBackend();
    if (ready) {
      console.log('[FotoDerp] Backend ready');
      return;
    }
    attempts++;
  }

  console.error('[FotoDerp] Backend failed to start');
}

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
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for Electron <-> Python backend communication
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
