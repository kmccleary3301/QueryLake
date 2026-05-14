import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { setTimeout as delay } from "node:timers/promises";

const AUTH_TOKEN = "querylake-smoke-auth-token";
const CHROMIUM = process.env.CHROMIUM_BIN ?? "/snap/bin/chromium";
const OUTPUT_ROOT = path.resolve(
  process.cwd(),
  "..",
  "..",
  "docs_tmp",
  "FRONTEND",
  "4-21_REDESIGN",
  "QC_CONTACT_SHEETS_2026-04-23"
);

const ROUTES = [
  {
    slug: "auth_login",
    path: "/auth/login",
    label: "Auth Login",
    auth: false,
    waitFor: "document.body.innerText.includes('Log In') || document.body.innerText.includes('Username or Email')",
  },
  {
    slug: "workspace_select",
    path: "/select-workspace",
    label: "Workspace Select",
    auth: true,
    waitFor: "document.body.innerText.includes('qa-user (Personal)') && document.body.innerText.includes('QA Organization')",
  },
  {
    slug: "workspace_dashboard",
    path: "/w/personal/dashboard",
    label: "Workspace Dashboard",
    auth: true,
    waitFor: "document.body.innerText.includes('Workspace dashboard') && document.body.innerText.includes('Operational view of collections')",
  },
  {
    slug: "workspace_collections",
    path: "/w/personal/collections",
    label: "Workspace Collections",
    auth: true,
    waitFor: "document.body.innerText.includes('Collections')",
  },
  {
    slug: "workspace_files",
    path: "/w/personal/files",
    label: "Workspace Files",
    auth: true,
    waitFor: "document.body.innerText.includes('Files') || document.body.innerText.includes('Upload')",
  },
  {
    slug: "workspace_runs",
    path: "/w/personal/runs",
    label: "Workspace Runs",
    auth: true,
    waitFor: "document.body.innerText.includes('Runs')",
  },
  {
    slug: "workspace_toolchains",
    path: "/w/personal/toolchains",
    label: "Workspace Toolchains",
    auth: true,
    waitFor: "document.body.innerText.includes('Toolchains')",
  },
  {
    slug: "toolchain_detail",
    path: "/w/personal/toolchains/smoke-toolchain",
    label: "Toolchain Detail",
    auth: true,
    waitFor: "document.body.innerText.includes('Workflow detail') && document.body.innerText.includes('Open v2 editor')",
  },
  {
    slug: "toolchain_graph_editor",
    path: "/w/personal/toolchains/smoke-toolchain/edit/graph",
    label: "Toolchain Graph Editor",
    auth: true,
    waitFor: "document.body.innerText.includes('Toolchain studio') && document.body.innerText.includes('Graph')",
  },
  {
    slug: "toolchain_interface_editor",
    path: "/w/personal/toolchains/smoke-toolchain/edit/interface",
    label: "Toolchain Interface Editor",
    auth: true,
    waitFor: "document.body.innerText.includes('Toolchain studio') && document.body.innerText.includes('Interface')",
  },
  {
    slug: "platform_api_keys",
    path: "/w/personal/platform/api-keys",
    label: "Platform API Keys",
    auth: true,
    waitFor: "document.body.innerText.includes('API keys') || document.body.innerText.includes('API Keys') || document.body.innerText.includes('Create key')",
  },
  {
    slug: "account_preferences",
    path: "/account/preferences",
    label: "Account Preferences",
    auth: true,
    waitFor: "document.body.innerText.includes('Preferences')",
  },
];

