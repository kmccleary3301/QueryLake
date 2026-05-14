import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";

const AUTH_TOKEN = "querylake-smoke-auth-token";
const CHROMIUM = process.env.CHROMIUM_BIN ?? "/snap/bin/chromium";

const mockUser = {
  username: "qa-user",
  auth: AUTH_TOKEN,
  memberships: [
    {
      organization_id: "qa-org",
      organization_name: "QA Organization",
      role: "admin",
      invite_still_open: false,
    },
  ],
  is_admin: true,
  available_models: {
    llm: {
      default_model: {
        title: "Mock LLM",
        id: "mock-llm",
        model_description: "Authenticated smoke fixture model.",
      },
      local_models: [],
      external_models: [],
    },
  },
  available_toolchains: [
    {
      category: "Smoke",
      entries: [{ title: "Smoke Toolchain", id: "smoke-toolchain", category: "Smoke" }],
    },
  ],
  default_toolchain: { title: "Smoke Toolchain", id: "smoke-toolchain", category: "Smoke" },
  user_set_providers: [],
  providers: ["openai", "anthropic", "google"],
};

const ok = (result = {}) => ({ success: true, result });

function readJsonBody(req) {
  return new Promise((resolve) => {
    let body = "";
    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        resolve({});
      }
    });
  });
}

function createMockApiServer(mockApiPort) {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://127.0.0.1:${mockApiPort}`);
    if (req.method === "OPTIONS") {
      res.writeHead(204, corsHeaders());
      res.end();
      return;
    }

    const body = req.method === "POST" ? await readJsonBody(req) : {};
    let payload;

    switch (url.pathname) {
      case "/api/login":
        payload = body.auth === AUTH_TOKEN ? ok(mockUser) : { success: false, error: "Invalid smoke token" };
        break;
      case "/api/fetch_all_collections":
        payload = ok({
          collections: {
            user_collections: [
              { name: "Smoke Personal Collection", hash_id: "personal-smoke", document_count: 3, type: "document" },
            ],
            global_collections: [
              { name: "Smoke Global Collection", hash_id: "global-smoke", document_count: 2, type: "document" },
            ],
            organization_collections: {
              "qa-org": {
                name: "QA Organization",
                collections: [
                  { name: "Smoke Org Collection", hash_id: "org-smoke", document_count: 5, type: "document" },
                ],
              },
            },
          },
        });
        break;
      case "/api/fetch_toolchain_sessions":
        payload = ok([
          { title: "Smoke Run", toolchain: "smoke-toolchain", id: "smoke-run", time: Math.floor(Date.now() / 1000) },
        ]);
        break;
      case "/api/fetch_toolchain_config":
        payload = ok({ id: "smoke-toolchain", title: "Smoke Toolchain", category: "Smoke", nodes: [], edges: [] });
        break;
      case "/api/get_usage_tally":
        payload = ok([
          {
            start_timestamp: Math.floor(Date.now() / 1000),
            organization_id: null,
            id: "usage-smoke",
            user_id: "qa-user",
            value: { requests: 1 },
            window: "day",
            api_key_id: null,
          },
        ]);
        break;
      case "/api/function_help":
        payload = ok([]);
        break;
      default:
        payload = ok({});
        break;
    }

    res.writeHead(200, { ...corsHeaders(), "content-type": "application/json" });
    res.end(JSON.stringify(payload));
  });
}

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
    "access-control-allow-headers": "content-type",
  };
}

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(Number(port), "127.0.0.1", () => resolve());
  });
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.once("error", reject);
    server.listen(0, () => {
      const address = server.address();
      const port = address && typeof address === "object" ? address.port : undefined;
      server.close(() => {
        if (port === undefined) reject(new Error("Unable to allocate a free port"));
        else resolve(String(port));
      });
    });
  });
}

function nextEnv(mockApiPort) {
  return {
    ...process.env,
    NODE_ENV: "production",
    QUERYLAKE_STUDIO_API_BASE_URL: `http://127.0.0.1:${mockApiPort}`,
  };
}

function runCommand(command, args, options = {}) {
  const child = spawn(command, args, {
    stdio: "inherit",
    env: options.env ?? process.env,
  });

  return new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(" ")} failed with ${signal ?? code}`));
    });
  });
}

async function buildNextForMockApi(mockApiPort) {
  console.log(`Building production app with QUERYLAKE_STUDIO_API_BASE_URL=http://127.0.0.1:${mockApiPort}`);
  await runCommand("npx", ["next", "build"], { env: nextEnv(mockApiPort) });
}

function startNext(mockApiPort, appPort) {
  return spawn("npx", ["next", "start", "-p", appPort], {
    stdio: ["ignore", "pipe", "pipe"],
    env: nextEnv(mockApiPort),
  });
}

async function waitForServer(baseUrl, child) {
  for (let i = 0; i < 80; i++) {
    if (child.exitCode !== null) {
      throw new Error(`Next server exited before becoming ready with code ${child.exitCode}`);
    }
    try {
      const res = await fetch(`${baseUrl}/`, { redirect: "manual" });
      if (res.status > 0) return;
    } catch {
      // keep waiting
    }
    await delay(500);
  }
  throw new Error(`Timed out waiting for Next at ${baseUrl}`);
}

async function waitForCdp(cdpPort) {
  for (let i = 0; i < 80; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
      if (res.ok) return await res.json();
    } catch {
      // keep waiting
    }
    await delay(250);
  }
  throw new Error(`Timed out waiting for Chromium CDP on port ${cdpPort}`);
}

