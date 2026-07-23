#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runLocalPageMatrix } = require("./playwright_browser_runtime.cjs");

const MAX_JSON_BYTES = 2_000_000;
const MAX_CAPTURE_BYTES = 8_000_000;
const MAX_TOTAL_CAPTURE_BYTES = 64_000_000;
const HASH = /^[a-f0-9]{64}$/;
const ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const DRAFT_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const PROFILE_STANDARD = [
  { name: "desktop-default", viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference", dpr: 1 },
  { name: "mobile-default", viewport: { width: 390, height: 844 }, reducedMotion: "reduce", dpr: 1 },
];

function fail(message) {
  process.stderr.write(`visual evidence capture failed: ${message}\n`);
  process.exitCode = 1;
}

function exactKeys(value, keys, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)
    || JSON.stringify(Object.keys(value).sort()) !== JSON.stringify([...keys].sort())) {
    throw new Error(`${label} has an invalid shape`);
  }
  return value;
}

function readJson(file, label) {
  const info = fs.lstatSync(file);
  if (!info.isFile() || info.isSymbolicLink() || info.size > MAX_JSON_BYTES) {
    throw new Error(`${label} must be a bounded regular file`);
  }
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function readUnaliasedJson(file, label) {
  if (!path.isAbsolute(file) || fs.realpathSync(file) !== file) {
    throw new Error(`${label} must be an absolute unaliased file`);
  }
  const info = fs.lstatSync(file);
  if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1 || info.size > MAX_JSON_BYTES) {
    throw new Error(`${label} must be a bounded unaliased file`);
  }
  return readJson(file, label);
}

function secureExclusiveJson(file, value) {
  const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL
    | (fs.constants.O_NOFOLLOW || 0);
  const encoded = Buffer.from(`${JSON.stringify(value, null, 2)}\n`, "utf8");
  const descriptor = fs.openSync(file, flags, 0o600);
  try {
    fs.writeFileSync(descriptor, encoded);
    fs.fsyncSync(descriptor);
    const info = fs.fstatSync(descriptor);
    if (!info.isFile() || info.nlink !== 1 || (info.mode & 0o777) !== 0o600) {
      throw new Error("private convergence evidence identity is invalid");
    }
  } finally {
    fs.closeSync(descriptor);
  }
  return { bytes: encoded.length, sha256: sha256Bytes(encoded) };
}

