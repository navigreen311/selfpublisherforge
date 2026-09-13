#!/usr/bin/env node
/**
 * Fail on `t("...")` calls whose key does not resolve in the merged English
 * messages. next-intl renders the key path instead of throwing, so a renamed
 * or mistyped key ships silently and the UI shows "reviews.books.emptyState"
 * to the user. This caught 67 of them at once.
 *
 * Run: npm run check:i18n
 */
const fs = require("fs");
const path = require("path");

const cfg = fs.readFileSync("src/i18n/config.ts", "utf8");
const start = cfg.indexOf("supportedNamespaces = [");
const namespaces = cfg.slice(start, cfg.indexOf("] as const", start)).match(/"[a-z-]+"/g).map((s) => s.replace(/"/g, ""));

function deepMerge(a, b) {
  const out = { ...a };
  for (const k of Object.keys(b)) {
    out[k] = b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) && out[k] && typeof out[k] === "object"
      ? deepMerge(out[k], b[k]) : b[k];
  }
  return out;
}

let messages = JSON.parse(fs.readFileSync("src/messages/en.json", "utf8"));
for (const ns of namespaces) {
  const f = path.join("src/messages/en", ns + ".json");
  if (fs.existsSync(f)) messages = deepMerge(messages, { [ns]: JSON.parse(fs.readFileSync(f, "utf8")) });
}

const lookup = (key) => key.split(".").reduce((n, p) => (n == null ? undefined : n[p]), messages);

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (e.name !== "__tests__") walk(p, out); }
    else if (/[.]tsx?$/.test(p) && !/[.]test[.]/.test(p) && !p.endsWith("use-translations.ts")) out.push(p);
  }
  return out;
}

let bad = 0;
for (const file of walk("src", [])) {
  const src = fs.readFileSync(file, "utf8");
  const scopes = {};
  for (const m of src.matchAll(/const[ ]+([A-Za-z0-9_]+)[ ]*=[ ]*use[A-Za-z]*Translations[(][ ]*["]([^"]*)["][ ]*[)]/g)) scopes[m[1]] = m[2];
  for (const m of src.matchAll(/const[ ]+([A-Za-z0-9_]+)[ ]*=[ ]*useCommonTranslations[(][)]/g)) scopes[m[1]] = "common";
  if (!Object.keys(scopes).length) continue;
  for (const name of Object.keys(scopes)) {
    const ns = scopes[name];
    const re = new RegExp('(^|[^A-Za-z0-9_.])' + name + '[(][ ]*["]([^"]+)["]', "g");
    for (const m of src.matchAll(re)) {
      const full = ns ? ns + "." + m[2] : m[2];
      if (typeof lookup(full) !== "string") { console.log(file + "  " + name + '("' + m[2] + '")  ->  ' + full); bad++; }
    }
  }
}
console.log("");
console.log(bad + " unresolved translation keys");
if (bad > 0) process.exit(1);
