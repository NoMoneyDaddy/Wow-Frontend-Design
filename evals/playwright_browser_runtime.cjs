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
        await context.addInitScript(() => {
          const pageGlobal = globalThis;
          const pageDocument = document;
          const apply = Reflect.apply;
          const construct = Reflect.construct;
          const descriptor = Object.getOwnPropertyDescriptor;
          const isPrototypeOf = Object.prototype.isPrototypeOf;
          const freeze = Object.freeze;
          const define = Object.defineProperty;
          const numberFunction = Number;
          const promiseConstructor = Promise;
          const regexExec = RegExp.prototype.exec;
          const animationFrame = pageGlobal.requestAnimationFrame;
          const performanceNow = Performance.prototype.now;
          const stringCharacter = String.prototype.charAt;
          const stringIndexOf = String.prototype.indexOf;
          const stringLower = String.prototype.toLocaleLowerCase;
          const stringSlice = String.prototype.slice;
          const stringStartsWith = String.prototype.startsWith;
          const stringTrim = String.prototype.trim;
          const styleFunction = pageGlobal.getComputedStyle;
          const styleValue = CSSStyleDeclaration.prototype.getPropertyValue;
          const elementRect = Element.prototype.getBoundingClientRect;
          const elementAnimations = Element.prototype.getAnimations;
          const elementAttribute = Element.prototype.getAttribute;
          const htmlPrototype = HTMLElement.prototype;
          const htmlInnerText = descriptor(htmlPrototype, "innerText").get;
          const nodeText = descriptor(Node.prototype, "textContent").get;
          const nodeParent = descriptor(Node.prototype, "parentElement").get;
          const nodeRoot = Node.prototype.getRootNode;
          const shadowPrototype = ShadowRoot.prototype;
          const shadowHost = descriptor(ShadowRoot.prototype, "host").get;
          const scrollWidth = descriptor(Element.prototype, "scrollWidth").get;
          const scrollHeight = descriptor(Element.prototype, "scrollHeight").get;
          const clientWidth = descriptor(Element.prototype, "clientWidth").get;
          const clientHeight = descriptor(Element.prototype, "clientHeight").get;
          const createRange = Document.prototype.createRange;
          const createTreeWalker = Document.prototype.createTreeWalker;
          const treeNext = TreeWalker.prototype.nextNode;
          const rangeSelect = Range.prototype.selectNodeContents;
          const rangeStart = Range.prototype.setStart;
          const rangeEnd = Range.prototype.setEnd;
          const rangeRects = Range.prototype.getClientRects;
          const rangeRect = Range.prototype.getBoundingClientRect;
          const rectListLength = descriptor(DOMRectList.prototype, "length").get;
          const rectListItem = DOMRectList.prototype.item;
          const rectPrototype = DOMRectReadOnly.prototype;
          const rectGetters = Object.fromEntries(
            ["bottom", "height", "left", "right", "top", "width"].map((name) =>
              [name, descriptor(rectPrototype, name).get]),
          );
          const animationState = descriptor(Animation.prototype, "playState").get;
          const fontFaceFamily = descriptor(FontFace.prototype, "family").get;
          const fontFaceStatus = descriptor(FontFace.prototype, "status").get;
          const fontSet = pageDocument.fonts;
          const fontIterator = Object.getPrototypeOf(fontSet)[Symbol.iterator];
          const fontIteratorSample = apply(fontIterator, fontSet, []);
          const fontIteratorNext = Object.getPrototypeOf(fontIteratorSample).next;
          const segmentConstructor = Intl.Segmenter;
          const segmentMethod = Intl.Segmenter.prototype.segment;
          const segmentSample = apply(segmentMethod, construct(segmentConstructor, [undefined, { granularity: "grapheme" }]), [""]);
          const segmentIterator = Object.getPrototypeOf(segmentSample)[Symbol.iterator];
          const segmentIteratorSample = apply(segmentIterator, segmentSample, []);
          const segmentIteratorNext = Object.getPrototypeOf(segmentIteratorSample).next;
          const hanGrapheme = /^\p{Script=Han}\p{M}*$/u;
          const punctuationGrapheme = /^\p{P}+$/u;

          const normalizeFamily = (value) => {
            let normalized = apply(stringTrim, value, []);
            const first = apply(stringCharacter, normalized, [0]);
            const last = apply(stringCharacter, normalized, [normalized.length - 1]);
            if ((first === "\"" && last === "\"") || (first === "'" && last === "'")) {
              normalized = apply(stringSlice, normalized, [1, -1]);
            }
            return apply(stringLower, normalized, []);
          };
          const appliedFontFamilies = (value) => {
            const families = [];
            let token = "";
            let quote = "";
            let escaped = false;
            for (let index = 0; index < value.length; index += 1) {
              const character = apply(stringCharacter, value, [index]);
              if (escaped) {
                token += character;
                escaped = false;
              } else if (character === "\\") {
                token += character;
                escaped = true;
              } else if (quote) {
                token += character;
                if (character === quote) quote = "";
              } else if (character === "\"" || character === "'") {
                token += character;
                quote = character;
              } else if (character === ",") {
                families[families.length] = normalizeFamily(token);
                token = "";
              } else {
                token += character;
              }
            }
            if (apply(stringTrim, token, []).length > 0) families[families.length] = normalizeFamily(token);
            return families;
          };

          const rectNames = ["bottom", "height", "left", "right", "top", "width"];
          const snapshotRect = (rect) => {
            const result = {};
            for (let index = 0; index < rectNames.length; index += 1) {
              const name = rectNames[index];
              result[name] = apply(rectGetters[name], rect, []);
            }
            return freeze(result);
          };
          const makeRange = () => apply(createRange, pageDocument, []);
          const parentOf = (node) => {
            const parent = apply(nodeParent, node, []);
            if (parent) return parent;
            const root = apply(nodeRoot, node, []);
            return apply(isPrototypeOf, shadowPrototype, [root])
              ? apply(shadowHost, root, [])
              : null;
          };
          const visible = (element) => {
            for (let current = element; current; current = parentOf(current)) {
              const computed = apply(styleFunction, pageGlobal, [current]);
              const display = apply(styleValue, computed, ["display"]);
              const visibility = apply(styleValue, computed, ["visibility"]);
              if (display === "none" || visibility === "hidden" || visibility === "collapse"
                || apply(numberFunction, undefined, [apply(styleValue, computed, ["opacity"])]) === 0) return false;
            }
            return true;
          };
          const visibleRect = (rect, owner) => {
            let left = rect.left;
            let right = rect.right;
            let top = rect.top;
            let bottom = rect.bottom;
            for (let current = owner; current; current = parentOf(current)) {
              const computed = apply(styleFunction, pageGlobal, [current]);
              const overflowX = apply(styleValue, computed, ["overflow-x"]);
              const overflowY = apply(styleValue, computed, ["overflow-y"]);
              const box = snapshotRect(apply(elementRect, current, []));
              if (overflowX === "auto" || overflowX === "clip" || overflowX === "hidden" || overflowX === "scroll") {
                left = left > box.left ? left : box.left;
                right = right < box.right ? right : box.right;
              }
              if (overflowY === "auto" || overflowY === "clip" || overflowY === "hidden" || overflowY === "scroll") {
                top = top > box.top ? top : box.top;
                bottom = bottom < box.bottom ? bottom : box.bottom;
              }
              if (right <= left || bottom <= top) return false;
            }
            return true;
          };
          const segmentText = (text, locale) => {
            let segmenter;
            try {
              segmenter = construct(segmentConstructor, [locale || undefined, { granularity: "grapheme" }]);
            } catch {
              segmenter = construct(segmentConstructor, [undefined, { granularity: "grapheme" }]);
            }
            const segmented = apply(segmentMethod, segmenter, [text]);
            const iterator = apply(segmentIterator, segmented, []);
            const result = [];
            while (true) {
              const item = apply(segmentIteratorNext, iterator, []);
              if (item.done) break;
              result[result.length] = freeze({ index: item.value.index, value: item.value.segment });
            }
            return freeze(result);
          };
          const mergeRenderedLines = (records) => {
            for (let index = 1; index < records.length; index += 1) {
              const record = records[index];
              let cursor = index - 1;
              while (cursor >= 0 && (records[cursor].rect.top > record.rect.top
                || (records[cursor].rect.top === record.rect.top && records[cursor].rect.left > record.rect.left))) {
                records[cursor + 1] = records[cursor];
                cursor -= 1;
              }
              records[cursor + 1] = record;
            }
            const lines = [];
            for (let recordIndex = 0; recordIndex < records.length; recordIndex += 1) {
              const record = records[recordIndex];
              let matching = null;
              for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
                const line = lines[lineIndex];
                const overlapBottom = line.bottom < record.rect.bottom ? line.bottom : record.rect.bottom;
                const overlapTop = line.top > record.rect.top ? line.top : record.rect.top;
                const smallestHeight = line.bottom - line.top < record.rect.height
                  ? line.bottom - line.top : record.rect.height;
                if (overlapBottom - overlapTop > smallestHeight * 0.4) {
                  matching = line;
                  break;
                }
              }
              if (matching) {
                matching.top = matching.top < record.rect.top ? matching.top : record.rect.top;
                matching.bottom = matching.bottom > record.rect.bottom ? matching.bottom : record.rect.bottom;
                matching.records[matching.records.length] = record;
              } else {
                lines[lines.length] = { top: record.rect.top, bottom: record.rect.bottom, records: [record] };
              }
            }
            for (let index = 1; index < lines.length; index += 1) {
              const line = lines[index];
              let cursor = index - 1;
              while (cursor >= 0 && lines[cursor].top > line.top) {
                lines[cursor + 1] = lines[cursor];
                cursor -= 1;
              }
              lines[cursor + 1] = line;
            }
            return lines;
          };
          const renderedLineProfile = (element) => {
            const computed = apply(styleFunction, pageGlobal, [element]);
            const writingMode = apply(styleValue, computed, ["writing-mode"]);
            const elementBox = snapshotRect(apply(elementRect, element, []));
            if (!visible(element) || !(elementBox.width > 0 && elementBox.height > 0)
              || !apply(stringStartsWith, writingMode, ["horizontal"])) return null;
            const nodes = [];
            const walker = apply(createTreeWalker, pageDocument, [element, 4]);
            let combined = "";
            while (true) {
              const node = apply(treeNext, walker, []);
              if (!node) break;
              const value = apply(nodeText, node, []) || "";
              const owner = parentOf(node);
              if (apply(stringTrim, value, []).length === 0 || !visible(owner)) continue;
              nodes[nodes.length] = { node, owner, start: combined.length, end: combined.length + value.length };
              combined += value;
            }
            const segments = segmentText(combined, apply(elementAttribute, pageDocument.documentElement, ["lang"]));
            const records = [];
            for (let segmentIndex = 0; segmentIndex < segments.length; segmentIndex += 1) {
              const segment = segments[segmentIndex];
              if (apply(stringTrim, segment.value, []).length === 0) continue;
              const segmentEnd = segment.index + segment.value.length;
              let startChunk = null;
              let endChunk = null;
              for (let chunkIndex = 0; chunkIndex < nodes.length; chunkIndex += 1) {
                const chunk = nodes[chunkIndex];
                if (segment.index >= chunk.start && segment.index < chunk.end) startChunk = chunk;
                if (segmentEnd > chunk.start && segmentEnd <= chunk.end) endChunk = chunk;
              }
              if (!startChunk || !endChunk) continue;
              const range = makeRange();
              apply(rangeStart, range, [startChunk.node, segment.index - startChunk.start]);
              apply(rangeEnd, range, [endChunk.node, segmentEnd - endChunk.start]);
              const rect = snapshotRect(apply(rangeRect, range, []));
              if (!(rect.width > 0 && rect.height > 0) || !visibleRect(rect, startChunk.owner)) continue;
              records[records.length] = {
                rect,
                start: segment.index,
                end: segmentEnd,
                han: apply(regexExec, hanGrapheme, [segment.value]) !== null,
                punctuation: apply(regexExec, punctuationGrapheme, [segment.value]) !== null,
              };
            }
            const lines = mergeRenderedLines(records);
            const publicSegments = [];
            let lastLineGraphemes = 0;
            let lastLineHanGraphemes = 0;
            let lastLinePunctuationGraphemes = 0;
            for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
              const line = lines[lineIndex];
              for (let recordIndex = 0; recordIndex < line.records.length; recordIndex += 1) {
                const record = line.records[recordIndex];
                publicSegments[publicSegments.length] = freeze({
                  start: record.start,
                  end: record.end,
                  line: lineIndex,
                });
                if (lineIndex === lines.length - 1) {
                  lastLineGraphemes += 1;
                  if (record.han) lastLineHanGraphemes += 1;
                  if (record.punctuation) lastLinePunctuationGraphemes += 1;
                }
              }
            }
            return freeze({
              lineCount: lines.length,
              lastLineGraphemes,
              lastLineHanGraphemes,
              lastLinePunctuationGraphemes,
              segments: freeze(publicSegments),
            });
          };
          const evaluatorRead = freeze({
            activeAnimationCount(element) {
              const animations = apply(elementAnimations, element, [{ subtree: true }]);
              let count = 0;
              for (let index = 0; index < animations.length; index += 1) {
                const state = apply(animationState, animations[index], []);
                if (state === "pending" || state === "running") count += 1;
              }
              return count;
            },
            animationsInactiveFor(element, duration) {
              const activeCount = () => {
                const animations = apply(elementAnimations, element, [{ subtree: true }]);
                let count = 0;
                for (let index = 0; index < animations.length; index += 1) {
                  const state = apply(animationState, animations[index], []);
                  if (state === "pending" || state === "running") count += 1;
                }
                return count;
              };
              const started = apply(performanceNow, pageGlobal.performance, []);
              return new promiseConstructor((resolve) => {
                const observe = () => {
                  if (activeCount() !== 0) {
                    resolve(false);
                    return;
                  }
                  if (apply(performanceNow, pageGlobal.performance, []) - started >= duration) {
                    resolve(true);
                    return;
                  }
                  apply(animationFrame, pageGlobal, [observe]);
                };
                observe();
              });
            },
            attribute(element, name) {
              return apply(elementAttribute, element, [name]);
            },
            fontFaceLoaded(element, family) {
              const expected = normalizeFamily(family);
              const computed = apply(styleFunction, pageGlobal, [element]);
              const applied = appliedFontFamilies(apply(styleValue, computed, ["font-family"]));
              let familyApplied = false;
              for (let index = 0; index < applied.length; index += 1) {
                if (applied[index] === expected) familyApplied = true;
              }
              if (!familyApplied) return false;
              const iterator = apply(fontIterator, fontSet, []);
              while (true) {
                const item = apply(fontIteratorNext, iterator, []);
                if (item.done) return false;
                if (normalizeFamily(apply(fontFaceFamily, item.value, [])) === expected
                  && apply(fontFaceStatus, item.value, []) === "loaded") return true;
              }
            },
            hasVisibleText(value) {
              return apply(stringTrim, value, []).length > 0;
            },
            horizontalWritingMode(value) {
              return apply(stringStartsWith, value, ["horizontal"]);
            },
            locale() {
              return apply(elementAttribute, pageDocument.documentElement, ["lang"]);
            },
            parent(node) {
              return parentOf(node);
            },
            rangeRect(startNode, startOffset, endNode, endOffset) {
              const range = makeRange();
              apply(rangeStart, range, [startNode, startOffset]);
              apply(rangeEnd, range, [endNode, endOffset]);
              return snapshotRect(apply(rangeRect, range, []));
            },
            rangeRects(node) {
              const range = makeRange();
              apply(rangeSelect, range, [node]);
              const list = apply(rangeRects, range, []);
              const length = apply(rectListLength, list, []);
              const result = [];
              for (let index = 0; index < length; index += 1) {
                result[result.length] = snapshotRect(apply(rectListItem, list, [index]));
              }
              return freeze(result);
            },
            rect(element) {
              return snapshotRect(apply(elementRect, element, []));
            },
            renderedTextIncludes(element, literal) {
              if (!apply(isPrototypeOf, htmlPrototype, [element])) return false;
              return apply(stringIndexOf, apply(htmlInnerText, element, []), [literal]) >= 0;
            },
            renderedLineProfile(element) {
              return renderedLineProfile(element);
            },
            scrollMetrics(element) {
              return freeze({
                clientHeight: apply(clientHeight, element, []),
                clientWidth: apply(clientWidth, element, []),
                scrollHeight: apply(scrollHeight, element, []),
                scrollWidth: apply(scrollWidth, element, []),
              });
            },
            segments(text, locale) {
              return segmentText(text, locale);
            },
            style(element, property) {
              const computed = apply(styleFunction, pageGlobal, [element]);
              return apply(styleValue, computed, [property]);
            },
            zeroNumber(value) {
              return apply(numberFunction, undefined, [value]) === 0;
            },
            text(node) {
              return apply(nodeText, node, []);
            },
            textNodes(element) {
              const walker = apply(createTreeWalker, pageDocument, [element, 4]);
              const result = [];
              while (true) {
                const node = apply(treeNext, walker, []);
                if (!node) break;
                result[result.length] = node;
              }
              return freeze(result);
            },
            uniqueLiteralRange(text, literal) {
              const start = apply(stringIndexOf, text, [literal]);
              if (start < 0 || apply(stringIndexOf, text, [literal, start + 1]) >= 0) return null;
              return freeze({ start, end: start + literal.length });
            },
          });
          define(pageGlobal, "__wowEvaluatorRead", {
            configurable: false,
            enumerable: false,
            value: evaluatorRead,
            writable: false,
          });
        });
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
