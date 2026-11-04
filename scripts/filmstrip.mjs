import { spawnSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { chromium } from "/Users/woojin/.nvm/versions/node/v22.22.0/lib/node_modules/playwright/index.mjs";

const PROFILE = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const EVIDENCE = path.resolve(PROFILE, "../.litclaude/evidence/profile-readme-v3");
const PORT = 8799;
const TIMES = [0.1, 0.4, 0.8, 1.4, 2.2, 3.5, 8];

const CSS = `
html, body { margin: 0; }
body.dark { background: #0d1117; color: #e6edf3; }
.markdown-body {
  box-sizing: border-box;
  width: min(846px, 100%);
  margin: 24px auto;
  padding: 0 0 48px;
  font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
.markdown-body p { margin-top: 0; margin-bottom: 16px; }
.markdown-body img, .markdown-body svg { max-width: 100%; height: auto; }
.markdown-body img[width="50%"], .markdown-body svg.pane { width: 50%; }
.markdown-body img[width="100%"], .markdown-body svg.full { width: 100%; }
.markdown-body a { color: #4493f8; text-decoration: none; }
.markdown-body details { margin: 12px 0; }
.markdown-body summary { cursor: pointer; }
.row { display: flex; flex-wrap: nowrap; gap: 0; justify-content: flex-start; align-items: flex-start; }
`;

function inline(file, className) {
  let svg = fs.readFileSync(path.join(PROFILE, "assets", file), "utf8");
  return svg.replace("<svg ", `<svg class="${className}" `);
}

function page(theme = "night") {
  const hero = inline(`hero-${theme}.svg`, "full hero");
  const lab = inline(`lab-${theme}.svg`, "pane lab");
  const shop = inline(`workshop-${theme}.svg`, "pane shop");
  const contrib = inline(`contrib-${theme}.svg`, "full contrib");
  const badges = fs
    .readFileSync(path.join(PROFILE, "data/badges.json"), "utf8");
  const ids = [...badges.matchAll(/"id": "([^"]+)"/g)].map((hit) => hit[1]);
  const contactAt = ids.indexOf("homepage");
  const badgeRow = ids
    .map((id, index) => `${index === contactAt ? "<br>" : ""}<img src="/assets/badges/${id}-${theme}.svg" alt="${id}">`)
    .join("");
  const readme = fs.readFileSync(path.join(PROFILE, "README.md"), "utf8");
  const summaries = [...readme.matchAll(/<summary>([\s\S]*?)<\/summary>/g)].map(
    (hit) => `<details><summary>${hit[1]}</summary></details>`,
  );
  return `<!doctype html><meta charset="utf-8"><title>v3</title><style>${CSS}</style>
<body class="dark"><article class="markdown-body">
${hero}
<p class="badges">${badgeRow}</p>
<div class="row">${lab}${shop}</div>
${contrib}
${summaries.join("")}
<p><img src="/assets/footer-${theme}.svg" alt="~/woojin-go"></p>
</article></body>`;
}

function serve(routes) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    if (routes[url]) {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(routes[url]);
      return;
    }
    const file = path.join(PROFILE, url.replace(/^\//, ""));
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

async function seek(page, seconds) {
  await page.evaluate((time) => {
    for (const svg of document.querySelectorAll("svg")) {
      if (typeof svg.setCurrentTime === "function") svg.setCurrentTime(time);
    }
    for (const animation of document.getAnimations()) {
      animation.pause();
      animation.currentTime = time * 1000;
    }
  }, seconds);
}

async function clipOf(page, selector) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) throw new Error(`missing ${selector}`);
  return { x: box.x, y: box.y, width: box.width, height: box.height };
}

fs.mkdirSync(EVIDENCE, { recursive: true });
const html = page("night");
const server = await serve({ "/": html, "/dark": html, "/light": page("day") });
const browser = await chromium.launch({ channel: "chrome" });
let height = 0;
try {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    reducedMotion: "no-preference",
  });
  const view = await context.newPage();
  await view.goto(`http://127.0.0.1:${PORT}/dark`, { waitUntil: "networkidle" });
  await view.waitForTimeout(80);
  const targets = {
    hero: "svg.hero",
    lab: "svg.lab",
    contrib: "svg.contrib",
  };
  await seek(view, 0.1);
  const probe = await view.evaluate(() => {
    const power = document.querySelector(".power");
    const reel = document.querySelector(".odo-reel");
    const style = power ? getComputedStyle(power) : null;
    return {
      powerOpacity: style && style.opacity,
      powerTransform: style && style.transform,
      reelTransform: reel ? getComputedStyle(reel).transform : null,
    };
  });
  console.log("probe", JSON.stringify(probe));
  for (const seconds of TIMES) {
    await seek(view, seconds);
    await view.waitForTimeout(40);
    for (const [name, selector] of Object.entries(targets)) {
      const clip = await clipOf(view, selector);
      const stamp = String(seconds).replace(".", "_");
      await view.screenshot({
        path: path.join(EVIDENCE, `filmstrip-${name}-${stamp}.png`),
        clip,
      });
    }
  }
  height = await view.locator("article.markdown-body").evaluate((el) => Math.round(el.getBoundingClientRect().height));
  await context.close();

  const videoContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    reducedMotion: "no-preference",
    recordVideo: { dir: EVIDENCE, size: { width: 1280, height: 800 } },
  });
  const film = await videoContext.newPage();
  await film.goto(`http://127.0.0.1:${PORT}/dark`, { waitUntil: "networkidle" });
  await film.waitForTimeout(6200);
  const video = film.video();
  await videoContext.close();
  const saved = await video.path();
  fs.renameSync(saved, path.join(EVIDENCE, "motion.webm"));

  const reduceContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  const quiet = await reduceContext.newPage();
  await quiet.goto(`http://127.0.0.1:${PORT}/dark`, { waitUntil: "networkidle" });
  await quiet.waitForTimeout(200);
  await quiet.screenshot({ path: path.join(EVIDENCE, "reduced.png") });
  await reduceContext.close();

  const light = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "light",
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  const lightPage = await light.newPage();
  await lightPage.goto(`http://127.0.0.1:${PORT}/light`, { waitUntil: "networkidle" });
  await lightPage.waitForTimeout(3000);
  await lightPage.screenshot({ path: path.join(EVIDENCE, "light.png"), fullPage: true });
  await light.close();

  const mobile = await browser.newContext({
    viewport: { width: 390, height: 800 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  const phone = await mobile.newPage();
  await phone.goto(`http://127.0.0.1:${PORT}/dark`, { waitUntil: "networkidle" });
  await phone.waitForTimeout(3000);
  await phone.screenshot({ path: path.join(EVIDENCE, "mobile.png"), fullPage: true });
  await mobile.close();

  const darkFull = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    colorScheme: "dark",
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  const darkPage = await darkFull.newPage();
  await darkPage.goto(`http://127.0.0.1:${PORT}/dark`, { waitUntil: "networkidle" });
  await darkPage.screenshot({ path: path.join(EVIDENCE, "dark.png"), fullPage: true });
  await darkFull.close();
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}

fs.writeFileSync(path.join(EVIDENCE, "fold.txt"), `${height}\n`);
const listen = spawnSync("lsof", ["-nP", `-iTCP:${PORT}`, "-sTCP:LISTEN"], { encoding: "utf8" });
console.log(`fold ${height}`);
console.log(`listen ${(listen.stdout || "").trim() || "empty"}`);
if (height >= 1200) process.exitCode = 1;
if ((listen.stdout || "").trim()) process.exitCode = 1;