function sha256Bytes(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function sha256File(file) {
  return sha256Bytes(fs.readFileSync(file));
}

function safeRelative(value, label) {
  if (typeof value !== "string" || !value || value.includes("\\") || value.includes("\0")
    || path.posix.isAbsolute(value) || path.posix.normalize(value) !== value
    || value === ".." || value.startsWith("../")) {
    throw new Error(`${label} must be a normalized relative path`);
  }
  return value;
}

function validateCase(data) {
  exactKeys(data, ["schema_version", "case_id", "run_id", "partition", "brief", "capture_plan", "craft"], "case");
  if (data.schema_version !== 1 || typeof data.case_id !== "string" || !ID.test(data.run_id)) {
    throw new Error("case identity is invalid");
  }
  if (!new Set(["validation", "test"]).has(data.partition)) {
    throw new Error("case partition must be validation or test");
  }
  const brief = exactKeys(data.brief, ["bytes", "sha256"], "case.brief");
  if (!Number.isSafeInteger(brief.bytes) || brief.bytes < 1 || !HASH.test(brief.sha256)) {
    throw new Error("case brief provenance is invalid");
  }
  const plan = exactKeys(data.capture_plan, ["locale", "state", "pages", "wait_condition", "profiles"], "case.capture_plan");
  if (!new Set(["zh-Hant", "en"]).has(plan.locale) || plan.state !== "default"
    || plan.pages !== "all_html_outputs"
    || plan.wait_condition !== "load+fonts+two-raf+300ms+two-raf") {
    throw new Error("case capture plan is not the current standard");
  }
  if (!Array.isArray(plan.profiles) || plan.profiles.length !== PROFILE_STANDARD.length
    || plan.profiles.some((profile, index) => {
      const expected = PROFILE_STANDARD[index];
      return !profile || typeof profile !== "object" || Array.isArray(profile)
        || JSON.stringify(Object.keys(profile).sort()) !== JSON.stringify(["dpr", "name", "reducedMotion", "viewport"])
        || profile.name !== expected.name || profile.reducedMotion !== expected.reducedMotion || profile.dpr !== expected.dpr
        || !profile.viewport || profile.viewport.width !== expected.viewport.width || profile.viewport.height !== expected.viewport.height;
    })) {
    throw new Error("case capture profiles are not the current standard");
  }
  if (!data.craft || typeof data.craft !== "object" || Array.isArray(data.craft)) {
    throw new Error("case craft policy must be an evaluator-owned object");
  }
}

function validateManifest(target, manifest) {
  if (!manifest || manifest.schema_version !== 2 || manifest.status !== "completed"
    || !manifest.brief || !manifest.skill_snapshot || !Array.isArray(manifest.outputs)) {
    throw new Error("run manifest is not a completed current build");
  }
  if (!Number.isSafeInteger(manifest.brief.bytes) || !HASH.test(manifest.brief.sha256)
    || !HASH.test(manifest.skill_snapshot.tree_sha256)) {
    throw new Error("run manifest provenance is invalid");
  }
  const names = new Set();
  const outputs = manifest.outputs.map((record, index) => {
    exactKeys(record, ["path", "bytes", "mode", "sha256"], `manifest.outputs[${index}]`);
    const name = safeRelative(record.path, `manifest.outputs[${index}].path`);
    if (names.has(name) || !Number.isSafeInteger(record.bytes) || record.bytes < 0 || !HASH.test(record.sha256)) {
      throw new Error("run manifest output provenance is invalid");
    }
    names.add(name);
    const file = path.join(target, name);
    const info = fs.lstatSync(file);
    if (!info.isFile() || info.isSymbolicLink() || info.size !== record.bytes
      || info.mode.toString(8).slice(-4) !== record.mode || sha256File(file) !== record.sha256) {
      throw new Error(`run output drifted: ${name}`);
    }
    return record;
  });
  const pages = outputs.map((record) => record.path).filter((name) => name.toLowerCase().endsWith(".html"));
  if (pages.length < 1 || pages.length > 8) throw new Error("current build must contain 1-8 HTML outputs");
  return { outputs, pages };
}

function validateDraftConvergence(value, pages) {
  exactKeys(value, ["schema_version", "cohort_id", "surface", "variants"], "draft convergence");
  if (value.schema_version !== 1 || typeof value.cohort_id !== "string" || !DRAFT_ID.test(value.cohort_id)
    || typeof value.surface !== "string" || !DRAFT_ID.test(value.surface)
    || !Array.isArray(value.variants) || value.variants.length < 2 || value.variants.length > 3) {
    throw new Error("draft convergence contract is invalid");
  }
  const ids = new Set();
  const configuredPages = new Set();
  for (const [index, variant] of value.variants.entries()) {
    exactKeys(variant, ["id", "page"], `draft convergence.variants[${index}]`);
    const page = safeRelative(variant.page, `draft convergence.variants[${index}].page`);
    if (typeof variant.id !== "string" || !DRAFT_ID.test(variant.id)
      || ids.has(variant.id) || configuredPages.has(page)) {
      throw new Error("draft convergence variants are invalid");
    }
    ids.add(variant.id);
    configuredPages.add(page);
  }
  if (configuredPages.size !== pages.length || pages.some((page) => !configuredPages.has(page))) {
    throw new Error("draft convergence pages do not match current HTML outputs");
  }
  return value;
}

function pngDimensions(file) {
  const data = fs.readFileSync(file);
  if (data.length < 24 || data.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a"
    || data.subarray(12, 16).toString("ascii") !== "IHDR") {
    throw new Error("capture is not a PNG");
  }
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) };
}

function slug(value) {
  return value.replace(/\.html$/i, "").replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "") || "page";
}

