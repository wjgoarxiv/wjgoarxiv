import { spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { chromium } from "/Users/woojin/.nvm/versions/node/v22.22.0/lib/node_modules/playwright/index.mjs";

const PROFILE = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const EVIDENCE = path.resolve(PROFILE, "../.litclaude/evidence/profile-readme-v2");
const PORT = 8797;
const ORIGIN = `http://127.0.0.1:${PORT}`;

const CSS = `
html, body { margin: 0; }
body.dark { background: #0d1117; color: #e6edf3; }
body.light { background: #ffffff; color: #1f2328; }
.markdown-body {
  box-sizing: border-box;
  width: min(838px, 100%);
  margin: 24px auto;
  padding: 0 16px 48px;
  font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
themed-picture, .markdown-body picture { display: contents; }
markdown-accessiblity-table { display: block; }
.markdown-body img, .markdown-body svg { max-width: 100%; height: auto; }
.markdown-body img[width="32%"] { width: 32%; }
.markdown-body img[width="49%"] { width: 49%; }
.markdown-body img[width="100%"] { width: 100%; }
.markdown-body svg.lab-inline { width: 49%; height: auto; }
.markdown-body table { border-collapse: collapse; width: 100%; }
.markdown-body th, .markdown-body td { border: 1px solid #30363d; padding: 6px 13px; text-align: left; vertical-align: top; }
body.light .markdown-body th, body.light .markdown-body td { border-color: #d1d9e0; }
.markdown-body a { color: #4493f8; text-decoration: none; }
body.light .markdown-body a { color: #0969da; }
.markdown-body h2, .markdown-body h3 { border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
body.light .markdown-body h2, body.light .markdown-body h3 { border-bottom-color: #d1d9e0; }
.markdown-body details { margin: 12px 0; }
.markdown-body summary { cursor: pointer; }
`;

function markdownHtml() {
  const rendered = spawnSync(
    "gh",
    ["api", "markdown", "-f", "mode=gfm", "-F", `text=@${path.join(PROFILE, "README.md")}`],
    { encoding: "utf8" },
  );
  if (rendered.status !== 0) {
    throw new Error(rendered.stderr || "gh api markdown failed");
  }
  return rendered.stdout;
}

function page(body, theme) {
  return `<!doctype html><meta charset="utf-8"><title>preview</title><style>${CSS}</style><body class="${theme}"><article class="markdown-body">${body}</article></body>`;
}

function withInline(body, file, pattern, className) {
  let svg = fs.readFileSync(path.join(PROFILE, "assets", file), "utf8");
  svg = svg.replace("<svg ", `<svg class="${className}" `);
  if (!body.match(pattern)) throw new Error(`missing picture for ${file}`);
  return body.replace(pattern, svg);
}

function serve(routes) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    if (routes[url]) {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(routes[url]);
      return;
    }
    const file = path.join(PROFILE, url);
    if (!file.startsWith(PROFILE) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404);
      res.end("missing");
      return;
    }
    const type = file.endsWith(".svg") ? "image/svg+xml" : "application/octet-stream";
    res.writeHead(200, { "Content-Type": type });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(PORT, "127.0.0.1", () => resolve(server)));
}

async function shoot(browser, file, options) {
  const context = await browser.newContext({
    viewport: options.viewport,
    colorScheme: options.colorScheme,
    reducedMotion: options.reducedMotion || "no-preference",
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto(options.url, { waitUntil: "networkidle" });
  if (options.open) {
    await page.evaluate(() => {
      for (const block of document.querySelectorAll("details")) block.open = true;
    });
  }
  if (options.wait) await page.waitForTimeout(options.wait);
  if (options.clip) {
    await page.screenshot({ path: file, clip: options.clip });
  } else {
    await page.screenshot({ path: file, fullPage: true });
  }
  const height = options.measure
    ? await page.locator("article.markdown-body").evaluate((el) => Math.round(el.getBoundingClientRect().height))
    : null;
  await context.close();
  return height;
}

function pixelDiff(left, right) {
  const metric = spawnSync("magick", ["compare", "-metric", "AE", left, right, "null:"], { encoding: "utf8" });
  const raw = `${metric.stderr || ""}\n${metric.stdout || ""}`.trim().split(/\s+/)[0];
  const changed = Number(raw);
  const id = spawnSync("magick", ["identify", "-format", "%w %h", left], { encoding: "utf8" });
  const [w, h] = id.stdout.trim().split(/\s+/).map(Number);
  if (!w || !h || Number.isNaN(changed)) throw new Error(`pixel diff failed: ${raw}`);
  return changed / (w * h);
}

function treeBytes(dir) {
  let total = 0;
  const rows = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const nested = treeBytes(full);
      total += nested.total;
      rows.push(...nested.rows);
    } else if (entry.name.endsWith(".svg")) {
      const size = fs.statSync(full).size;
      total += size;
      rows.push([size, path.relative(PROFILE, full)]);
    } else {
      total += fs.statSync(full).size;
    }
  }
  return { total, rows };
}

