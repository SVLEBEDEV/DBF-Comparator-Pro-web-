const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const API_PORT = 18400;
const UI_PORT = 18401;

let backendProcess = null;

function ensureDir(targetPath) {
  fs.mkdirSync(targetPath, { recursive: true });
  return targetPath;
}

function buildSqliteUrl(filePath) {
  const normalized = filePath.split(path.sep).join("/");
  return `sqlite:///${normalized.startsWith("/") ? "" : "/"}${normalized}`;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForBackendReady() {
  const healthUrl = `http://127.0.0.1:${API_PORT}/api/v1/health`;

  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(healthUrl);
      if (response.ok) {
        return;
      }
    } catch {}

    await wait(500);
  }

  throw new Error("Local backend did not start in time.");
}

function resolveBackendCommand() {
  if (!app.isPackaged) {
    return {
      command: process.env.DBF_DESKTOP_PYTHON ?? "python",
      args: [
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        String(API_PORT)
      ],
      cwd: path.resolve(__dirname, "../backend"),
      envFile: path.resolve(__dirname, "../backend/.env.desktop")
    };
  }

  const backendRoot = path.join(process.resourcesPath, "backend");
  const executableName = process.platform === "win32" ? "dbf-comparator-backend.exe" : "dbf-comparator-backend";

  return {
    command: path.join(backendRoot, executableName),
    args: [],
    cwd: backendRoot,
    envFile: path.join(backendRoot, ".env")
  };
}

function buildBackendEnv(envFile) {
  const baseEnv = { ...process.env };

  if (fs.existsSync(envFile)) {
    const lines = fs.readFileSync(envFile, "utf8").split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) {
        continue;
      }

      const separatorIndex = trimmed.indexOf("=");
      if (separatorIndex === -1) {
        continue;
      }

      const key = trimmed.slice(0, separatorIndex).trim();
      const value = trimmed.slice(separatorIndex + 1).trim();
      baseEnv[key] = value;
    }
  }

  const dataRoot = ensureDir(path.join(app.getPath("userData"), "runtime"));
  const logsRoot = ensureDir(path.join(dataRoot, "logs"));
  const backendRoot = ensureDir(path.join(dataRoot, "backend"));
  const storageRoot = ensureDir(path.join(dataRoot, "storage"));

  baseEnv.DATABASE_URL = buildSqliteUrl(path.join(backendRoot, "desktop-app.sqlite"));
  baseEnv.TEMP_STORAGE_ROOT = storageRoot;
  baseEnv.LOG_PATH = path.join(logsRoot, "backend.log");
  baseEnv.PORT = String(API_PORT);
  return baseEnv;
}

function startBackend() {
  const runtime = resolveBackendCommand();
  const env = buildBackendEnv(runtime.envFile);
  const logPath = env.LOG_PATH;
  const logStream = fs.createWriteStream(logPath, { flags: "a" });

  backendProcess = spawn(runtime.command, runtime.args, {
    cwd: runtime.cwd,
    env,
    stdio: ["ignore", "pipe", "pipe"]
  });

  backendProcess.stdout.on("data", (chunk) => {
    logStream.write(chunk);
  });

  backendProcess.stderr.on("data", (chunk) => {
    logStream.write(chunk);
  });

  backendProcess.on("exit", (code) => {
    logStream.end();
    backendProcess = null;
    if (code !== 0) {
      dialog.showErrorBox(
        "DBF Comparator Pro",
        `Local backend stopped with code ${code ?? "unknown"}.\n\nLog: ${logPath}`,
      );
    }
  });
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 980,
    minWidth: 1180,
    minHeight: 800,
    backgroundColor: "#f3efe7",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs")
    }
  });

  if (!app.isPackaged) {
    window.loadURL(`http://127.0.0.1:${UI_PORT}`);
    return;
  }

  window.loadFile(path.join(process.resourcesPath, "frontend", "index.html"));
}

app.whenReady().then(async () => {
  startBackend();

  try {
    await waitForBackendReady();
  } catch (error) {
    dialog.showErrorBox("DBF Comparator Pro", String(error));
    app.quit();
    return;
  }

  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
