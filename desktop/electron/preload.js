const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('varwiseDesktop', {
  onBackendLog(callback) {
    ipcRenderer.on('backend-log', (_event, log) => callback(log));
  },
});
