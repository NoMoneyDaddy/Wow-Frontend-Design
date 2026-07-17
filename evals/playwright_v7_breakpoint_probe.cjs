#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const CONTRACT_PATH = path.join(__dirname, "v7-breakpoint-probe-contract.json");
const MAX_JSON_BYTES = 1024 * 1024;
const OUTPUT_KEYS = new Set([
  "schema_version", "status", "authority", "claim_boundary", "identity", "subject",
  "probe", "contract", "coverage", "transitions", "findings", "advisories",
]);
const REASON_CODES = new Set([
  "depth_budget_exhausted", "fonts_unavailable", "interaction_unavailable",
  "layout_signature_unstable", "probe_execution_unavailable", "probe_provenance_drift",
  "runtime_or_external_event", "sample_budget_exhausted", "transition_budget_exhausted",
]);

function fail(message) {
  throw new Error(message);
}

function sha256Bytes(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join("|") === [...keys].sort().join("|");
}

function isSha256(value) {
  return typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
}

function modeHash(value) {
  return sha256Bytes(canonical(value));
}

function reasonCode(error) {
  const message = error instanceof Error ? error.message : "";
  if (REASON_CODES.has(message)) return message;
  if (message.startsWith("interaction step ")) return "interaction_unavailable";
  return "probe_execution_unavailable";
}

function securePath(file, label) {
  const absolute = path.resolve(file);
  const parsed = path.parse(absolute);
  let current = parsed.root;
  for (const [index, part] of absolute.slice(parsed.root.length).split(path.sep).filter(Boolean).entries()) {
    current = path.join(current, part);
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) {
      const allowedDarwinVar = process.platform === "darwin" && index === 0 && part === "var"
        && fs.realpathSync(current) === "/private/var";
      if (!allowedDarwinVar) fail(`${label} path must not traverse a symlink`);
      current = "/private/var";
    }
  }
  return absolute;
}

function stableFile(file, label, maximum = MAX_JSON_BYTES) {
  const absolute = securePath(file, label);
  const noFollow = fs.constants.O_NOFOLLOW || 0;
  const descriptor = fs.openSync(absolute, fs.constants.O_RDONLY | noFollow);
  try {
    const before = fs.fstatSync(descriptor);
    if (!before.isFile() || before.size < 1 || before.size > maximum) {
      fail(`${label} must be a bounded regular file`);
    }
    const bytes = fs.readFileSync(descriptor);
    const after = fs.fstatSync(descriptor);
    if (before.dev !== after.dev || before.ino !== after.ino || before.size !== after.size
        || before.mtimeMs !== after.mtimeMs || bytes.length !== before.size) {
      fail(`${label} changed while it was read`);
    }
    return { absolute, bytes, bytesLength: bytes.length, sha256: sha256Bytes(bytes) };
  } finally {
    fs.closeSync(descriptor);
  }
}

function freshOutput(file) {
  const absolute = path.resolve(file);
  if (fs.existsSync(absolute)) fail("output already exists");
  const parentPath = securePath(path.dirname(absolute), "output parent");
  const parent = fs.lstatSync(parentPath);
  if (!parent.isDirectory() || parent.isSymbolicLink()) fail("output parent is unsafe");
  return absolute;
}

function loadJson(file, label, maximum = MAX_JSON_BYTES) {
  const record = stableFile(file, label, maximum);
  let value;
  try {
    value = JSON.parse(record.bytes.toString("utf8"));
  } catch (error) {
    fail(`${label} is not valid JSON: ${error.message}`);
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) fail(`${label} root must be an object`);
  return { ...record, value };
}

