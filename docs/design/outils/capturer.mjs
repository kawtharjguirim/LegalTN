// Pilote Edge headless (DevTools) : captures + audit de contraste WCAG sur une liste de pages.
// Usage : node capturer.mjs <portDebug> <plan.json> <dossierSortie>
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const [portDebug, planFichier, dossier] = process.argv.slice(2);
mkdirSync(dossier, { recursive: true });
const plan = JSON.parse(readFileSync(planFichier, "utf8"));
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const cibles = await (await fetch(`http://127.0.0.1:${portDebug}/json`)).json();
const page = cibles.find(c => c.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r));
let id = 0; const attente = new Map();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && attente.has(m.id)) { attente.get(m.id)(m); attente.delete(m.id); }
});
const cmd = (method, params = {}) => new Promise(r => { const i = ++id; attente.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluer = async (expr) => {
  const r = await cmd("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) console.error("ERREUR JS", JSON.stringify(r.result.exceptionDetails).slice(0, 400));
  return r.result?.result?.value;
};

// Audit de contraste : chaque élément visible portant du texte direct, fond effectif par remontée.
const AUDIT = `(() => {
  const rgb = s => { const m = s.match(/[\\d.]+/g) || []; return m.map(Number); };
  const lum = ([r,g,b]) => { const f = v => { v/=255; return v <= .03928 ? v/12.92 : ((v+.055)/1.055)**2.4; };
    return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const melange = (h, b) => { const a = h[3] ?? 1; return [0,1,2].map(i => h[i]*a + b[i]*(1-a)); };
  function fond(el) {
    const pile = [];
    for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor);
      if (c.length === 4 && c[3] === 0) continue;
      pile.push(c); if ((c[3] ?? 1) >= 1) break;
    }
    let base = [255,255,255];
    for (let i = pile.length - 1; i >= 0; i--) base = melange(pile[i], base);
    return base;
  }
  const echecs = []; let total = 0;
  for (const el of document.querySelectorAll("body *")) {
    if (!["#text"].some(() => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none" || el.closest("[hidden]") || !el.getClientRects().length) continue;
    if (el.closest("svg")) continue;
    const bg = fond(el), fg = melange(rgb(cs.color), bg);
    const L1 = lum(fg), L2 = lum(bg), ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const px = parseFloat(cs.fontSize), gras = Number(cs.fontWeight) >= 700;
    const grand = px >= 24 || (px >= 18.66 && gras);
    const seuil = grand ? 3 : 4.5; total++;
    if (ratio < seuil) echecs.push({ el: el.tagName.toLowerCase() + (el.className ? "." + String(el.className).split(" ").join(".") : ""),
      texte: [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(" ").slice(0, 40),
      ratio: Math.round(ratio*100)/100, seuil, px });
  }
  return { total, echecs };
})()`;

const rapport = {};
await cmd("Page.enable"); await cmd("Runtime.enable"); await cmd("Network.enable"); await cmd("Network.setCacheDisabled", { cacheDisabled: true });
for (const etape of plan) {
  await cmd("Emulation.setDeviceMetricsOverride", { width: etape.largeur, height: etape.hauteur, deviceScaleFactor: 1, mobile: !!etape.mobile });
  if (etape.url) { await cmd("Page.navigate", { url: etape.url }); await sleep(etape.attente ?? 1500); }
  if (etape.script) { await evaluer(etape.script); await sleep(etape.apres ?? 1800); }
  for (let k = 0; k < (etape.tabs || 0); k++) {   // navigation au clavier réelle (touche Tab)
    for (const type of ["keyDown", "keyUp"]) await cmd("Input.dispatchKeyEvent", { type, key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
    await sleep(60);
  }
  // Pleine page seulement si la page dépasse l'écran (sinon Chromium décale les pages RTL courtes).
  const haute = await evaluer("document.documentElement.scrollHeight > innerHeight");
  const r = await cmd("Page.captureScreenshot", { format: "png", captureBeyondViewport: !!haute });
  writeFileSync(`${dossier}/${etape.nom}.png`, Buffer.from(r.result.data, "base64"));
  rapport[etape.nom] = { contraste: await evaluer(AUDIT), etat: etape.etat ? await evaluer(etape.etat) : undefined };
  const c = rapport[etape.nom].contraste;
  console.log(etape.nom, "| textes vérifiés:", c?.total, "| échecs AA:", c?.echecs.length);
}
writeFileSync(`${dossier}/audit.json`, JSON.stringify(rapport, null, 2));
ws.close();
