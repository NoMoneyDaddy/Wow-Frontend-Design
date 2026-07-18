"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const MIME = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".svg", "image/svg+xml"],
]);

function inside(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function startServer(stage, allowedFiles) {
  const allowed = new Set(allowedFiles.map((name) => path.resolve(stage, name)));
  const server = http.createServer((request, response) => {
    let pathname;
    try {
      pathname = decodeURIComponent(new URL(request.url, "http://127.0.0.1").pathname);
    } catch {
      response.writeHead(400).end();
      return;
    }
    const candidate = path.resolve(stage, `.${pathname}`);
    if (request.method !== "GET" || !inside(stage, candidate) || !allowed.has(candidate)) {
      response.writeHead(404, { "cache-control": "no-store" }).end();
      return;
    }
    let info;
    try {
      info = fs.lstatSync(candidate);
    } catch {
      response.writeHead(404, { "cache-control": "no-store" }).end();
      return;
    }
    if (!info.isFile() || info.isSymbolicLink()) {
      response.writeHead(404, { "cache-control": "no-store" }).end();
      return;
    }
    response.writeHead(200, {
      "cache-control": "no-store",
      "content-length": info.size,
      "content-type": MIME.get(path.extname(candidate).toLowerCase()) || "application/octet-stream",
      "x-content-type-options": "nosniff",
    });
    fs.createReadStream(candidate).pipe(response);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, origin: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function closeServer(server) {
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

async function runLocalPageMatrix({ stage, pages, allowedFiles, profiles, inspectPage }) {
  const canonicalStage = fs.realpathSync(stage);
  const { server, origin } = await startServer(canonicalStage, allowedFiles);
  let browser;
  let browserVersion;
  const results = [];
  try {
    browser = await chromium.launch({
      headless: true,
      args: ["--force-webrtc-ip-handling-policy=disable_non_proxied_udp"],
    });
    browserVersion = browser.version();
    for (const relativePage of pages) {
      for (const profile of profiles) {
        const contextOptions = {
          viewport: profile.viewport,
          reducedMotion: profile.reducedMotion,
          serviceWorkers: "block",
        };
        if (profile.locale) contextOptions.locale = profile.locale;
        if (profile.dpr) contextOptions.deviceScaleFactor = profile.dpr;
        const context = await browser.newContext(contextOptions);
        const counters = {
          page_errors: 0,
          console_errors: 0,
          blocked_external_requests: 0,
          blocked_websockets: 0,
          failed_requests: 0,
          bad_responses: 0,
          dialogs: 0,
          unexpected_pages: 0,
        };
        await context.route("**/*", async (route) => {
          const url = route.request().url();
          let sameOrigin = false;
          try {
            sameOrigin = new URL(url).origin === origin;
          } catch {
            sameOrigin = false;
          }
          if (sameOrigin || url.startsWith("data:") || url.startsWith("blob:") || url === "about:blank") {
            await route.continue();
          } else {
            counters.blocked_external_requests += 1;
            await route.abort("blockedbyclient");
          }
        });
        await context.routeWebSocket("**/*", async (socket) => {
          counters.blocked_websockets += 1;
          await socket.close({ code: 1008, reason: "network smoke" });
        });
        const page = await context.newPage();
        await new Promise((resolve) => setImmediate(resolve));
        page.on("popup", () => { counters.unexpected_pages += 1; });
        page.on("pageerror", () => { counters.page_errors += 1; });
        page.on("console", (message) => {
          if (message.type() === "error") counters.console_errors += 1;
        });
        page.on("requestfailed", () => { counters.failed_requests += 1; });
        page.on("response", (response) => {
          if (response.status() >= 400) counters.bad_responses += 1;
        });
        page.on("dialog", async (dialog) => {
          counters.dialogs += 1;
          await dialog.dismiss().catch(() => {});
        });

        let navigation = "passed";
        try {
          const encodedPath = relativePage.split("/").map(encodeURIComponent).join("/");
          await page.goto(`${origin}/${encodedPath}`, { waitUntil: "load", timeout: 15_000 });
          await page.evaluate(async () => {
            if (document.fonts) await document.fonts.ready;
            await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          });
          await page.waitForTimeout(300);
          await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        } catch {
          navigation = "failed";
        }
        const visibleMain = navigation === "passed" && await page.locator("main").isVisible().catch(() => false);
        const metrics = navigation === "passed" ? await page.evaluate(() => ({
          visible_text: getComputedStyle(document.body).display !== "none"
            && getComputedStyle(document.body).visibility !== "hidden"
            && (document.body.innerText || "").trim().length > 0,
          visible_primary_content: (() => {
            const main = document.querySelector("main");
            if (!main) return false;
            const visible = (element) => {
              const style = getComputedStyle(element);
              const box = element.getBoundingClientRect();
              return style.display !== "none" && style.visibility !== "hidden" && box.width > 0 && box.height > 0;
            };
            if (!visible(main)) return false;
            if ((main.innerText || "").trim().length > 0) return true;
            return Array.from(main.querySelectorAll("img,svg,canvas,video,audio,input,select,textarea,button"))
              .some(visible);
          })(),
          root_horizontal_overflow: (() => {
            // CSSOM View defines scrollingElement as the element that scrolls the document.
            const rootScroller = document.scrollingElement || document.documentElement;
            return rootScroller.scrollWidth > rootScroller.clientWidth + 1;
          })(),
        })).catch(() => ({ visible_text: false, visible_primary_content: false, root_horizontal_overflow: false })) : {
          visible_text: false,
          visible_primary_content: false,
          root_horizontal_overflow: false,
        };
        const inspection = navigation === "passed" && inspectPage
          ? await inspectPage(page, { relativePage, profile })
          : {};
        results.push({
          page: relativePage,
          profile: profile.name,
          navigation,
          visible_main: visibleMain,
          ...metrics,
          counters,
          inspection,
        });
        await context.close();
      }
    }
  } finally {
    try {
      if (browser) await browser.close();
    } finally {
      await closeServer(server);
    }
  }
  return { browserVersion, results };
}

module.exports = { runLocalPageMatrix };
