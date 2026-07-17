#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const CONTRACT_PATH = path.join(__dirname, "v7-motion-probe-contract.json");
const MAX_JSON_BYTES = 1024 * 1024;
const OUTPUT_KEYS = [
  "schema_version", "status", "authority", "claim_boundary", "identity", "subject",
  "probe", "contract", "coverage", "motion", "findings", "advisories",
];
const REASON_CODES = new Set([
  "animation_budget_exhausted", "fonts_unavailable", "motion_preference_unavailable",
  "probe_execution_unavailable", "probe_provenance_drift", "runtime_or_external_event",
  "sample_budget_exhausted",
]);
const FINDING_CODES = new Set([
  "reduced_motion_task_regression", "reduced_motion_horizontal_overflow",
]);
const ADVISORY_CODES = new Set(["reduced_motion_no_categorical_change"]);

function fail(message) {
  throw new Error(message);
}

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
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
  const descriptor = fs.openSync(absolute, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0));
  try {
    const before = fs.fstatSync(descriptor);
    if (!before.isFile() || before.size < 1 || before.size > maximum) fail(`${label} is not a bounded regular file`);
    const bytes = fs.readFileSync(descriptor);
    const after = fs.fstatSync(descriptor);
    if (before.dev !== after.dev || before.ino !== after.ino || before.size !== after.size
        || before.mtimeMs !== after.mtimeMs || bytes.length !== before.size) {
      fail(`${label} changed while it was read`);
    }
    return { absolute, bytes, sha256: sha256(bytes) };
  } finally {
    fs.closeSync(descriptor);
  }
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