const VIEWPORTS = [
  {
    slug: "desktop",
    label: "Desktop 2200x1500 @2x",
    width: 2200,
    height: 1500,
    deviceScaleFactor: 2,
    sheets: {
      core: [
        "auth_login",
        "workspace_select",
        "workspace_dashboard",
        "workspace_collections",
        "workspace_files",
        "workspace_runs",
        "workspace_toolchains",
        "platform_api_keys",
      ],
      toolchains: [
        "toolchain_detail",
        "toolchain_graph_editor",
        "toolchain_interface_editor",
        "account_preferences",
      ],
    },
  },
  {
    slug: "tablet",
    label: "Tablet 1600x1200 @2x",
    width: 1600,
    height: 1200,
    deviceScaleFactor: 2,
    sheets: {
      core: [
        "workspace_select",
        "workspace_dashboard",
        "workspace_collections",
        "workspace_files",
        "workspace_toolchains",
        "toolchain_graph_editor",
      ],
    },
  },
  {
    slug: "mobile",
    label: "Mobile 900x1600 @3x",
    width: 900,
    height: 1600,
    deviceScaleFactor: 3,
    sheets: {
      core: [
        "workspace_select",
        "workspace_dashboard",
        "workspace_toolchains",
        "toolchain_interface_editor",
      ],
    },
  },
];

const mockUser = {
  username: "qa-user",
  auth: AUTH_TOKEN,
  memberships: [
    {
      organization_id: "qa-org",
      organization_name: "QA Organization",
      role: "admin",
      invite_still_open: false,
      sender: "owner@querylake.local",
    },
  ],
  is_admin: true,
  available_models: {
    llm: {
      default_model: {
        title: "Mock LLM",
        id: "mock-llm",
        model_description: "Authenticated screenshot fixture model.",
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
  user_set_providers: ["openai"],
  providers: ["openai", "anthropic", "google"],
};

const mockToolchain = {
  id: "smoke-toolchain",
  name: "Smoke Toolchain",
  title: "Smoke Toolchain",
  category: "Smoke",
  first_event_follow_up: "chat",
  nodes: [
    { id: "ingest", api_function: "upload_document" },
    { id: "retrieve", api_function: "search_bm25" },
    { id: "answer", api_function: "llm_structured_output" },
    { id: "rate", api_function: "feedback" },
    { id: "archive", api_function: "persist_results" },
    { id: "notify", api_function: "send_update" },
  ],
  edges: [
    { from: "ingest", to: "retrieve" },
    { from: "retrieve", to: "answer" },
  ],
};

const mockCollections = {
  collections: {
    user_collections: [
      { name: "Smoke Personal Collection", hash_id: "personal-smoke", document_count: 3, type: "document" },
      { name: "Launch Notes", hash_id: "launch-notes", document_count: 8, type: "document" },
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
};

const mockApiKeys = {
  api_keys: [
    {
      id: "key_1",
      title: "Studio QA Key",
      key_preview: "qlk_****************A1",
      created: 1713800000,
      created_string: "2024-04-22",
      last_used: 1713886400,
      last_used_string: "2024-04-23",
    },
  ],
};

const mockOrgMembers = {
  memberships: [
    {
      user_name: "qa-user",
      username: "qa-user",
      email: "qa-user@querylake.local",
      role: "admin",
      organization_id: "qa-org",
      organization_name: "QA Organization",
      invite_still_open: false,
    },
    {
      user_name: "ops-user",
      username: "ops-user",
      email: "ops@querylake.local",
      role: "member",
      organization_id: "qa-org",
      organization_name: "QA Organization",
      invite_still_open: false,
    },
  ],
};

const mockUsage = [
  {
    start_timestamp: Math.floor(Date.now() / 1000),
    organization_id: null,
    id: "usage-smoke-1",
    user_id: "qa-user",
    value: { requests: 14, tokens: 12004 },
    window: "day",
    api_key_id: null,
  },
  {
    start_timestamp: Math.floor(Date.now() / 1000) - 86400,
    organization_id: null,
    id: "usage-smoke-2",
    user_id: "qa-user",
    value: { requests: 9, tokens: 8240 },
    window: "day",
    api_key_id: null,
  },
];

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

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,PUT,DELETE,OPTIONS",
    "access-control-allow-headers": "content-type,authorization",
  };
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
        payload = ok(mockCollections);
        break;
      case "/api/fetch_toolchain_sessions":
        payload = ok([
          { title: "Smoke Run", toolchain: "smoke-toolchain", id: "smoke-run", time: Math.floor(Date.now() / 1000) },
          { title: "Replay Run", toolchain: "smoke-toolchain", id: "replay-run", time: Math.floor(Date.now() / 1000) - 7200 },
        ]);
        break;
      case "/api/fetch_toolchain_config":
        payload = ok(mockToolchain);
        break;
      case "/api/get_usage_tally":
        payload = ok(mockUsage);
        break;
      case "/api/function_help":
        payload = ok([]);
        break;
      case "/api/fetch_api_keys":
        payload = ok(mockApiKeys);
        break;
      case "/api/fetch_memberships":
        payload = ok({ memberships: mockUser.memberships, admin: true });
        break;
      case "/api/fetch_memberships_of_organization":
        payload = ok(mockOrgMembers);
        break;
      case "/api/modify_user_external_providers":
      case "/api/create_api_key":
      case "/api/delete_api_key":
      case "/api/create_organization":
      case "/api/invite_user_to_organization":
      case "/api/change_organization_member_role":
      case "/api/resolve_organization_invitation":
      case "/api/update_toolchain_config":
        payload = ok({});
        break;
      case "/v2/kernel/sessions":
        payload = ok({ session_id: "smoke-session-v2" });
        break;
      default:
        payload = ok({});
        break;
    }

    res.writeHead(200, { ...corsHeaders(), "content-type": "application/json" });
    res.end(JSON.stringify(payload));
  });
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

function appEnv(mockApiPort) {
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
    cwd: options.cwd ?? process.cwd(),
  });
  return new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(" ")} failed with ${signal ?? code}`));
    });
  });
}

function startNext(mockApiPort, appPort) {
  return spawn("npx", ["next", "start", "-p", appPort], {
    stdio: ["ignore", "pipe", "pipe"],
    env: appEnv(mockApiPort),
    cwd: process.cwd(),
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
      // retry
    }
    await delay(500);
  }
  throw new Error(`Timed out waiting for ${baseUrl}`);
}

async function waitForCdp(cdpPort) {
  for (let i = 0; i < 80; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
      if (res.ok) return;
    } catch {
      // retry
    }
    await delay(250);
  }
  throw new Error(`Timed out waiting for CDP on ${cdpPort}`);
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
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method, handler) {
    const handlers = this.handlers.get(method) ?? [];
    handlers.push(handler);
    this.handlers.set(method, handlers);
  }
}

async function openPageTarget(cdpPort, url) {
  const res = await fetch(`http://127.0.0.1:${cdpPort}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) throw new Error(`Unable to create Chromium target on ${cdpPort}`);
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

