/**
 * Manual mock for `next-intl` (auto-applied: this directory is adjacent to
 * node_modules, so jest substitutes it for every `next-intl` import).
 *
 * Components reach translations through `@/hooks/use-translations`, which is a
 * thin wrapper over `useTranslations`. Real next-intl throws unless a
 * `NextIntlClientProvider` is somewhere above the component, and no test wraps
 * one — so every suite rendering a translated component died at first render.
 *
 * This mock resolves keys against the *real* English message files using the
 * same main-file + namespace-file merge as `src/i18n/request.ts`, so tests
 * assert on the strings users actually see rather than on key paths.
 */

const fs = require("fs");
const path = require("path");
const React = require("react");

const { defaultLocale, supportedNamespaces, deepMerge } = require("../src/i18n/config");

const MESSAGES_DIR = path.join(__dirname, "..", "src", "messages");

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function loadMessages(locale) {
  let messages = readJson(path.join(MESSAGES_DIR, `${locale}.json`));
  for (const namespace of supportedNamespaces) {
    const file = path.join(MESSAGES_DIR, locale, `${namespace}.json`);
    if (!fs.existsSync(file)) continue;
    messages = deepMerge(messages, { [namespace]: readJson(file) });
  }
  return messages;
}

let cachedMessages = null;
function messages() {
  if (cachedMessages === null) cachedMessages = loadMessages(defaultLocale);
  return cachedMessages;
}

function lookup(keyPath) {
  return keyPath
    .split(".")
    .reduce((node, part) => (node == null ? undefined : node[part]), messages());
}

/** Minimal ICU: `{name}` substitution only. No plural/select forms are used. */
function interpolate(template, values) {
  if (!values) return template;
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    Object.prototype.hasOwnProperty.call(values, name) ? String(values[name]) : match
  );
}

function makeTranslator(namespace) {
  const prefix = namespace ? `${namespace}.` : "";

  // Real next-intl renders the full key path when a message is missing rather
  // than throwing, so a missing key shows up as a readable assertion failure.
  const t = (key, values) => {
    const message = lookup(prefix + key);
    return typeof message === "string" ? interpolate(message, values) : prefix + key;
  };

  t.rich = (key, values) => t(key, values);
  t.markup = (key, values) => t(key, values);
  t.raw = (key) => {
    const message = lookup(prefix + key);
    return message === undefined ? prefix + key : message;
  };
  t.has = (key) => lookup(prefix + key) !== undefined;

  return t;
}

const useTranslations = (namespace) => makeTranslator(namespace);
const getTranslations = async (namespace) => makeTranslator(namespace);
const useLocale = () => defaultLocale;
const useMessages = () => messages();
const useNow = () => new Date();
const useTimeZone = () => "UTC";

const useFormatter = () => ({
  dateTime: (value) => new Date(value).toISOString(),
  number: (value) => String(value),
  list: (value) => Array.from(value).join(", "),
  relativeTime: (value) => new Date(value).toISOString(),
});

function NextIntlClientProvider({ children }) {
  return React.createElement(React.Fragment, null, children);
}

module.exports = {
  NextIntlClientProvider,
  useTranslations,
  getTranslations,
  useLocale,
  useMessages,
  useNow,
  useTimeZone,
  useFormatter,
};