function loadContract() {
  const record = stableFile(CONTRACT_PATH, "motion contract", 64 * 1024);
  let value;
  try {
    value = JSON.parse(record.bytes.toString("utf8"));
  } catch {
    fail("motion contract is invalid JSON");
  }
  const expected = {
    schema_version: 1,
    probe_id: "v7-reduced-motion-v1",
    authority: "supporting-discovery-only",
    claim_boundary: "Bounded Chromium normal/reduce computed-motion comparison only; no screenshot, cross-engine, physical-device, visual-quality, WCAG-conformance or release claim.",
    widths: [390, 1024],
    height: 844,
    device_scale_factor: 1,
    max_samples: 12,
    max_animations: 64,
    max_hidden_selectors: 40,
    max_nodes_per_selector: 4,
    max_children_per_node: 32,
    settle_timeout_ms: 10000,
    dependencies: {
      breakpoint_helper: {
        path: "evals/playwright_v7_breakpoint_probe.cjs",
        sha256: "8079cf820d5c9f6f81caa48e1c57bfaec13decaa062fdd572607e2a86ce4c6cd",
      },
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
    screenshots: false,
    traces: false,
    videos: false,
  };
  if (canonical(value) !== canonical(expected)) fail("motion contract changed");
  const repositoryRoot = path.resolve(__dirname, "..");
  const dependencies = {};
  for (const [name, binding] of Object.entries(value.dependencies)) {
    const dependency = stableFile(path.join(repositoryRoot, binding.path), `motion dependency ${name}`, 64 * 1024);
    if (dependency.sha256 !== binding.sha256) fail(`motion dependency ${name} drifted`);
    dependencies[name] = dependency;
  }
  const manifest = JSON.parse(dependencies.playwright_manifest.bytes.toString("utf8"));
  if (manifest.version !== value.dependencies.playwright_manifest.version) fail("Playwright version drifted");
  return { ...record, value, dependencies };
}

function freshOutput(file) {
  const absolute = path.resolve(file);
  if (fs.existsSync(absolute)) fail("output already exists");
  const parent = securePath(path.dirname(absolute), "output parent");
  if (!fs.lstatSync(parent).isDirectory()) fail("output parent is unsafe");
  return absolute;
}

function motionSnapshot(maximum) {
  const animations = document.getAnimations();
  if (animations.length > maximum) return { budgetExceeded: true };
  const buckets = {};
  let active = 0;
  let infinite = 0;
  for (const animation of animations) {
    if (["running", "pending"].includes(animation.playState)) active += 1;
    const timing = animation.effect?.getComputedTiming?.() || {};
    if (timing.iterations === Infinity) infinite += 1;
    const duration = typeof timing.duration === "number" ? timing.duration : 0;
    const durationBucket = duration <= 16 ? "instant" : duration <= 200 ? "short"
      : duration <= 1000 ? "medium" : "long";
    const constructorName = animation.constructor?.name;
    const kind = constructorName === "CSSAnimation" ? "css_animation"
      : constructorName === "CSSTransition" ? "css_transition" : "web_animation";
    const key = `${kind}:${durationBucket}:${timing.iterations === Infinity ? "infinite" : "finite"}`;
    buckets[key] = (buckets[key] || 0) + 1;
  }
  return {
    budgetExceeded: false,
    total: animations.length,
    active,
    infinite,
    categories: Object.fromEntries(Object.entries(buckets).sort(([left], [right]) => left.localeCompare(right))),
    reduceMediaMatches: matchMedia("(prefers-reduced-motion: reduce)").matches,
  };
}

function unavailable(base, reasonCode, sampleCount = 0) {
  return {
    ...base,
    status: "unavailable",
    coverage: { status: "unavailable", reason_code: reasonCode, sample_count: sampleCount },
    motion: { status: "unavailable", observations: [] },
    findings: [],
    advisories: [],
  };
}

function confirmedRegressionCodes(normal, reduce, normalReplay, reduceReplay) {
  const codes = [];
  if (normal.assertions_passed && !reduce.assertions_passed
      && normalReplay.motion.total > 0
      && normalReplay.assertions_passed && !reduceReplay.assertions_passed) {
    codes.push("reduced_motion_task_regression");
  }
  if (!normal.horizontal_overflow && reduce.horizontal_overflow
      && normalReplay.motion.total > 0
      && !normalReplay.horizontal_overflow && reduceReplay.horizontal_overflow) {
    codes.push("reduced_motion_horizontal_overflow");
  }
  return codes;
}

function validateMotionReport(report, contract) {
  if (!exactKeys(report, OUTPUT_KEYS) || report.schema_version !== 1
      || !["complete", "unavailable"].includes(report.status)
      || report.authority !== contract.authority || report.claim_boundary !== contract.claim_boundary) {
    fail("motion output root schema changed");
  }
  if (!exactKeys(report.identity, ["variant", "case_id", "state"])
      || !["accepted", "candidate"].includes(report.identity.variant)
      || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(report.identity.case_id)
      || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(report.identity.state)) {
    fail("motion output identity is invalid");
  }
  if (!exactKeys(report.subject, ["route", "route_sha256", "manifest", "manifest_sha256", "spec", "spec_sha256"])
      || report.subject.route !== "index.html" || report.subject.manifest !== "run-manifest.json"
      || report.subject.spec !== "hidden-spec" || !isSha256(report.subject.route_sha256)
      || !isSha256(report.subject.manifest_sha256) || !isSha256(report.subject.spec_sha256)) {
    fail("motion output subject is invalid");
  }
  const probeKeys = ["id", "script_sha256", "contract_sha256", "helper_sha256", "playwright", "engine"];
  if (Object.hasOwn(report.probe || {}, "engine_version")) probeKeys.push("engine_version");
  if (!exactKeys(report.probe, probeKeys) || report.probe.id !== contract.probe_id
      || !isSha256(report.probe.script_sha256) || !isSha256(report.probe.contract_sha256)
      || report.probe.helper_sha256 !== contract.dependencies.breakpoint_helper.sha256
      || report.probe.playwright !== contract.dependencies.playwright_manifest.version
      || report.probe.engine !== "chromium"
      || (Object.hasOwn(report.probe, "engine_version")
        && (typeof report.probe.engine_version !== "string" || report.probe.engine_version.length > 100))) {
    fail("motion output probe is invalid");
  }
  if (!exactKeys(report.contract, ["widths", "height", "device_scale_factor", "max_samples", "max_animations", "screenshots", "traces", "videos"])
      || canonical(report.contract.widths) !== canonical(contract.widths)
      || report.contract.height !== contract.height
      || report.contract.device_scale_factor !== contract.device_scale_factor
      || report.contract.max_samples !== contract.max_samples
      || report.contract.max_animations !== contract.max_animations
      || report.contract.screenshots !== false || report.contract.traces !== false
      || report.contract.videos !== false) {
    fail("motion output contract is invalid");
  }
  if (!exactKeys(report.coverage, ["status", "reason_code", "sample_count"])
      || !Number.isInteger(report.coverage.sample_count) || report.coverage.sample_count < 0
      || report.coverage.sample_count > contract.max_samples) {
    fail("motion output coverage is invalid");
  }
  const unavailableReport = report.status === "unavailable";
  if (unavailableReport !== (report.coverage.status === "unavailable")
      || (unavailableReport ? !REASON_CODES.has(report.coverage.reason_code)
        : report.coverage.status !== "complete" || report.coverage.reason_code !== null)) {
    fail("motion output reason is invalid");
  }
  if (!exactKeys(report.motion, ["status", "observations"]) || !Array.isArray(report.motion.observations)
      || report.motion.observations.length > contract.widths.length
      || (unavailableReport && (report.motion.status !== "unavailable" || report.motion.observations.length !== 0))
      || (!unavailableReport && !["complete", "not_applicable"].includes(report.motion.status))) {
    fail("motion output observations are invalid");
  }
  const validateSample = (sample, expectedPreference) => {
    if (!exactKeys(sample, ["preference", "assertions_passed", "horizontal_overflow", "layout_signature", "motion"])
        || sample.preference !== expectedPreference || typeof sample.assertions_passed !== "boolean"
        || typeof sample.horizontal_overflow !== "boolean" || !isSha256(sample.layout_signature)
        || !exactKeys(sample.motion, ["budgetExceeded", "total", "active", "infinite", "categories", "reduceMediaMatches"])
        || sample.motion.budgetExceeded !== false
        || ![sample.motion.total, sample.motion.active, sample.motion.infinite].every(Number.isInteger)
        || sample.motion.total < 0 || sample.motion.total > contract.max_animations
        || sample.motion.active < 0 || sample.motion.active > sample.motion.total
        || sample.motion.infinite < 0 || sample.motion.infinite > sample.motion.total
        || sample.motion.reduceMediaMatches !== (expectedPreference === "reduce")
        || !sample.motion.categories || typeof sample.motion.categories !== "object"
        || Array.isArray(sample.motion.categories)) fail("motion output sample is invalid");
    let categoryTotal = 0;
    for (const [key, count] of Object.entries(sample.motion.categories)) {
      if (!/^(css_animation|css_transition|web_animation):(instant|short|medium|long):(finite|infinite)$/.test(key)
          || !Number.isInteger(count) || count < 1 || count > contract.max_animations) {
        fail("motion output category is invalid");
      }
      categoryTotal += count;
    }
    if (categoryTotal !== sample.motion.total) fail("motion output category total is invalid");
  };
  for (const observation of report.motion.observations) {
    if (!exactKeys(observation, ["width", "normal", "reduce", "replayed"])
        || typeof observation.replayed !== "boolean"
        || !contract.widths.includes(observation.width)) fail("motion output observation is invalid");
    validateSample(observation.normal, "no-preference");
    if (observation.normal.motion.total === 0) {
      if (observation.reduce !== null) fail("motion output reduce lane is invalid");
    } else {
      validateSample(observation.reduce, "reduce");
    }
  }
  if (!unavailableReport) {
    if (report.motion.observations.map((item) => item.width).join("|") !== contract.widths.join("|")) {
      fail("motion output width coverage is incomplete");
    }
    const expectedSamples = report.motion.observations.reduce((total, item) => (
      total + 1 + (item.reduce === null ? 0 : 1) + (item.replayed ? 2 : 0)
    ), 0);
    if (report.coverage.sample_count !== expectedSamples) fail("motion output sample receipt is invalid");
  }
  if (unavailableReport && (report.findings.length || report.advisories.length)) {
    fail("unavailable motion output must not make claims");
  }
  if (!Array.isArray(report.findings) || report.findings.length > contract.widths.length * FINDING_CODES.size
      || report.findings.some((item) => !exactKeys(item, ["code", "width", "replays"])
        || !FINDING_CODES.has(item.code) || !contract.widths.includes(item.width) || item.replays !== 2)) {
    fail("motion output findings are invalid");
  }
  if (!Array.isArray(report.advisories) || report.advisories.length > contract.widths.length
      || report.advisories.some((item) => !exactKeys(item, ["code", "width"])
        || !ADVISORY_CODES.has(item.code) || !contract.widths.includes(item.width))) {
    fail("motion output advisories are invalid");
  }
  const observedMotion = report.motion.observations.some((item) => item.normal.motion.total > 0);
  if (!unavailableReport && ((report.motion.status === "complete") !== observedMotion)) {
    fail("motion output applicability is invalid");
  }
}

async function main() {
  const contractRecord = loadContract();
  const helper = require("./playwright_v7_breakpoint_probe.cjs");
  const args = helper.parseArguments(process.argv.slice(2));
  const output = freshOutput(args.output);
  const contract = contractRecord.value;
  if (path.basename(path.resolve(args["target-manifest"])) !== "run-manifest.json") {
    fail("target manifest filename is invalid");
  }
  const target = helper.validateTarget(args.route, args["target-manifest"]);
  const specRecord = stableFile(args.spec, "hidden spec");
  let specValue;
  try {
    specValue = JSON.parse(specRecord.bytes.toString("utf8"));
  } catch {
    fail("hidden spec is invalid JSON");
  }
  const spec = helper.validateSpecValue(specValue, args["case-id"], args.state);
  const anchors = helper.hiddenAnchors(spec, contract);
  const scriptRecord = stableFile(__filename, "motion probe script", 2 * 1024 * 1024);
  const temporaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), "wow-v7-motion-"));
  fs.chmodSync(temporaryRoot, 0o700);
  const snapshotRoute = path.join(temporaryRoot, "index.html");
  fs.writeFileSync(snapshotRoute, target.snapshots["index.html"].bytes, { flag: "wx", mode: 0o600 });
  const playwright = require("playwright");
  const runtimeVersion = require("playwright/package.json").version;
  if (runtimeVersion !== contract.dependencies.playwright_manifest.version) fail("Playwright runtime version drifted");
  const base = {
    schema_version: 1,
    authority: contract.authority,
    claim_boundary: contract.claim_boundary,
    identity: { variant: args.variant, case_id: args["case-id"], state: args.state },
    subject: {
      route: path.basename(target.route), route_sha256: target.routeSha256,
      manifest: "run-manifest.json", manifest_sha256: target.manifestSha256,
      spec: "hidden-spec", spec_sha256: specRecord.sha256,
    },
    probe: {
      id: contract.probe_id,
      script_sha256: scriptRecord.sha256,
      contract_sha256: contractRecord.sha256,
      helper_sha256: contract.dependencies.breakpoint_helper.sha256,
      playwright: runtimeVersion,
      engine: "chromium",
    },
    contract: {
      widths: contract.widths,
      height: contract.height,
      device_scale_factor: contract.device_scale_factor,
      max_samples: contract.max_samples,
      max_animations: contract.max_animations,
      screenshots: false,
      traces: false,
      videos: false,
    },
  };
  const verifyProvenance = () => {
    try {
      const currentContract = loadContract();
      const currentTarget = helper.validateTarget(args.route, args["target-manifest"]);
      if (currentContract.sha256 !== contractRecord.sha256
          || currentTarget.routeSha256 !== target.routeSha256
          || currentTarget.manifestSha256 !== target.manifestSha256
          || currentTarget.snapshots["DESIGN.md"].sha256 !== target.snapshots["DESIGN.md"].sha256
          || stableFile(specRecord.absolute, "hidden spec").sha256 !== specRecord.sha256
          || stableFile(__filename, "motion probe script", 2 * 1024 * 1024).sha256 !== scriptRecord.sha256
          || stableFile(snapshotRoute, "route snapshot", 8 * 1024 * 1024).sha256 !== target.routeSha256) {
        throw new Error("drift");
      }
    } catch {
      throw new Error("probe_provenance_drift");
    }
  };
  const writeReport = (report, exitCode = 0) => {
    validateMotionReport(report, contract);
    const serialized = `${JSON.stringify(report, null, 2)}\n`;
    if (Buffer.byteLength(serialized) > MAX_JSON_BYTES) fail("motion report exceeds its byte budget");
    fs.writeFileSync(output, serialized, { flag: "wx", mode: 0o600 });
    process.stdout.write(`${JSON.stringify({ status: report.status, output: path.basename(output) })}\n`);
    process.exitCode = exitCode;
  };
  let browser;
  let sampleCount = 0;
  try {
    try {
      verifyProvenance();
    } catch {
      writeReport(unavailable(base, "probe_provenance_drift"), 2);
      return;
    }
    try {
      browser = await playwright.chromium.launch({ headless: true });
    } catch {
      writeReport(unavailable(base, "probe_execution_unavailable"), 2);
      return;
    }
    base.probe.engine_version = browser.version();
    const sample = async (width, preference) => {
      if (sampleCount >= contract.max_samples) throw new Error("sample_budget_exhausted");
      verifyProvenance();
      sampleCount += 1;
      const context = await browser.newContext({
        viewport: { width, height: contract.height },
        screen: { width, height: contract.height },
        deviceScaleFactor: contract.device_scale_factor,
        hasTouch: false,
        isMobile: false,
        serviceWorkers: "block",
        locale: "zh-TW",
        timezoneId: "Asia/Taipei",
        reducedMotion: preference,
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
        await helper.applySteps(page, spec.steps);
        await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const assertions = await helper.assertionsPassed(page, spec.assertions);
        const layout = await page.evaluate(helper.browserModeSnapshot, {
          anchors,
          maxNodes: contract.max_nodes_per_selector,
          maxChildren: contract.max_children_per_node,
        });
        const motion = await page.evaluate(motionSnapshot, contract.max_animations);
        if (motion.budgetExceeded) throw new Error("animation_budget_exhausted");
        if (motion.reduceMediaMatches !== (preference === "reduce")) {
          throw new Error("motion_preference_unavailable");
        }
        if (externalRequests || runtimeErrors) throw new Error("runtime_or_external_event");
        return {
          preference,
          assertions_passed: assertions,
          horizontal_overflow: layout.horizontalOverflow,
          layout_signature: helper.modeHash({ ...layout, requiredAssertionsPassed: assertions }),
          motion,
        };
      } finally {
        await context.close().catch(() => {});
      }
    };
    const observations = [];
    const findings = [];
    const advisories = [];
    try {
      for (const width of contract.widths) {
        const normal = await sample(width, "no-preference");
        if (normal.motion.total === 0) {
          observations.push({ width, normal, reduce: null, replayed: false });
          continue;
        }
        const reduce = await sample(width, "reduce");
        const observation = { width, normal, reduce, replayed: false };
        observations.push(observation);
        const taskRegression = normal.assertions_passed && !reduce.assertions_passed;
        const overflowRegression = !normal.horizontal_overflow && reduce.horizontal_overflow;
        if (taskRegression || overflowRegression) {
          observation.replayed = true;
          const normalReplay = await sample(width, "no-preference");
          const reduceReplay = await sample(width, "reduce");
          for (const code of confirmedRegressionCodes(normal, reduce, normalReplay, reduceReplay)) {
            findings.push({ code, width, replays: 2 });
          }
        }
        if (canonical(normal.motion.categories) === canonical(reduce.motion.categories)
            && normal.motion.total === reduce.motion.total && normal.motion.active === reduce.motion.active
            && normal.motion.infinite === reduce.motion.infinite) {
          advisories.push({ code: "reduced_motion_no_categorical_change", width });
        }
      }
      verifyProvenance();
    } catch (error) {
      const reason = ["animation_budget_exhausted", "fonts_unavailable", "motion_preference_unavailable",
        "probe_provenance_drift", "runtime_or_external_event", "sample_budget_exhausted"].includes(error.message)
        ? error.message : "probe_execution_unavailable";
      writeReport(unavailable(base, reason, sampleCount), 2);
      return;
    }
    const hasObservedMotion = observations.some((item) => item.normal.motion.total > 0);
    writeReport({
      ...base,
      status: "complete",
      coverage: { status: "complete", reason_code: null, sample_count: sampleCount },
      motion: { status: hasObservedMotion ? "complete" : "not_applicable", observations },
      findings,
      advisories,
    });
  } finally {
    await browser?.close().catch(() => {});
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`v7 motion probe failed: ${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = {
  canonical, confirmedRegressionCodes, loadContract, motionSnapshot, stableFile, validateMotionReport,
};