function loadContract(file = CONTRACT_PATH) {
  const { absolute, bytes, sha256, value } = loadJson(file, "breakpoint contract", 64 * 1024);
  const expected = {
    schema_version: 1,
    probe_id: "v7-breakpoint-transition-v1",
    authority: "supporting-discovery-only",
    claim_boundary: "Bounded Chromium width-transition observation only; no screenshot, cross-engine, touch, height, zoom, motion, physical-device, visual-quality or release claim.",
    dependencies: {
      playwright_entrypoint: {
        path: "node_modules/playwright/index.js",
        sha256: "4e98f65f0a9d9bcab8cffc0c5cfdd87fd3f5b0be74fc494ff166a466b204cd44",
      },
      playwright_manifest: {
        path: "node_modules/playwright/package.json",
        sha256: "6b840268612656f0639fb7d68782e8353bdf11518589d30ddf66f283c2670ed5",
        version: "1.61.1",
      },
    },
    widths: [320, 360, 390, 480, 600, 768, 900, 1024, 1152, 1280, 1440],
    height: 844,
    device_scale_factor: 1,
    max_samples: 48,
    max_depth: 11,
    max_transitions: 8,
    max_hidden_selectors: 40,
    max_nodes_per_selector: 4,
    max_children_per_node: 32,
    settle_timeout_ms: 10000,
    screenshots: false,
    traces: false,
    videos: false,
  };
  if (canonical(value) !== canonical(expected)) fail("breakpoint contract changed");
  const repositoryRoot = path.resolve(__dirname, "..");
  const dependencies = {};
  for (const [name, binding] of Object.entries(value.dependencies)) {
    const dependency = stableFile(path.join(repositoryRoot, binding.path), `breakpoint dependency ${name}`, 64 * 1024);
    if (dependency.sha256 !== binding.sha256) fail(`breakpoint dependency ${name} drifted`);
    dependencies[name] = dependency;
  }
  const manifest = JSON.parse(dependencies.playwright_manifest.bytes.toString("utf8"));
  if (manifest.version !== value.dependencies.playwright_manifest.version) fail("Playwright version drifted");
  return { absolute, bytes, value, sha256, dependencies };
}

function parseArguments(argv) {
  const allowed = new Set(["variant", "case-id", "state", "route", "target-manifest", "spec", "output"]);
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const raw = argv[index];
    if (!raw?.startsWith("--") || index + 1 >= argv.length) fail("arguments must be --key value pairs");
    const key = raw.slice(2);
    if (!allowed.has(key) || Object.hasOwn(result, key)) fail(`unknown or duplicate argument: ${raw}`);
    result[key] = argv[index + 1];
  }
  for (const key of allowed) if (!result[key]) fail(`missing --${key}`);
  if (!["accepted", "candidate"].includes(result.variant)) fail("variant is invalid");
  for (const key of ["case-id", "state"]) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(result[key])) fail(`${key} is invalid`);
  }
  return result;
}

function boundedString(value, label, maximum = 500) {
  if (typeof value !== "string" || value.length < 1 || value.length > maximum || value.trim() !== value) {
    fail(`${label} is invalid`);
  }
}