fs.mkdirSync(EVIDENCE, { recursive: true });
const body = markdownHtml();
const labPattern = /<picture>[\s\S]*?assets\/lab-night\.svg[\s\S]*?<\/picture>/i;
const heroPattern = /<picture>[\s\S]*?assets\/hero-night\.svg[\s\S]*?<\/picture>/i;
const cageBody = withInline(body, "lab-night.svg", labPattern, "lab-inline");
const reduceBody = withInline(body, "hero-night.svg", heroPattern, "hero-inline");
const server = await serve({
  "/": page(body, "dark"),
  "/dark": page(body, "dark"),
  "/light": page(body, "light"),
  "/reduce": page(reduceBody, "dark"),
  "/cage": page(cageBody, "dark"),
});
const browser = await chromium.launch({ channel: "chrome" });
let height = 0;
let diff = 0;
try {
  height = await shoot(browser, path.join(EVIDENCE, "dark.png"), {
    url: `${ORIGIN}/dark`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    wait: 2800,
    measure: true,
  });
  await shoot(browser, path.join(EVIDENCE, "light.png"), {
    url: `${ORIGIN}/light`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "light",
    wait: 2800,
  });
  await shoot(browser, path.join(EVIDENCE, "mobile.png"), {
    url: `${ORIGIN}/dark`,
    viewport: { width: 390, height: 800 },
    colorScheme: "dark",
    wait: 2800,
  });
  await shoot(browser, path.join(EVIDENCE, "rm.png"), {
    url: `${ORIGIN}/reduce`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    reducedMotion: "reduce",
    wait: 200,
  });
  const cageContext = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
  });
  const cagePage = await cageContext.newPage();
  await cagePage.goto(`${ORIGIN}/cage`, { waitUntil: "networkidle" });
  const cage = cagePage.locator("svg.lab-inline");
  async function cageClip(seconds) {
    await cagePage.evaluate((time) => {
      document.querySelector("svg.lab-inline").setCurrentTime(time);
    }, seconds);
    const box = await cage.boundingBox();
    return {
      x: box.x + box.width * 0.46,
      y: box.y + box.height * 0.08,
      width: box.width * 0.5,
      height: box.height * 0.62,
    };
  }
  await cagePage.screenshot({ path: path.join(EVIDENCE, "cage-a.png"), clip: await cageClip(1) });
  await cagePage.screenshot({ path: path.join(EVIDENCE, "cage-b.png"), clip: await cageClip(2.5) });
  await cageContext.close();
  diff = pixelDiff(path.join(EVIDENCE, "cage-a.png"), path.join(EVIDENCE, "cage-b.png"));
  await shoot(browser, path.join(EVIDENCE, "open.png"), {
    url: `${ORIGIN}/dark`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    open: true,
    wait: 2800,
  });
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
const listen = spawnSync("lsof", ["-nP", `-iTCP:${PORT}`, "-sTCP:LISTEN"], { encoding: "utf8" });
const { total, rows } = treeBytes(path.join(PROFILE, "assets"));
rows.sort((a, b) => b[0] - a[0]);
const lines = [
  "# Preview",
  "",
  `collapsed height: ${height}`,
  `cage pixel diff: ${diff.toFixed(4)}`,
  `assets bytes: ${total}`,
  `listen: ${(listen.stdout || "").trim() || "empty"}`,
  "",
  "Largest SVGs:",
  ...rows.slice(0, 8).map(([size, name]) => `- ${size} ${name}`),
  "",
];
fs.writeFileSync(path.join(EVIDENCE, "report.md"), lines.join("\n"));
console.log(lines.join("\n"));
if (height >= 1200) process.exitCode = 1;
if (diff <= 0.01) process.exitCode = 1;
if ((listen.stdout || "").trim()) process.exitCode = 1;
