import { spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";

const dashboardUrl = process.env.DASHBOARD_URL ?? "http://127.0.0.1:3000";
const debugPort = Number(process.env.CHROME_DEBUG_PORT ?? 9223);
const screenshotPath = resolve(process.cwd(), "../../test_artifacts/dashboard-smoke.png");
const chromeCandidates = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
].filter(Boolean);

function findBrowser() {
  const browserPath = chromeCandidates.find((candidate) => existsSync(candidate));
  if (!browserPath) {
    throw new Error("No Chrome or Edge executable found. Set CHROME_PATH to run the dashboard smoke test.");
  }
  return browserPath;
}

function delay(ms) {
  return new Promise((resolveDelay) => {
    setTimeout(resolveDelay, ms);
  });
}

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function waitForDebugEndpoint() {
  const endpoint = `http://127.0.0.1:${debugPort}/json/version`;
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      return await fetchJson(endpoint);
    } catch {
      await delay(250);
    }
  }
  throw new Error(`Chrome DevTools endpoint did not start on port ${debugPort}.`);
}

async function createPageTarget() {
  const target = await fetchJson(`http://127.0.0.1:${debugPort}/json/new?${encodeURIComponent("about:blank")}`, {
    method: "PUT",
  });
  if (!target.webSocketDebuggerUrl) {
    throw new Error("Chrome did not return a page WebSocket URL.");
  }
  return target.webSocketDebuggerUrl;
}

async function createCdpClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  const pending = new Map();
  const events = [];
  let nextId = 1;

  await new Promise((resolveOpen, rejectOpen) => {
    socket.addEventListener("open", resolveOpen, { once: true });
    socket.addEventListener("error", rejectOpen, { once: true });
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolveMessage, rejectMessage } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) {
        rejectMessage(new Error(message.error.message));
      } else {
        resolveMessage(message.result ?? {});
      }
      return;
    }
    events.push(message);
  });

  return {
    events,
    close() {
      socket.close();
    },
    send(method, params = {}) {
      const id = nextId;
      nextId += 1;
      socket.send(JSON.stringify({ id, method, params }));
      return new Promise((resolveMessage, rejectMessage) => {
        pending.set(id, { resolveMessage, rejectMessage });
      });
    },
  };
}

async function evaluate(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    awaitPromise: true,
    expression,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text ?? "Runtime evaluation failed.");
  }
  return result.result?.value;
}

async function waitForArtifact(client) {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    const text = await evaluate(client, "document.body.innerText");
    if (/Campaign Package/i.test(text) && !/Running workflow/i.test(text)) {
      return text;
    }
    await delay(1000);
  }
  return evaluate(client, "document.body.innerText");
}

const userDataDir = resolve(tmpdir(), `agent-dashboard-smoke-${Date.now()}`);
const browserPath = findBrowser();
mkdirSync(dirname(screenshotPath), { recursive: true });

const browser = spawn(browserPath, [
  "--headless=new",
  "--disable-gpu",
  "--disable-extensions",
  "--disable-background-networking",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${userDataDir}`,
  "--window-size=1440,1100",
  "about:blank",
], {
  stdio: "ignore",
});

let client;

try {
  await waitForDebugEndpoint();
  client = await createCdpClient(await createPageTarget());
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("Log.enable");
  await client.send("Page.navigate", { url: dashboardUrl });
  await delay(4000);

  const beforeText = await evaluate(client, "document.body.innerText");
  const keyElements = await evaluate(
    client,
    `(() => ({
      heading: /Command center for multi-user agent workflows/i.test(document.body.innerText),
      commandButton: [...document.querySelectorAll("button")].some((button) => /Run agent workflow/i.test(button.innerText)),
      resultTabs: document.querySelectorAll('[role="tab"]').length,
      memory: /Short, Long, Checkpoint/i.test(document.body.innerText)
    }))()`,
  );
  const overlayStatus = await evaluate(
    client,
    `document.querySelector("[data-nextjs-dialog], .vite-error-overlay, #webpack-dev-server-client-overlay") ? "ERROR_OVERLAY" : "OK"`,
  );
  const clickStatus = await evaluate(
    client,
    `(() => {
      const button = [...document.querySelectorAll("button")].find((candidate) => /Run agent workflow/i.test(candidate.innerText));
      if (!button) return "missing";
      button.click();
      return "clicked";
    })()`,
  );
  const afterText = await waitForArtifact(client);
  const screenshot = await client.send("Page.captureScreenshot", {
    captureBeyondViewport: true,
    format: "png",
    fromSurface: true,
  });
  writeFileSync(screenshotPath, Buffer.from(screenshot.data, "base64"));

  const consoleIssues = client.events
    .filter((event) => event.method === "Runtime.consoleAPICalled" || event.method === "Log.entryAdded")
    .map((event) => event.params)
    .filter((event) => ["error", "warning"].includes(event.type ?? event.entry?.level));

  const report = {
    dashboardUrl,
    hasContent: beforeText.trim().length > 0,
    overlayStatus,
    keyElements,
    clickStatus,
    artifactVisible: /Campaign Package/i.test(afterText),
    checkpointVisible: /checkpoint/i.test(afterText),
    consoleIssues,
    screenshotPath,
  };

  console.log(JSON.stringify(report, null, 2));
  if (
    !report.hasContent ||
    report.overlayStatus !== "OK" ||
    !report.keyElements.heading ||
    clickStatus !== "clicked" ||
    !report.artifactVisible
  ) {
    process.exitCode = 1;
  }
} finally {
  client?.close();
  browser.kill();
  try {
    rmSync(userDataDir, { force: true, recursive: true });
  } catch {
    // Windows may keep the browser profile briefly locked after process shutdown.
  }
}
