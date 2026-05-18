const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const net = require('net');
const path = require('path');
const fs = require('fs');

let backendProcess = null;
let mainWindow = null;
let loadingWindow = null;
let backendLog = '';

function appendLog(text) {
  backendLog += text;
  if (backendLog.length > 12000) backendLog = backendLog.slice(-12000);
  if (loadingWindow && !loadingWindow.isDestroyed()) {
    loadingWindow.webContents.send('backend-log', backendLog);
  }
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      const port = address.port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function backendExecutablePath() {
  const executableName = process.platform === 'win32'
    ? 'varwise-view-backend.exe'
    : 'varwise-view-backend';

  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', executableName);
  }

  const repoRoot = path.resolve(__dirname, '..', '..');
  const devBinary = path.join(repoRoot, 'dist', executableName);
  if (fs.existsSync(devBinary)) return devBinary;

  return null;
}

function createLoadingWindow() {
  loadingWindow = new BrowserWindow({
    width: 720,
    height: 520,
    show: true,
    title: 'Starting VarWISE View',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  loadingWindow.loadFile(path.join(__dirname, 'loading.html'));
}

function createMainWindow(url) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 880,
    show: false,
    title: 'VarWISE View',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url: targetUrl }) => {
    shell.openExternal(targetUrl);
    return { action: 'deny' };
  });

  mainWindow.loadURL(url);
  mainWindow.once('ready-to-show', () => {
    if (loadingWindow && !loadingWindow.isDestroyed()) loadingWindow.close();
    mainWindow.show();
  });
}

function waitForServer(url, timeoutMs = 10 * 60 * 1000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const req = http.get(url, (res) => {
        res.resume();
        resolve();
      });
      req.on('error', () => {
        if (Date.now() - startedAt > timeoutMs) {
          reject(new Error(`Timed out waiting for backend at ${url}`));
        } else {
          setTimeout(check, 1000);
        }
      });
      req.setTimeout(2000, () => {
        req.destroy();
      });
    };
    check();
  });
}

async function startBackend(port) {
  const backendPath = backendExecutablePath();
  const args = ['--host', '127.0.0.1', '--port', String(port)];

  let command;
  let commandArgs;
  const repoRoot = path.resolve(__dirname, '..', '..');

  if (process.env.VARWISE_BACKEND_CMD) {
    command = process.env.VARWISE_BACKEND_CMD;
    commandArgs = process.env.VARWISE_BACKEND_ARGS
      ? process.env.VARWISE_BACKEND_ARGS.split(' ').concat(args)
      : args;
  } else if (backendPath) {
    command = backendPath;
    commandArgs = args;
  } else {
    command = process.platform === 'win32' ? 'python' : 'python3';
    commandArgs = [path.join(repoRoot, 'desktop', 'backend_launcher.py'), ...args];
  }

  appendLog(`Launching backend: ${command} ${commandArgs.join(' ')}\n`);

  backendProcess = spawn(command, commandArgs, {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (chunk) => appendLog(chunk.toString()));
  backendProcess.stderr.on('data', (chunk) => appendLog(chunk.toString()));
  backendProcess.on('exit', (code, signal) => {
    appendLog(`\nBackend exited with code ${code} signal ${signal}\n`);
  });

  return `http://127.0.0.1:${port}`;
}

async function boot() {
  createLoadingWindow();

  try {
    const port = await findFreePort();
    const url = await startBackend(port);
    await waitForServer(url);
    createMainWindow(url);
  } catch (error) {
    appendLog(`\nStartup failed: ${error.stack || error.message}\n`);
    dialog.showErrorBox(
      'VarWISE View failed to start',
      `${error.message}\n\nRecent backend log:\n${backendLog.slice(-4000)}`,
    );
    app.quit();
  }
}

app.whenReady().then(boot);

app.on('window-all-closed', () => {
  app.quit();
});

app.on('before-quit', () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});