function validateSpecValue(value, expectedCase, expectedState) {
  const rootKeys = ["assertions", "caseId", "schemaVersion", "state", "steps", "targets"];
  if (Object.keys(value).sort().join("|") !== rootKeys.sort().join("|") || value.schemaVersion !== 1
      || value.caseId !== expectedCase || value.state !== expectedState) {
    fail("hidden spec root contract is invalid");
  }
  const minimum = expectedState === "interaction" ? 1 : 0;
  if (!Array.isArray(value.steps) || value.steps.length < minimum || value.steps.length > 20
      || !Array.isArray(value.assertions) || value.assertions.length < minimum || value.assertions.length > 20
      || !Array.isArray(value.targets) || value.targets.length < 1 || value.targets.length > 64) {
    fail("hidden spec entry budget is invalid");
  }
  const stepSchemas = {
    click: ["action", "id", "selector"],
    fill: ["action", "id", "selector", "value"],
    select: ["action", "id", "selector", "value"],
    press: ["action", "id", "selector", "value"],
  };
  const assertionSchemas = {
    visible: ["id", "selector", "type"],
    hidden: ["id", "selector", "type"],
    text: ["id", "selector", "type", "value"],
  };
  const ids = { steps: new Set(), assertions: new Set(), targets: new Set() };
  for (const [index, step] of value.steps.entries()) {
    if (!step || typeof step !== "object" || Array.isArray(step) || !Object.hasOwn(stepSchemas, step.action)
        || Object.keys(step).sort().join("|") !== [...stepSchemas[step.action]].sort().join("|")) {
      fail(`hidden step ${index} contract is invalid`);
    }
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(step.id || "") || ids.steps.has(step.id)) fail("hidden step id is invalid");
    ids.steps.add(step.id);
    boundedString(step.selector, `hidden step ${index} selector`, 300);
    if (step.value !== undefined) boundedString(step.value, `hidden step ${index} value`, 300);
  }
  for (const [index, assertion] of value.assertions.entries()) {
    if (!assertion || typeof assertion !== "object" || Array.isArray(assertion)
        || !Object.hasOwn(assertionSchemas, assertion.type)
        || Object.keys(assertion).sort().join("|") !== [...assertionSchemas[assertion.type]].sort().join("|")) {
      fail(`hidden assertion ${index} contract is invalid`);
    }
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(assertion.id || "") || ids.assertions.has(assertion.id)) {
      fail("hidden assertion id is invalid");
    }
    ids.assertions.add(assertion.id);
    boundedString(assertion.selector, `hidden assertion ${index} selector`, 300);
    if (assertion.value !== undefined) boundedString(assertion.value, `hidden assertion ${index} value`, 300);
  }
  for (const target of value.targets) {
    const expected = ["id", "mode", "ownerSelector", "role", "selector"];
    if (target?.peerSelector !== undefined) expected.push("peerSelector");
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== expected.sort().join("|")
        || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(target.id || "") || ids.targets.has(target.id)
        || !["product", "editorial", "display"].includes(target.mode)
        || !["heading", "prose"].includes(target.role)) {
      fail("hidden target contract is invalid");
    }
    ids.targets.add(target.id);
    boundedString(target.selector, `hidden target ${target.id} selector`, 300);
    boundedString(target.ownerSelector, `hidden target ${target.id} owner`, 300);
    if (target.peerSelector !== undefined) boundedString(target.peerSelector, `hidden target ${target.id} peer`, 300);
  }
  return value;
}

function validateTarget(routeArgument, manifestArgument) {
  const route = stableFile(routeArgument, "route", 8 * 1024 * 1024);
  const manifest = loadJson(manifestArgument, "target manifest");
  if (path.dirname(route.absolute) !== path.dirname(manifest.absolute)
      || path.basename(route.absolute) !== "index.html"
      || path.basename(manifest.absolute) !== "run-manifest.json") {
    fail("route and target manifest must bind one target root");
  }
  const value = manifest.value;
  if (value.schema_version !== 1 || value.status !== "completed" || !Array.isArray(value.outputs) || value.outputs.length !== 2) {
    fail("target manifest contract is invalid");
  }
  const indexed = new Map(value.outputs.map((item) => [item?.path, item]));
  if (indexed.size !== 2 || !indexed.has("DESIGN.md") || !indexed.has("index.html")) fail("target outputs are incomplete");
  const snapshots = { "index.html": route };
  for (const name of ["DESIGN.md", "index.html"]) {
    const file = snapshots[name] || stableFile(
      path.join(path.dirname(manifest.absolute), name), `target ${name}`, 8 * 1024 * 1024
    );
    const record = indexed.get(name);
    if (!record || Object.keys(record).sort().join("|") !== "bytes|path|sha256"
        || record.bytes !== file.bytesLength || record.sha256 !== file.sha256) {
      fail(`target ${name} receipt drifted`);
    }
    snapshots[name] = file;
  }
  return {
    route: route.absolute,
    manifest: manifest.absolute,
    routeSha256: route.sha256,
    manifestSha256: manifest.sha256,
    snapshots,
    manifestBytes: manifest.bytes,
  };
}

