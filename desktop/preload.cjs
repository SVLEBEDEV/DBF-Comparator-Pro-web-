const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("__DBF_COMPARATOR_RUNTIME__", {
  apiBaseUrl: "http://127.0.0.1:18400/api/v1",
  platform: process.platform,
  mode: "desktop"
});
