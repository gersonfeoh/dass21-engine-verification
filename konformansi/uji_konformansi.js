#!/usr/bin/env node
/*
 * Conformance harness for the DASS-21 screening engine.
 *
 * Runs the unmodified functions apiSubmitDass() and _bolehChat() from the
 * platform's Google Apps Script source (Code.gs) against the 35-vector oracle
 * (vektor_uji_bva_kisi_putar.csv). The platform source is NOT distributed in
 * this repository; pass its path on the command line.
 *
 * Every Apps Script service (SpreadsheetApp, MailApp, PropertiesService, ...)
 * is replaced by an inert stub, and the I/O helpers (auth_, appendRow_,
 * readAll_, catatEvent_, kirimEmailPenanda_) are replaced by in-memory
 * versions, so no spreadsheet row, alert, or e-mail is ever produced.
 *
 * Usage:
 *   node konformansi/uji_konformansi.js <path/to/Code.gs> [path/to/oracle.csv]
 *   node konformansi/uji_konformansi.js <path/to/Code.gs> --sensitivity
 *
 * Exit code 0 when all cases pass, 1 otherwise.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');

const args = process.argv.slice(2);
if (!args.length) {
  console.error('Usage: node uji_konformansi.js <Code.gs> [oracle.csv] [--sensitivity]');
  process.exit(2);
}
const sumberPath = args[0];
const sensitivity = args.includes('--sensitivity');
const csvPath = args.find((a, i) => i > 0 && !a.startsWith('--')) ||
  path.join(__dirname, '..', 'vektor_uji_bva_kisi_putar.csv');

// Category labels: the oracle uses English labels, the platform uses Indonesian ones.
const LABEL = { 'Normal': 'Normal', 'Ringan': 'Mild', 'Sedang': 'Moderate',
                'Berat': 'Severe', 'Sangat Berat': 'Extremely Severe' };

// Universal inert stub: any property access or call returns another stub.
function stub() {
  const f = function () { return stub(); };
  return new Proxy(f, {
    get: (t, k) => (k === Symbol.toPrimitive ? () => '' : k === 'then' ? undefined : stub()),
    apply: () => stub(),
    construct: () => stub(),
  });
}

function loadEngine(source) {
  const store = {};                       // sheet name -> array of row objects
  const sandbox = {
    console, Math, Date, JSON, Number, String, Array, Object, isNaN, parseInt, parseFloat,
    SpreadsheetApp: stub(), MailApp: stub(), GmailApp: stub(), PropertiesService: stub(),
    CacheService: stub(), LockService: stub(), Utilities: stub(), Session: stub(),
    HtmlService: stub(), UrlFetchApp: stub(), ScriptApp: stub(), DriveApp: stub(),
    ContentService: stub(), Logger: { log: () => {} },
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: 'Code.gs' });
  // In-memory replacements for I/O helpers (defined after the source, so they win).
  vm.runInContext(`
    var __USER = { user_id: 'UJI-0001', nama: 'Uji Sintetik', status: 'aktif' };
    var __STORE = {};
    auth_ = function () { return __USER; };
    appendRow_ = function (sheet, row) { (__STORE[sheet] = __STORE[sheet] || []).push(row); };
    readAll_ = function (sheet) { return (__STORE[sheet] || []).slice(); };
    catatEvent_ = function () {};
    kirimEmailPenanda_ = function () {};
    __reset = function () { __STORE = {}; };
    __alerts = function () { return (__STORE[CFG.SHEET_ALERT] || []).length; };
  `, sandbox);
  return sandbox;
}

function readCsv(p) {
  const lines = fs.readFileSync(p, 'utf8').trim().split(/\r?\n/);
  const head = lines[0].split(',');
  return lines.slice(1).map(l => {
    const v = l.split(','); const o = {};
    head.forEach((h, i) => { o[h] = v[i]; });
    return o;
  });
}

function runOracle(engine, cases) {
  let pass = 0; const fails = []; const gateAndFlag = [];
  for (const c of cases) {
    engine.__reset();
    const jawaban = [];
    for (let i = 1; i <= 21; i++) jawaban.push(Number(c['b' + String(i).padStart(2, '0')]));
    const r = engine.apiSubmitDass('token-uji', jawaban, '');
    if (!r || !r.ok) { fails.push([c.kasus, 'apiSubmitDass error: ' + (r && r.msg)]); continue; }
    const gate = engine._bolehChat(engine.__USER).boleh;
    const got = {
      skor: [r.skor.D, r.skor.A, r.skor.S].join('/'),
      D: LABEL[r.kat.D], A: LABEL[r.kat.A], S: LABEL[r.kat.S],
      gerbang: gate ? 'terbuka' : 'tertutup',
      penanda: r.flag === 'PERLU_PERHATIAN' ? 'ya' : 'tidak',
    };
    const exp = {
      skor: [c.skor_D, c.skor_A, c.skor_S].join('/'),
      D: c.harapan_D, A: c.harapan_A, S: c.harapan_S,
      gerbang: c.harapan_gerbang, penanda: c.harapan_penanda,
    };
    const diff = Object.keys(exp).filter(k => String(got[k]) !== String(exp[k]));
    if (diff.length) fails.push([c.kasus, diff.map(k => `${k}: expected ${exp[k]}, got ${got[k]}`).join('; ')]);
    else pass++;
    if (got.gerbang === 'terbuka' && got.penanda === 'ya') gateAndFlag.push(c.kasus);
  }
  return { pass, fails, gateAndFlag };
}

const source = fs.readFileSync(sumberPath, 'utf8');
const cases = readCsv(csvPath);
const sha = crypto.createHash('sha256').update(source).digest('hex');
console.log(`Source: ${path.basename(sumberPath)}  sha256=${sha}`);
console.log(`Oracle: ${path.basename(csvPath)}  (${cases.length} cases)`);

const res = runOracle(loadEngine(source), cases);
console.log(`Result: ${res.pass}/${cases.length} passed`);
res.fails.forEach(f => console.log(`  FAIL ${f[0]}: ${f[1]}`));
console.log(`Cases that open the gate AND raise the flag: ${res.gateAndFlag.join(', ') || 'none'}`);

let ok = res.fails.length === 0;
if (sensitivity) {
  // Two seeded faults; each must make exactly one case fail.
  const seeds = [
    ['Depression Normal upper bound 9 -> 7', s => s.replace("D: [ {max:9,label:'Normal'}", "D: [ {max:7,label:'Normal'}")],
    ['Item 21 check removed', s => s.replace('|| (Number(jawaban[20]) >= 3)', '')],
  ];
  for (const [name, mutate] of seeds) {
    const m = mutate(source);
    if (m === source) { console.log(`Sensitivity [${name}]: pattern not found, skipped`); ok = false; continue; }
    const r = runOracle(loadEngine(m), cases);
    console.log(`Sensitivity [${name}]: ${r.fails.length} case(s) fail -> ${r.fails.map(f => f[0]).join(', ')}`);
    if (r.fails.length !== 1) ok = false;
  }
}
process.exit(ok ? 0 : 1);