async function waitForExpression(cdp, expression, label, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const result = await cdp.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.result?.value) return true;
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function navigate(cdp, url) {
  await cdp.send("Page.navigate", { url });
  await waitForExpression(cdp, "document.readyState === 'complete'", `document ready at ${url}`);
}

async function setViewport(cdp, viewport) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.deviceScaleFactor,
    mobile: viewport.slug === "mobile",
    screenWidth: viewport.width,
    screenHeight: viewport.height,
  });
}

async function captureFullPage(cdp, outputPath) {
  const metrics = await cdp.send("Page.getLayoutMetrics");
  const width = Math.ceil(metrics.cssContentSize?.width ?? metrics.contentSize?.width ?? 0);
  const height = Math.ceil(metrics.cssContentSize?.height ?? metrics.contentSize?.height ?? 0);
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: true,
    clip: {
      x: 0,
      y: 0,
      width,
      height,
      scale: 1,
    },
  });
  await writeFile(outputPath, Buffer.from(screenshot.data, "base64"));
}

async function main() {
  await mkdir(OUTPUT_ROOT, { recursive: true });

  const mockApiPort = process.env.QUERYLAKE_MOCK_API_PORT ?? await getFreePort();
  const appPort = process.env.PORT ?? await getFreePort();
  const cdpPort = process.env.QUERYLAKE_CAPTURE_CDP_PORT ?? await getFreePort();
  const baseUrl = `http://127.0.0.1:${appPort}`;
  const profileDir = await mkdtemp(path.join(os.tmpdir(), "ql-redesign-capture-"));
  const mockApi = createMockApiServer(mockApiPort);

  let next;
  let chromium;
  let cdp;
  const consoleMessages = [];
  const captures = [];
  const warnings = [];

  const stopProcess = (child) => {
    if (!child || child.killed) return;
    child.kill("SIGTERM");
    setTimeout(() => {
      if (!child.killed) child.kill("SIGKILL");
    }, 1500).unref();
  };

  const closeServer = (server) => new Promise((resolve) => {
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

  try {
    await listen(mockApi, mockApiPort);
    console.log(`Mock API: 127.0.0.1:${mockApiPort}`);

    console.log("Building production app for contact-sheet capture...");
    await runCommand("npx", ["next", "build"], { env: appEnv(mockApiPort), cwd: process.cwd() });

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

    const target = await openPageTarget(cdpPort, "about:blank");
    cdp = await connectCdp(target.webSocketDebuggerUrl);
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Network.enable");

    cdp.on("Runtime.consoleAPICalled", (event) => {
      const text = event.args?.map((arg) => arg.value ?? arg.description ?? "").join(" ") ?? "";
      consoleMessages.push(`${event.type}: ${text}`);
    });
    cdp.on("Runtime.exceptionThrown", (event) => {
      consoleMessages.push(`exception: ${event.exceptionDetails?.text ?? "unknown"}`);
    });

    await navigate(cdp, baseUrl);
    await cdp.send("Network.setCookie", {
      name: "UD",
      value: AUTH_TOKEN,
      url: baseUrl,
      path: "/",
    });
    await cdp.send("Runtime.evaluate", {
      expression: `window.localStorage.setItem('ql_last_workspace', 'personal')`,
      awaitPromise: true,
    });

    for (const viewport of VIEWPORTS) {
      const viewportDir = path.join(OUTPUT_ROOT, viewport.slug);
      await mkdir(viewportDir, { recursive: true });
      await setViewport(cdp, viewport);

      for (const route of ROUTES) {
        const outputPath = path.join(viewportDir, `${route.slug}.png`);
        console.log(`Capturing ${viewport.slug} :: ${route.path}`);
        await navigate(cdp, `${baseUrl}${route.path}`);
        if (route.auth) {
          await cdp.send("Runtime.evaluate", {
            expression: `window.localStorage.setItem('ql_last_workspace', 'personal')`,
            awaitPromise: true,
          });
        }
        try {
          await waitForExpression(cdp, route.waitFor, `${route.slug} ${viewport.slug}`);
        } catch (error) {
          warnings.push({
            viewport: viewport.slug,
            route: route.slug,
            warning: String(error),
          });
          await delay(2000);
        }
        await delay(800);
        await captureFullPage(cdp, outputPath);
        captures.push({ viewport: viewport.slug, route: route.slug, label: route.label, path: outputPath });
      }
    }

    const jotaiWarnings = consoleMessages.filter((message) => message.includes("Detected multiple Jotai instances"));
    if (jotaiWarnings.length > 0) {
      throw new Error(`Jotai warning detected during capture: ${jotaiWarnings.join(" | ")}`);
    }

    await writeFile(
      path.join(OUTPUT_ROOT, "capture-manifest.json"),
      JSON.stringify({
        generated_at: new Date().toISOString(),
        source: "current QueryLake studio frontend",
        output_root: OUTPUT_ROOT,
        captures,
        warnings,
        viewports: VIEWPORTS.map(({ slug, label, width, height, deviceScaleFactor }) => ({ slug, label, width, height, deviceScaleFactor })),
      }, null, 2)
    );
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