function snapshotOutputs(source, destination, outputs) {
  fs.mkdirSync(destination, { mode: 0o700 });
  for (const record of outputs) {
    const sourceFile = path.join(source, record.path);
    const destinationFile = path.join(destination, record.path);
    fs.mkdirSync(path.dirname(destinationFile), { recursive: true, mode: 0o700 });
    fs.copyFileSync(sourceFile, destinationFile, fs.constants.COPYFILE_EXCL);
    fs.chmodSync(destinationFile, Number.parseInt(record.mode, 8));
  }
  const copied = validateManifest(destination, {
    schema_version: 2,
    status: "completed",
    brief: { bytes: 1, sha256: "0".repeat(64) },
    skill_snapshot: { tree_sha256: "0".repeat(64) },
    outputs,
  });
  if (JSON.stringify(copied.outputs) !== JSON.stringify(outputs)) {
    throw new Error("evaluator source snapshot does not match current outputs");
  }
}

async function main() {
  if (![5, 6].includes(process.argv.length)) {
    throw new Error("expected target, evaluator case, fresh evidence directory and optional draft convergence contract");
  }
  const targetArg = process.argv[2];
  const caseArg = process.argv[3];
  const evidenceArg = process.argv[4];
  const convergenceArg = process.argv[5] || null;
  if (![targetArg, caseArg, evidenceArg, ...(convergenceArg ? [convergenceArg] : [])].every(path.isAbsolute)) {
    throw new Error("all paths must be absolute");
  }

  const target = fs.realpathSync(targetArg);
  const caseArgInfo = fs.lstatSync(caseArg);
  if (!caseArgInfo.isFile() || caseArgInfo.isSymbolicLink() || caseArgInfo.size > MAX_JSON_BYTES) {
    throw new Error("case must be a bounded regular non-symlink file");
  }
  const caseFile = fs.realpathSync(caseArg);
  if (fs.existsSync(evidenceArg)) throw new Error("evidence directory must not already exist");
  const parent = fs.realpathSync(path.dirname(evidenceArg));
  const evidence = path.join(parent, path.basename(evidenceArg));
  if (target === evidence || target.startsWith(`${evidence}${path.sep}`) || evidence.startsWith(`${target}${path.sep}`)) {
    throw new Error("evidence directory and current build must be separate");
  }

  const caseData = readJson(caseFile, "case");
  const caseBytes = fs.readFileSync(caseFile);
  validateCase(caseData);
  const manifestFile = path.join(target, "run-manifest.json");
  const manifest = readJson(manifestFile, "run manifest");
  const manifestBytes = fs.readFileSync(manifestFile);
  const before = validateManifest(target, manifest);
  const convergence = convergenceArg
    ? validateDraftConvergence(readUnaliasedJson(convergenceArg, "draft convergence contract"), before.pages)
    : null;
  const convergenceTools = convergence
    ? require("../wow-frontend-design/scripts/cross_output_template_audit.cjs")
    : null;
  if (JSON.stringify(caseData.brief) !== JSON.stringify(manifest.brief)) {
    throw new Error("case brief does not match the current build");
  }

  const artifacts = path.join(evidence, "artifacts");
  const sourceSnapshot = path.join(evidence, ".source-snapshot");
  const captures = [];
  const macroObservations = [];
  let ordinal = 0;
  try {
    fs.mkdirSync(evidence, { mode: 0o700 });
    fs.mkdirSync(artifacts, { mode: 0o700 });
    snapshotOutputs(target, sourceSnapshot, before.outputs);
    const profiles = PROFILE_STANDARD.map((profile) => ({ ...profile, locale: caseData.capture_plan.locale }));
    const { browserVersion, results } = await runLocalPageMatrix({
      stage: sourceSnapshot,
      pages: before.pages,
      allowedFiles: before.outputs.map((record) => record.path),
      profiles,
      inspectPage: async (page, meta) => {
        ordinal += 1;
        const name = `${String(ordinal).padStart(2, "0")}-${slug(meta.relativePage)}-${meta.profile.name}.png`;
        const relative = `artifacts/${name}`;
        const destination = path.join(evidence, relative);
        await page.screenshot({ path: destination, type: "png", fullPage: false, animations: "disabled", caret: "hide", scale: "device" });
        const info = fs.lstatSync(destination);
        const dimensions = pngDimensions(destination);
        if (!info.isFile() || info.isSymbolicLink() || info.size > MAX_CAPTURE_BYTES
          || dimensions.width !== meta.profile.viewport.width * meta.profile.dpr
          || dimensions.height !== meta.profile.viewport.height * meta.profile.dpr) {
          throw new Error(`capture violates size or viewport contract: ${relative}`);
        }
        const label = `${String(ordinal).padStart(2, "0")}-${slug(meta.relativePage)}-${meta.profile.name}`;
        captures.push({
          label,
          page: meta.relativePage,
          profile: meta.profile.name,
          path: relative,
          bytes: info.size,
          sha256: sha256File(destination),
          width: dimensions.width,
          height: dimensions.height,
          captured_at: new Date().toISOString(),
          context: {
            route: `/${meta.relativePage}`,
            state: caseData.capture_plan.state,
            locale: caseData.capture_plan.locale,
            viewport: `${meta.profile.viewport.width}x${meta.profile.viewport.height}`,
            dpr: meta.profile.dpr,
            reduced_motion: meta.profile.reducedMotion,
            wait_condition: caseData.capture_plan.wait_condition,
          },
        });
        if (convergence) {
          const variant = convergence.variants.find((item) => item.page === meta.relativePage);
          macroObservations.push({
            caseId: variant.id,
            route: `/${meta.relativePage}`,
            surface: convergence.surface,
            viewport: meta.profile.name,
            state: caseData.capture_plan.state,
            macroFingerprint: await page.evaluate(convergenceTools.collectMacroFingerprint),
          });
        }
        return { capture: relative };
      },
    });
    if (captures.length !== before.pages.length * PROFILE_STANDARD.length
      || captures.reduce((sum, item) => sum + item.bytes, 0) > MAX_TOTAL_CAPTURE_BYTES
      || results.some((result) => result.navigation !== "passed" || !result.visible_main
        || !result.visible_text || !result.visible_primary_content || result.root_horizontal_overflow
        || Object.values(result.counters).some((count) => count !== 0))) {
      throw new Error("fresh browser replay did not remain clean");
    }
    const afterManifest = fs.readFileSync(manifestFile);
    const after = validateManifest(target, readJson(manifestFile, "run manifest"));
    if (!afterManifest.equals(manifestBytes) || JSON.stringify(after.outputs) !== JSON.stringify(before.outputs)) {
      throw new Error("current build drifted during capture");
    }
    if (convergence) {
      if (macroObservations.length !== convergence.variants.length * PROFILE_STANDARD.length) {
        throw new Error("draft convergence matrix is incomplete");
      }
      const observationInput = {
        schemaVersion: 1,
        cohort: convergence.cohort_id,
        observations: macroObservations,
      };
      const audit = convergenceTools.auditCrossOutputTemplates(observationInput);
      const observationRecord = secureExclusiveJson(
        path.join(evidence, "macro-observations.json"), observationInput,
      );
      secureExclusiveJson(path.join(evidence, "cross-output-template-audit.json"), {
        schema_version: 1,
        observations: observationRecord,
        result: audit,
      });
    }
    fs.rmSync(sourceSnapshot, { recursive: true });
    const receipt = {
      schema_version: 1,
      status: "captured",
      case: {
        case_id: caseData.case_id,
        run_id: caseData.run_id,
        partition: caseData.partition,
        case_sha256: sha256Bytes(caseBytes),
      },
      source: {
        run_manifest_sha256: sha256Bytes(manifestBytes),
        brief: manifest.brief,
        skill_tree_sha256: manifest.skill_snapshot.tree_sha256,
        outputs: before.outputs,
      },
      runtime: {
        package: "playwright",
        version: require("playwright/package.json").version,
        browser: "chromium",
        browser_version: browserVersion,
        headless: true,
      },
      capture_standard: {
        profiles: PROFILE_STANDARD,
        screenshot_mode: "viewport",
        animations: "disabled",
        caret: "hide",
        network: "local-output-only",
      },
      captures,
    };
    fs.writeFileSync(path.join(evidence, "capture-receipt.json"), `${JSON.stringify(receipt, null, 2)}\n`, { encoding: "utf8", flag: "wx", mode: 0o600 });
    process.stdout.write(`${JSON.stringify(receipt)}\n`);
  } catch (error) {
    fs.rmSync(evidence, { recursive: true, force: true });
    throw error;
  }
}

main().catch((error) => fail(error && error.message ? error.message : "unknown"));
