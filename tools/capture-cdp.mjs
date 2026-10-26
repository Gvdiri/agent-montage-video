#!/usr/bin/env node
/**
 * Captures reelles pilotees par CDP — complement de `capture-product-pages.py`.
 *
 * Ce que le script Python ne sait pas faire et qui manquait :
 *  - forcer `prefers-color-scheme: dark` (les captures claires font exploser la
 *    luminance du montage — voir memoire « mesurer contre la reference ») ;
 *  - capturer une SEQUENCE de positions de scroll, pour fabriquer un b-roll de
 *    defilement reel plutot qu'un panoramique sur une image fixe.
 *
 * Usage :
 *   node tools/capture-cdp.mjs --url <url> --out <dossier> --slug <slug>
 *        [--width 1600] [--height 1000] [--scale 2] [--dark|--light]
 *        [--wait 4000] [--scroll 0,600,1200,...] [--full]
 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const args = process.argv.slice(2);
const opt = (n, d = null) => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : d;
};
const flag = (n) => args.includes(`--${n}`);

const URL_ = opt("url");
const OUT = resolve(opt("out", "."));
const SLUG = opt("slug", "capture");
const W = parseInt(opt("width", "1600"), 10);
const H = parseInt(opt("height", "1000"), 10);
const SCALE = parseFloat(opt("scale", "2"));
const WAIT = parseInt(opt("wait", "4500"), 10);
const DARK = !flag("light");
const SCROLLS = opt("scroll") ? opt("scroll").split(",").map((s) => parseInt(s.trim(), 10)) : [0];
const FULL = flag("full");
// Certaines preuves ne sont accessibles qu'apres un clic (le panneau Outline de
// GitHub, par exemple, qui est LA capture qui montre la portee d'un document).
const CLICK = opt("click");
const CLICK_WAIT = parseInt(opt("clickwait", "1800"), 10);

if (!URL_) {
  console.error("--url manquant");
  process.exit(1);
}

const CHROME = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
].find((p) => existsSync(p));
if (!CHROME) {
  console.error("Chrome introuvable");
  process.exit(1);
}

const PORT = 9222 + Math.floor(Math.random() * 500);
const proc = spawn(CHROME, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--mute-audio",
  "--no-first-run",
  "--disable-extensions",
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${resolve(OUT, "..", `_chrome-cdp-${PORT}`)}`,
  "--window-size=1600,1000",
  "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function endpoint() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      const j = await r.json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl;
    } catch {}
    await sleep(250);
  }
  throw new Error("CDP injoignable");
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.sessions = new Map();
    ws.addEventListener("message", (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && this.pending.has(m.id)) {
        const { res, rej } = this.pending.get(m.id);
        this.pending.delete(m.id);
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
      }
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
}

const main = async () => {
  const wsUrl = await endpoint();
  const ws = new WebSocket(wsUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  const cdp = new Cdp(ws);

  const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
  const S = sessionId;

  await cdp.send("Page.enable", {}, S);
  await cdp.send("Runtime.enable", {}, S);
  await cdp.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-color-scheme", value: DARK ? "dark" : "light" }],
  }, S);
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: W, height: H, deviceScaleFactor: SCALE, mobile: false,
  }, S);
  await cdp.send("Network.enable", {}, S).catch(() => {});
  await cdp.send("Network.setUserAgentOverride", {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
  }, S).catch(() => {});

  await cdp.send("Page.navigate", { url: URL_ }, S);
  await sleep(WAIT);

  // --probe : liste les controles de la page, pour trouver un selecteur sans
  // deviner. Une capture ratee coute un aller-retour ; une sonde, rien.
  if (flag("probe")) {
    const { result } = await cdp.send("Runtime.evaluate", {
      expression: `Array.from(document.querySelectorAll("button,a[role=button],summary"))
        .map(e => [e.tagName, e.getAttribute("aria-label"), e.getAttribute("data-testid"), (e.textContent||"").trim().slice(0,28)].join(" | "))
        .filter(t => t.length > 12).slice(0, 80).join("\n")`,
      returnByValue: true,
    }, S);
    console.log(result.value);
  }

  if (CLICK) {
    const { result } = await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const el = document.querySelector(${JSON.stringify(CLICK)});
        if (!el) return "introuvable";
        el.click();
        return "clique";
      })()`,
      returnByValue: true,
    }, S);
    console.log(`  clic ${CLICK} -> ${result.value}`);
    await sleep(CLICK_WAIT);
  }

  mkdirSync(OUT, { recursive: true });
  const faits = [];

  const metrics = await cdp.send("Page.getLayoutMetrics", {}, S);
  const pageH = Math.round(metrics.cssContentSize?.height ?? H);

  if (FULL) {
    const shot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: true,
      clip: { x: 0, y: 0, width: W, height: Math.min(pageH, 16000), scale: 1 },
    }, S);
    const f = resolve(OUT, `capture_${SLUG}_pleine.png`);
    writeFileSync(f, Buffer.from(shot.data, "base64"));
    faits.push({ fichier: f, y: 0, hauteur: pageH });
    console.log(`  ${SLUG}_pleine  ${W}x${pageH}`);
  }

  for (const y of SCROLLS) {
    await cdp.send("Runtime.evaluate", { expression: `window.scrollTo(0, ${y})` }, S);
    await sleep(700);
    const shot = await cdp.send("Page.captureScreenshot", { format: "png" }, S);
    const suffix = SCROLLS.length > 1 ? `_y${String(y).padStart(5, "0")}` : "";
    const f = resolve(OUT, `capture_${SLUG}${suffix}.png`);
    writeFileSync(f, Buffer.from(shot.data, "base64"));
    faits.push({ fichier: f, y });
    console.log(`  ${SLUG}${suffix}  y=${y}`);
  }

  writeFileSync(resolve(OUT, `_${SLUG}.json`), JSON.stringify({
    url: URL_, slug: SLUG, sombre: DARK, largeur: W, hauteur: H,
    echelle: SCALE, hauteur_page: pageH, capture_le: new Date().toISOString().slice(0, 10),
    fichiers: faits,
  }, null, 2));

  ws.close();
  proc.kill();
  process.exit(0);
};

main().catch((e) => {
  console.error(e.message);
  proc.kill();
  process.exit(1);
});
