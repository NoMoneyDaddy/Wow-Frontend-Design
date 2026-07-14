#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const reportPath = path.join(root, "evals", "product-flow-v3-visual-results.json");
const allowedRoot = path.join(root, "assets", "product-flow-v3") + path.sep;

const reportStat = fs.lstatSync(reportPath);
if (!reportStat.isFile() || reportStat.isSymbolicLink()) throw new Error("visual report must be a real file");
const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
if (!Array.isArray(report.results) || report.results.length !== 60) throw new Error("expected exactly 60 visual results");

for (const result of report.results) {
  if (Object.hasOwn(result, "screenshotSha256")) throw new Error("report is already finalized");
  const absolute = path.resolve(root, result.screenshot || "");
  if (!absolute.startsWith(allowedRoot)) throw new Error(`unsafe screenshot path: ${result.screenshot}`);
  const stat = fs.lstatSync(absolute);
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`unsafe screenshot file: ${result.screenshot}`);
  result.screenshotSha256 = crypto.createHash("sha256").update(fs.readFileSync(absolute)).digest("hex");
}

const temporary = `${reportPath}.tmp-${process.pid}`;
fs.writeFileSync(temporary, `${JSON.stringify(report, null, 2)}\n`, { encoding: "utf8", flag: "wx", mode: 0o644 });
fs.renameSync(temporary, reportPath);
