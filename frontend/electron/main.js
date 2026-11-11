const { app, BrowserWindow, session } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

// Portrait kiosk: a 1280x720 monitor standing vertically => 720 wide x 1280 tall.
const WINDOW_WIDTH = 720;
const WINDOW_HEIGHT = 1280;
const PORT = Number(process.env.BOOTH_PORT || 3000);
const APP_URL = `http://localhost:${PORT}`;
const IS_DEV = process.env.BOOTH_DEV === "1";
const WINDOWED = process.env.BOOTH_WINDOWED === "1";
const SCREENSHOT_TO = process.env.BOOTH_SCREENSHOT;

let serverProcess = null;
let mainWindow = null;

function startNextServer() {
  const nextBin = path.join(__dirname, "..", "node_modules", ".bin", "next");
  const args = [IS_DEV ? "dev" : "start", "-p", String(PORT)];
  serverProcess = spawn(nextBin, args, {
    cwd: path.join(__dirname, ".."),
    stdio: "inherit",
    env: { ...process.env, PORT: String(PORT) },
  });
  serverProcess.on("exit", (code) => {
    if (!app.isQuitting) {
      console.error(`Next.js server exited with code ${code}`);
      app.quit();
    }
  });
}

function stopNextServer() {
  if (serverProcess && !serverProcess.killed) {
    serverProcess.kill("SIGTERM");
    serverProcess = null;
  }
}

function waitForServer(url, timeoutMs = 90000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const probe = () => {
      const request = http.get(url, (response) => {
        response.resume();
        resolve();
      });
      request.on("error", () => {
        if (Date.now() - startedAt > timeoutMs) {
          reject(new Error(`Timed out waiting for ${url}`));
        } else {
          setTimeout(probe, 400);
        }
      });
    };
    probe();
  });
}

function maybeCaptureScreenshot() {
  if (!SCREENSHOT_TO) return;
  mainWindow.webContents.once("did-finish-load", () => {
    (async () => {
      try {
        // With software rendering the first frames can be empty; retry until painted.
        for (let attempt = 1; attempt <= 10; attempt++) {
          await new Promise((resolve) => setTimeout(resolve, 1500));
          const image = await mainWindow.webContents.capturePage();
          const png = image.toPNG();
          if (png.length > 0) {
            fs.writeFileSync(SCREENSHOT_TO, png);
            console.log(`Screenshot saved to ${SCREENSHOT_TO}`);
            return;
          }
          console.log(`Screenshot attempt ${attempt}: empty frame, retrying...`);
        }
        console.error("Screenshot failed: empty frame after 10 attempts");
      } catch (error) {
        console.error("Screenshot failed", error);
      } finally {
        app.isQuitting = true;
        app.quit();
      }
    })();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    fullscreen: !WINDOWED,
    kiosk: !WINDOWED,
    autoHideMenuBar: true,
    backgroundColor: "#0b1021",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // The booth camera (getUserMedia) must work without a permission prompt.
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(permission === "media");
  });
  session.defaultSession.setPermissionCheckHandler((_wc, permission) => permission === "media");

  await waitForServer(APP_URL);
  await maybeCaptureScreenshot();
  await mainWindow.loadURL(APP_URL);
}

app.whenReady().then(() => {
  startNextServer();
  createWindow().catch((error) => {
    console.error(error);
    app.quit();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("will-quit", () => {
  app.isQuitting = true;
  stopNextServer();
});
