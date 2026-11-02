import { spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { chromium } from "/Users/woojin/.nvm/versions/node/v22.22.0/lib/node_modules/playwright/index.mjs";

const PROFILE = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const EVIDENCE = path.resolve(PROFILE, "../.litclaude/evidence/profile-readme");
const PORT = 8791;
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
themed-picture, markdown-accessiblity-table { display: block; }
.markdown-body img, .markdown-body picture, .markdown-body svg { max-width: 100%; height: auto; }
.markdown-body table { border-collapse: collapse; width: 100%; }
.markdown-body th, .markdown-body td { border: 1px solid #30363d; padding: 6px 13px; text-align: left; vertical-align: top; }
body.light .markdown-body th, body.light .markdown-body td { border-color: #d1d9e0; }
.markdown-body a { color: #4493f8; text-decoration: none; }
body.light .markdown-body a { color: #0969da; }
.markdown-body h2, .markdown-body h3 { border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
body.light .markdown-body h2, body.light .markdown-body h3 { border-bottom-color: #d1d9e0; }
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

function page(body, theme, { inlineHero = false } = {}) {
  let html = body;
  if (inlineHero) {
    const hero = fs.readFileSync(path.join(PROFILE, "assets", "hero.svg"), "utf8");
    html = html.replace(/<img\b[^>]*assets\/hero\.svg[^>]*>/i, hero);
  }
  return `<!doctype html><meta charset="utf-8"><title>preview</title><style>${CSS}</style><body class="${theme}"><article class="markdown-body">${html}</article></body>`;
}

function serve(darkHtml, lightHtml, reduceHtml) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    if (url === "/" || url === "/dark") {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(darkHtml);
      return;
    }
    if (url === "/light") {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(lightHtml);
      return;
    }
    if (url === "/reduce") {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(reduceHtml);
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
    reducedMotion: options.reducedMotion,
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto(options.url, { waitUntil: "networkidle" });
  if (options.wait) await page.waitForTimeout(options.wait);
  await page.screenshot({ path: file, fullPage: true });
  await context.close();
}

const body = markdownHtml();
const reduceHtml = page(body, "dark", { inlineHero: true });
const server = await serve(page(body, "dark"), page(body, "light"), reduceHtml);
const browser = await chromium.launch({ channel: "chrome" });
try {
  await shoot(browser, path.join(EVIDENCE, "task-10-dark.png"), {
    url: `${ORIGIN}/dark`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    wait: 4800,
  });
  await shoot(browser, path.join(EVIDENCE, "task-10-light.png"), {
    url: `${ORIGIN}/light`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "light",
    wait: 800,
  });
  await shoot(browser, path.join(EVIDENCE, "task-10-mobile.png"), {
    url: `${ORIGIN}/dark`,
    viewport: { width: 390, height: 800 },
    colorScheme: "dark",
    wait: 4800,
  });
  await shoot(browser, path.join(EVIDENCE, "task-10-rm.png"), {
    url: `${ORIGIN}/reduce`,
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
    reducedMotion: "reduce",
    wait: 200,
  });
  const videoContext = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    recordVideo: { dir: EVIDENCE, size: { width: 1280, height: 720 } },
  });
  const videoPage = await videoContext.newPage();
  await videoPage.goto(`${ORIGIN}/dark`, { waitUntil: "networkidle" });
  await videoPage.waitForTimeout(6000);
  const video = videoPage.video();
  await videoContext.close();
  const saved = await video.path();
  fs.renameSync(saved, path.join(EVIDENCE, "task-10-boot.webm"));
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
console.log("preview done");
