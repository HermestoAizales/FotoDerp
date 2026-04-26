const { contextBridge, ipcRenderer } = require('electron');

// Expose a safe API to the renderer process
contextBridge.exposeInMainWorld('fotoerp', {
  // Backend communication
  backendRequest: (method, endpoint, data) => 
    ipcRenderer.invoke('backend-request', method, endpoint, data),
  
  // App info
  getAppVersion: () => require('electron').remote.app.getVersion(),
  getPlatform: () => process.platform,
  
  // File system (sandboxed)
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),
  openFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
});