class CdpClient {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.handlers = new Map();

    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(message.error.message));
        else resolve(message.result ?? {});
        return;
      }
      if (message.method && this.handlers.has(message.method)) {
        for (const handler of this.handlers.get(message.method)) handler(message.params ?? {});
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    const payload = JSON.stringify({ id, method, params });
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(payload);
    });
  }

  on(method, handler) {
    const handlers = this.handlers.get(method) ?? [];
    handlers.push(handler);
    this.handlers.set(method, handlers);
  }
}

async function openPageTarget(url, cdpPort) {
  const res = await fetch(`http://127.0.0.1:${cdpPort}/json/new?${encodeURIComponent(url)}`, {
    method: "PUT",
  });
  if (!res.ok) throw new Error(`Unable to create Chromium target: ${res.status}`);
  return await res.json();
}

async function connectCdp(wsUrl) {
  const socket = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  return new CdpClient(socket);
}

async function waitForExpression(cdp, expression, label, timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const result = await cdp.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.result?.value) return;
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function getLocationPath(cdp) {
  const result = await cdp.send("Runtime.evaluate", {
    expression: "window.location.pathname",
    returnByValue: true,
  });
  return result.result?.value;
}

async function navigate(cdp, url) {
  await cdp.send("Page.navigate", { url });
  await waitForExpression(cdp, "document.readyState === 'complete'", `document ready at ${url}`);
}

async function main() {
  const mockApiPort = process.env.QUERYLAKE_MOCK_API_PORT ?? await getFreePort();
  const appPort = process.env.PORT ?? await getFreePort();
  const cdpPort = process.env.QUERYLAKE_SMOKE_CDP_PORT ?? await getFreePort();
  const baseUrl = `http://127.0.0.1:${appPort}`;
  const mockApi = createMockApiServer(mockApiPort);
  const profileDir = await mkdtemp(path.join(os.tmpdir(), "ql-auth-smoke-"));
  let next;
  let chromium;
  let cdp;
  const browserMessages = [];

  const stopProcess = (child) => {
    if (!child || child.killed) return;
    child.kill("SIGTERM");
    setTimeout(() => {
      if (!child.killed) child.kill("SIGKILL");
    }, 1500).unref();
  };

  const closeServer = (server) =>
    new Promise((resolve) => {
      server.closeAllConnections?.();
      server.close(() => resolve());
    });

  const cleanup = async () => {
    if (cdp?.socket?.readyState === WebSocket.OPEN) cdp.socket.close();
    stopProcess(chromium);
    stopProcess(next);
    await closeServer(mockApi);
    await rm(profileDir, { recursive: true, force: true });
  };

  process.on("SIGINT", async () => {
    await cleanup();
    process.exit(130);
  });
  process.on("SIGTERM", async () => {
    await cleanup();
    process.exit(143);
  });

  try {
    await listen(mockApi, mockApiPort);
    console.log(`Mock QueryLake API listening on 127.0.0.1:${mockApiPort}`);

    await buildNextForMockApi(mockApiPort);

    next = startNext(mockApiPort, appPort);
    next.stdout.on("data", (chunk) => process.stdout.write(chunk));
    next.stderr.on("data", (chunk) => process.stderr.write(chunk));
    await waitForServer(baseUrl, next);

    chromium = spawn(CHROMIUM, [
      "--headless=new",
      "--no-sandbox",
      "--disable-gpu",
      `--remote-debugging-port=${cdpPort}`,
      `--user-data-dir=${profileDir}`,
      "about:blank",
    ], { stdio: ["ignore", "ignore", "pipe"] });
    chromium.stderr.on("data", (chunk) => process.stderr.write(chunk));
    await waitForCdp(cdpPort);

    const target = await openPageTarget("about:blank", cdpPort);
    cdp = await connectCdp(target.webSocketDebuggerUrl);
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Network.enable");

    cdp.on("Runtime.consoleAPICalled", (event) => {
      const text = event.args?.map((arg) => arg.value ?? arg.description ?? "").join(" ") ?? "";
      browserMessages.push(`${event.type}: ${text}`);
    });
    cdp.on("Runtime.exceptionThrown", (event) => {
      browserMessages.push(`exception: ${event.exceptionDetails?.text ?? "unknown"}`);
    });

    await cdp.send("Network.setCookie", {
      name: "UD",
      value: AUTH_TOKEN,
      url: baseUrl,
      path: "/",
    });

    await navigate(cdp, `${baseUrl}/select-workspace`);
    await waitForExpression(
      cdp,
      "document.body.innerText.includes('qa-user (Personal)') && document.body.innerText.includes('QA Organization')",
      "authenticated workspace selector"
    );

    await navigate(cdp, `${baseUrl}/w/personal/dashboard`);
    await waitForExpression(
      cdp,
      "document.body.innerText.includes('Workspace dashboard') && document.body.innerText.includes('Operational view of collections') && !document.body.innerText.includes('Authentication required')",
      "authenticated workspace dashboard"
    );

    const locationPath = await getLocationPath(cdp);
    if (locationPath !== "/w/personal/dashboard") {
      throw new Error(`Expected to remain on /w/personal/dashboard, got ${locationPath}`);
    }

    const jotaiWarnings = browserMessages.filter((message) =>
      message.includes("Detected multiple Jotai instances")
    );
    if (jotaiWarnings.length > 0) {
      throw new Error(`Multiple-Jotai warning still present: ${jotaiWarnings.join(" | ")}`);
    }

    console.log("OK authenticated smoke: workspace selector and dashboard rendered without multiple-Jotai warning");
  } finally {
    await cleanup();
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