function hiddenAnchors(spec, contract) {
  const anchors = [];
  for (const target of spec.targets) {
    anchors.push({ id: `${target.id}:target`, selector: target.selector });
    anchors.push({ id: `${target.id}:owner`, selector: target.ownerSelector });
    if (target.peerSelector) anchors.push({ id: `${target.id}:peer`, selector: target.peerSelector });
  }
  for (const step of spec.steps) anchors.push({ id: `${step.id}:step`, selector: step.selector });
  for (const assertion of spec.assertions) anchors.push({ id: `${assertion.id}:assertion`, selector: assertion.selector });
  const unique = [];
  const seen = new Set();
  for (const anchor of anchors) {
    const key = `${anchor.id}\u0000${anchor.selector}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(anchor);
    }
  }
  if (unique.length < 1 || unique.length > contract.max_hidden_selectors) fail("hidden selector budget exceeded");
  return unique;
}

async function applySteps(page, steps) {
  for (const step of steps) {
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) fail(`interaction step ${step.id} is unavailable`);
    if (step.action === "click") await locator.click();
    else if (step.action === "fill") await locator.fill(step.value);
    else if (step.action === "select") await locator.selectOption(step.value);
    else await locator.press(step.value);
  }
}

async function assertionsPassed(page, assertions) {
  for (const assertion of assertions) {
    const locator = page.locator(assertion.selector);
    const count = await locator.count();
    if (assertion.type === "visible" && !(count === 1 && await locator.isVisible())) return false;
    if (assertion.type === "hidden" && !(count === 0 || (count === 1 && !(await locator.isVisible())))) return false;
    if (assertion.type === "text" && !(count === 1 && (await locator.textContent() || "").includes(assertion.value))) return false;
  }
  return true;
}

function browserModeSnapshot({ anchors, maxNodes, maxChildren }) {
  const visible = (node) => {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0
      && rect.width > 0.5 && rect.height > 0.5;
  };
  const clusters = (values) => {
    const sorted = [...values].sort((left, right) => left - right);
    const groups = [];
    for (const value of sorted) {
      if (!groups.length || Math.abs(value - groups[groups.length - 1]) > 8) groups.push(value);
    }
    return groups.length;
  };
  const records = anchors.map((anchor) => {
    let nodes;
    try {
      nodes = [...document.querySelectorAll(anchor.selector)];
    } catch {
      return { id: anchor.id, selectorValid: false, count: 0, visibleCount: 0, modes: [] };
    }
    const inspected = nodes.slice(0, maxNodes);
    const modes = inspected.map((node) => {
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      const children = [...node.children].filter(visible).slice(0, maxChildren).map((child) => {
        const childRect = child.getBoundingClientRect();
        return { x: childRect.left + childRect.width / 2, y: childRect.top + childRect.height / 2 };
      });
      return {
        visible: visible(node),
        display: style.display.slice(0, 40),
        position: style.position.slice(0, 20),
        writingMode: style.writingMode.slice(0, 30),
        flexDirection: style.flexDirection.slice(0, 20),
        flexWrap: style.flexWrap.slice(0, 20),
        childRows: clusters(children.map((item) => item.y)),
        childColumns: clusters(children.map((item) => item.x)),
        clippedX: rect.left < -2 || rect.right > innerWidth + 2,
        clippedY: rect.top < -2 || rect.bottom > innerHeight + 2,
      };
    });
    return {
      id: anchor.id,
      selectorValid: true,
      count: nodes.length > maxNodes ? "many" : nodes.length,
      visibleCount: modes.filter((mode) => mode.visible).length,
      modes,
    };
  });
  return {
    horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 2,
    anchors: records,
  };
}

function unavailableReport(base, reasonCode, coverage = {}) {
  return {
    ...base,
    status: "unavailable",
    coverage: {
      status: "unavailable",
      reason_code: reasonCode,
      sample_count: coverage.sample_count || 0,
      sampled_widths: coverage.sampled_widths || [],
      budget_exhausted: Boolean(coverage.budget_exhausted),
    },
    transitions: [],
    findings: [],
    advisories: [],
  };
}

function validateBreakpointReport(report, contract) {
  if (!exactKeys(report, OUTPUT_KEYS) || report.schema_version !== 1
      || !["complete", "unavailable"].includes(report.status)
      || report.authority !== contract.authority || report.claim_boundary !== contract.claim_boundary) {
    fail("breakpoint output root schema changed");
  }
  if (!exactKeys(report.identity, ["variant", "case_id", "state"])
      || !["accepted", "candidate"].includes(report.identity.variant)
      || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(report.identity.case_id)
      || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(report.identity.state)) {
    fail("breakpoint output identity is invalid");
  }
  if (!exactKeys(report.subject, ["route", "route_sha256", "manifest", "manifest_sha256", "spec", "spec_sha256"])
      || report.subject.route !== "index.html" || report.subject.manifest !== "run-manifest.json"
      || report.subject.spec !== "hidden-spec" || !isSha256(report.subject.route_sha256)
      || !isSha256(report.subject.manifest_sha256) || !isSha256(report.subject.spec_sha256)) {
    fail("breakpoint output subject is invalid");
  }
  const probeKeys = ["id", "script_sha256", "contract_sha256", "playwright", "dependencies", "engine"];
  if (Object.hasOwn(report.probe || {}, "engine_version")) probeKeys.push("engine_version");
  if (!exactKeys(report.probe, probeKeys) || report.probe.id !== contract.probe_id
      || !isSha256(report.probe.script_sha256) || !isSha256(report.probe.contract_sha256)
      || report.probe.playwright !== contract.dependencies.playwright_manifest.version
      || report.probe.engine !== "chromium"
      || !exactKeys(report.probe.dependencies, ["playwright_entrypoint_sha256", "playwright_manifest_sha256"])
      || report.probe.dependencies.playwright_entrypoint_sha256 !== contract.dependencies.playwright_entrypoint.sha256
      || report.probe.dependencies.playwright_manifest_sha256 !== contract.dependencies.playwright_manifest.sha256
      || (Object.hasOwn(report.probe, "engine_version")
        && (typeof report.probe.engine_version !== "string" || report.probe.engine_version.length > 100))) {
    fail("breakpoint output probe is invalid");
  }
  if (!exactKeys(report.contract, ["widths", "height", "device_scale_factor", "max_samples", "max_depth", "max_transitions", "screenshots", "traces", "videos"])
      || canonical(report.contract.widths) !== canonical(contract.widths)
      || report.contract.height !== contract.height
      || report.contract.device_scale_factor !== contract.device_scale_factor
      || report.contract.max_samples !== contract.max_samples || report.contract.max_depth !== contract.max_depth
      || report.contract.max_transitions !== contract.max_transitions
      || report.contract.screenshots !== false || report.contract.traces !== false
      || report.contract.videos !== false) {
    fail("breakpoint output contract is invalid");
  }
  if (!exactKeys(report.coverage, ["status", "reason_code", "sample_count", "sampled_widths", "budget_exhausted"])
      || !Number.isInteger(report.coverage.sample_count) || report.coverage.sample_count < 0
      || report.coverage.sample_count > contract.max_samples || !Array.isArray(report.coverage.sampled_widths)
      || report.coverage.sampled_widths.length > contract.max_samples
      || typeof report.coverage.budget_exhausted !== "boolean") {
    fail("breakpoint output coverage is invalid");
  }
  const minimumWidth = Math.min(...contract.widths);
  const maximumWidth = Math.max(...contract.widths);
  const sampled = report.coverage.sampled_widths;
  if (sampled.some((width) => !Number.isInteger(width) || width < minimumWidth || width > maximumWidth)
      || sampled.some((width, index) => index > 0 && width <= sampled[index - 1])
      || report.coverage.sample_count < sampled.length) {
    fail("breakpoint output sampled widths are invalid");
  }
  const unavailable = report.status === "unavailable";
  if (unavailable !== (report.coverage.status === "unavailable")
      || (unavailable ? !REASON_CODES.has(report.coverage.reason_code)
        : report.coverage.status !== "complete" || report.coverage.reason_code !== null
          || report.coverage.budget_exhausted)) {
    fail("breakpoint output reason is invalid");
  }
  if (!unavailable && contract.widths.some((width) => !sampled.includes(width))) {
    fail("breakpoint output baseline coverage is incomplete");
  }
  if (!Array.isArray(report.transitions) || report.transitions.length > contract.max_transitions
      || report.transitions.some((item) => !exactKeys(item, ["lower_width", "upper_width", "from", "to"])
        || !Number.isInteger(item.lower_width) || item.upper_width !== item.lower_width + 1
        || item.lower_width < minimumWidth || item.upper_width > maximumWidth
        || !isSha256(item.from) || !isSha256(item.to) || item.from === item.to)) {
    fail("breakpoint output transitions are invalid");
  }
  if (!Array.isArray(report.findings) || report.findings.length > contract.max_samples * 2
      || report.findings.some((item) => !exactKeys(item, ["code", "width", "replays"])
        || !["breakpoint_horizontal_overflow", "breakpoint_required_assertion_failed"].includes(item.code)
        || !sampled.includes(item.width) || item.replays !== 2)) {
    fail("breakpoint output findings are invalid");
  }
  if (!Array.isArray(report.advisories) || report.advisories.length > contract.max_transitions + contract.max_samples
      || report.advisories.some((item) => {
        if (item?.code === "responsive_mode_transition") {
          return !exactKeys(item, ["code", "lower_width", "upper_width"])
            || item.upper_width !== item.lower_width + 1 || item.lower_width < minimumWidth
            || item.upper_width > maximumWidth;
        }
        return item?.code !== "same_width_replay_changed" || !exactKeys(item, ["code", "width"])
          || !sampled.includes(item.width);
      })) {
    fail("breakpoint output advisories are invalid");
  }
  if (unavailable && (report.transitions.length || report.findings.length || report.advisories.length)) {
    fail("unavailable breakpoint output must not make claims");
  }
}

async function locateTransitions(widths, sample, contract) {
  const cache = new Map();
  const transitions = [];
  let budgetExhausted = false;
  const read = async (width) => {
    if (cache.has(width)) return cache.get(width);
    if (cache.size >= contract.max_samples) {
      budgetExhausted = true;
      throw new Error("sample_budget_exhausted");
    }
    const value = await sample(width);
    cache.set(width, value);
    return value;
  };
  const visit = async (leftWidth, rightWidth, depth) => {
    const left = await read(leftWidth);
    const right = await read(rightWidth);
    if (left.signature === right.signature) return;
    if (rightWidth - leftWidth <= 1) {
      transitions.push({ lower_width: leftWidth, upper_width: rightWidth, from: left.signature, to: right.signature });
      if (transitions.length > contract.max_transitions) throw new Error("transition_budget_exhausted");
      return;
    }
    if (depth >= contract.max_depth) throw new Error("depth_budget_exhausted");
    const midpoint = Math.floor((leftWidth + rightWidth) / 2);
    await read(midpoint);
    await visit(leftWidth, midpoint, depth + 1);
    await visit(midpoint, rightWidth, depth + 1);
  };
  try {
    for (const width of widths) await read(width);
    for (let index = 0; index < widths.length - 1; index += 1) {
      await visit(widths[index], widths[index + 1], 0);
    }
  } catch (error) {
    return {
      status: "unavailable",
      reason_code: reasonCode(error),
      samples: cache,
      transitions: [],
      budget_exhausted: budgetExhausted || /budget/.test(error.message),
    };
  }
  transitions.sort((left, right) => left.lower_width - right.lower_width || left.upper_width - right.upper_width);
  return { status: "complete", reason_code: null, samples: cache, transitions, budget_exhausted: false };
}

async function main() {
  const args = parseArguments(process.argv.slice(2));
  const output = freshOutput(args.output);
  const contractRecord = loadContract();
  const contract = contractRecord.value;
  const target = validateTarget(args.route, args["target-manifest"]);
  const specRecord = loadJson(args.spec, "hidden spec");
  const spec = validateSpecValue(specRecord.value, args["case-id"], args.state);
  const scriptRecord = stableFile(__filename, "breakpoint probe script", 2 * 1024 * 1024);
  const anchors = hiddenAnchors(spec, contract);
  const temporaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), "wow-v7-breakpoint-"));
  fs.chmodSync(temporaryRoot, 0o700);
  const snapshotRoute = path.join(temporaryRoot, "index.html");
  fs.writeFileSync(snapshotRoute, target.snapshots["index.html"].bytes, { flag: "wx", mode: 0o600 });
  if (stableFile(snapshotRoute, "route snapshot", 8 * 1024 * 1024).sha256 !== target.routeSha256) {
    fail("route snapshot changed");
  }
  const playwright = require("playwright");
  const runtimePlaywrightVersion = require("playwright/package.json").version;
  if (runtimePlaywrightVersion !== contract.dependencies.playwright_manifest.version) {
    fail("Playwright runtime version drifted");
  }
  const base = {
    schema_version: 1,
    authority: contract.authority,
    claim_boundary: contract.claim_boundary,
    identity: { variant: args.variant, case_id: args["case-id"], state: args.state },
    subject: {
      route: path.basename(target.route),
      route_sha256: target.routeSha256,
      manifest: "run-manifest.json",
      manifest_sha256: target.manifestSha256,
      spec: "hidden-spec",
      spec_sha256: specRecord.sha256,
    },
    probe: {
      id: contract.probe_id,
      script_sha256: scriptRecord.sha256,
      contract_sha256: contractRecord.sha256,
      playwright: runtimePlaywrightVersion,
      dependencies: {
        playwright_entrypoint_sha256: contract.dependencies.playwright_entrypoint.sha256,
        playwright_manifest_sha256: contract.dependencies.playwright_manifest.sha256,
      },
      engine: "chromium",
    },
    contract: {
      widths: contract.widths,
      height: contract.height,
      device_scale_factor: contract.device_scale_factor,
      max_samples: contract.max_samples,
      max_depth: contract.max_depth,
      max_transitions: contract.max_transitions,
      screenshots: false,
      traces: false,
      videos: false,
    },
  };
  const verifyProvenance = () => {
    try {
      const currentContract = loadContract();
      const currentTarget = validateTarget(args.route, args["target-manifest"]);
      const currentSpec = stableFile(specRecord.absolute, "hidden spec");
      const currentScript = stableFile(__filename, "breakpoint probe script", 2 * 1024 * 1024);
      if (currentContract.sha256 !== contractRecord.sha256
          || currentTarget.routeSha256 !== target.routeSha256
          || currentTarget.manifestSha256 !== target.manifestSha256
          || currentTarget.snapshots["DESIGN.md"].sha256 !== target.snapshots["DESIGN.md"].sha256
          || currentSpec.sha256 !== specRecord.sha256
          || currentScript.sha256 !== scriptRecord.sha256
          || stableFile(snapshotRoute, "route snapshot", 8 * 1024 * 1024).sha256 !== target.routeSha256) {
        throw new Error("drift");
      }
    } catch {
      throw new Error("probe_provenance_drift");
    }
  };
  const writeReport = (report, exitCode = 0) => {
    validateBreakpointReport(report, contract);
    const serialized = `${JSON.stringify(report, null, 2)}\n`;
    if (Buffer.byteLength(serialized) > MAX_JSON_BYTES) fail("output exceeds its byte budget");
    fs.writeFileSync(output, serialized, { flag: "wx", mode: 0o600 });
    process.stdout.write(`${JSON.stringify({ status: report.status, output: path.basename(output) })}\n`);
    process.exitCode = exitCode;
  };
  let browser;
  try {
    try {
      verifyProvenance();
    } catch {
      writeReport(unavailableReport(base, "probe_provenance_drift"), 2);
      return;
    }
    try {
      browser = await playwright.chromium.launch({ headless: true });
    } catch {
      writeReport(unavailableReport(base, "probe_execution_unavailable"), 2);
      return;
    }
    base.probe.engine_version = browser.version();
    const sample = async (width) => {
      verifyProvenance();
      const context = await browser.newContext({
        viewport: { width, height: contract.height },
        screen: { width, height: contract.height },
        deviceScaleFactor: contract.device_scale_factor,
        hasTouch: false,
        isMobile: false,
        serviceWorkers: "block",
        locale: "zh-TW",
        timezoneId: "Asia/Taipei",
        reducedMotion: "reduce",
      });
      let externalRequests = 0;
      let runtimeErrors = 0;
      try {
        const routeUrl = pathToFileURL(snapshotRoute);
        await context.route("**/*", async (route) => {
          const requestUrl = new URL(route.request().url());
          if (["data:", "blob:"].includes(requestUrl.protocol) || requestUrl.href === routeUrl.href) await route.continue();
          else {
            externalRequests += 1;
            await route.abort("blockedbyclient");
          }
        });
        const page = await context.newPage();
        page.on("console", (message) => { if (message.type() === "error") runtimeErrors += 1; });
        page.on("pageerror", () => { runtimeErrors += 1; });
        await page.goto(routeUrl.href, { waitUntil: "domcontentloaded", timeout: 30000 });
        const fontsReady = await page.evaluate(async (timeout) => Promise.race([
          document.fonts.ready.then(() => true),
          new Promise((resolve) => setTimeout(() => resolve(false), timeout)),
        ]), contract.settle_timeout_ms);
        if (!fontsReady) throw new Error("fonts_unavailable");
        await applySteps(page, spec.steps);
        await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const assertionPass = await assertionsPassed(page, spec.assertions);
        const payload = { anchors, maxNodes: contract.max_nodes_per_selector, maxChildren: contract.max_children_per_node };
        const first = await page.evaluate(browserModeSnapshot, payload);
        await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const second = await page.evaluate(browserModeSnapshot, payload);
        if (modeHash(first) !== modeHash(second)) throw new Error("layout_signature_unstable");
        if (externalRequests || runtimeErrors) throw new Error("runtime_or_external_event");
        const mode = { ...second, requiredAssertionsPassed: assertionPass };
        return {
          signature: modeHash(mode),
          horizontal_overflow: second.horizontalOverflow,
          required_assertions_passed: assertionPass,
        };
      } finally {
        await context.close().catch(() => {});
      }
    };
    const located = await locateTransitions(contract.widths, sample, contract);
    const sampledWidths = [...located.samples.keys()].sort((left, right) => left - right);
    if (located.status !== "complete") {
      const report = unavailableReport(base, located.reason_code, {
        sample_count: located.samples.size,
        sampled_widths: sampledWidths,
        budget_exhausted: located.budget_exhausted,
      });
      writeReport(report, 2);
      return;
    }
    const candidateRisks = [...located.samples.entries()].filter(([, value]) => (
      value.horizontal_overflow || !value.required_assertions_passed
    ));
    const findings = [];
    const advisories = located.transitions.map((transition) => ({
      code: "responsive_mode_transition",
      lower_width: transition.lower_width,
      upper_width: transition.upper_width,
    }));
    if (located.samples.size + candidateRisks.length > contract.max_samples) {
        const report = unavailableReport(base, "sample_budget_exhausted", {
          sample_count: located.samples.size,
          sampled_widths: sampledWidths,
          budget_exhausted: true,
        });
        writeReport(report, 2);
        return;
    }
    let replayCount = 0;
    for (const [width, first] of candidateRisks) {
      let replay;
      try {
        replay = await sample(width);
        replayCount += 1;
      } catch (error) {
        const report = unavailableReport(base, reasonCode(error), {
          sample_count: located.samples.size + replayCount,
          sampled_widths: sampledWidths,
          budget_exhausted: false,
        });
        writeReport(report, 2);
        return;
      }
      if (first.horizontal_overflow && replay.horizontal_overflow) {
        findings.push({ code: "breakpoint_horizontal_overflow", width, replays: 2 });
      }
      if (!first.required_assertions_passed && !replay.required_assertions_passed) {
        findings.push({ code: "breakpoint_required_assertion_failed", width, replays: 2 });
      }
      if (first.signature !== replay.signature) {
        advisories.push({ code: "same_width_replay_changed", width });
      }
    }
    const report = {
      ...base,
      status: "complete",
      coverage: {
        status: "complete",
        reason_code: null,
        sample_count: located.samples.size + replayCount,
        sampled_widths: sampledWidths,
        budget_exhausted: false,
      },
      transitions: located.transitions,
      findings,
      advisories,
    };
    try {
      verifyProvenance();
    } catch {
      writeReport(unavailableReport(base, "probe_provenance_drift", {
        sample_count: located.samples.size + replayCount,
        sampled_widths: sampledWidths,
        budget_exhausted: false,
      }), 2);
      return;
    }
    writeReport(report);
  } finally {
    await browser?.close().catch(() => {});
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`v7 breakpoint probe failed: ${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = {
  applySteps,
  assertionsPassed,
  browserModeSnapshot,
  canonical,
  hiddenAnchors,
  loadContract,
  locateTransitions,
  modeHash,
  parseArguments,
  reasonCode,
  stableFile,
  validateSpecValue,
  validateBreakpointReport,
  validateTarget,
};
