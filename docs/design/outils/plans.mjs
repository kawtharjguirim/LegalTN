// Génère les plans de capture : maquettes (file://) et interface réelle (serveur local).
// Usage : node plans.mjs <racineDepot> <portApp>
import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const [racine, port] = process.argv.slice(2);
const app = `http://127.0.0.1:${port}/`;

const maquettes = [];
for (const m of ["a_institutionnel", "b_moteur_epure", "c_outil_analyse"])
  for (const lang of ["fr", "ar"])
    maquettes.push({ nom: `${m}_${lang}`, url: pathToFileURL(`${racine}/static/maquettes/${m}.html`).href + `?lang=${lang}`,
      largeur: 1280, hauteur: 900, attente: 1200 });
writeFileSync("design/plan_maquettes.json", JSON.stringify(maquettes, null, 1));

// Interface réelle : la question est posée comme un utilisateur (champ + envoi du formulaire).
const poser = (q, lang, debug, actions = "") => `(async () => {
  document.querySelector('.lang-btn[data-lang="${lang}"]').click();
  const chk = document.querySelector("#chk-debug");
  if (chk.checked !== ${debug}) { chk.checked = ${debug}; chk.dispatchEvent(new Event("change")); }
  document.querySelector('[data-nav="recherche"]').click();
  document.querySelector("#input-q").value = ${JSON.stringify(q)};
  document.querySelector("#form-search").requestSubmit();
  await new Promise(r => setTimeout(r, 1200));
  ${actions}
})()`;
const etat = `({ dir: document.documentElement.dir,
  bandeau: document.querySelector("#did-you-mean")?.hidden ? null : document.querySelector("#did-you-mean")?.innerText,
  articles: [...document.querySelectorAll(".card-answer")].map(c => c.innerText.split("\\n")[0]).slice(0, 3),
  marks: document.querySelectorAll("#results mark").length,
  etapes: !!document.querySelector(".steps"), abstention: !!document.querySelector(".abs-card"),
  latence: document.querySelector(".latency-inline, .latency")?.innerText,
  debordement: document.documentElement.scrollWidth > innerWidth })`;
const QFR = "quel est le préavi de rupture d'un contart CDI ?";
const QAR = "ما هي مدة الاعلام بانهاء عقد الشغلل؟";
const ouvrir = `document.querySelector(".js-toggle-full")?.click(); document.querySelector(".js-toggle-alt")?.click();`;
const focus = `(() => { const a = document.activeElement; return { tag: a.tagName, texte: (a.innerText || a.value || "").slice(0, 40), focusVisible: a.matches(":focus-visible"), outline: getComputedStyle(a).outlineStyle + " " + getComputedStyle(a).outlineColor }; })()`;
const reel = [
  { nom: "accueil_fr", url: app, largeur: 1280, hauteur: 900, attente: 2000, etat },
  { nom: "fr_bureau_debug", largeur: 1280, hauteur: 900, script: poser(QFR, "fr", true, ouvrir), etat },
  { nom: "ar_bureau_debug", largeur: 1280, hauteur: 900, script: poser(QAR, "ar", true, ouvrir), etat },
  { nom: "fr_abstention", largeur: 1280, hauteur: 900, script: poser("Quelle est la capitale de la Tunisie ?", "fr", false), etat },
  { nom: "fr_mobile", largeur: 390, hauteur: 844, mobile: true, script: poser(QFR, "fr", true, ouvrir), etat },
  { nom: "ar_mobile", largeur: 390, hauteur: 844, mobile: true, script: poser(QAR, "ar", false), etat },
];
const apres = [
  ...reel.slice(0, 4),
  { nom: "accueil_ar", url: app, largeur: 1280, hauteur: 900, attente: 2000, script: `document.querySelector('.lang-btn[data-lang="ar"]').click()`, apres: 400, etat },
  { nom: "ar_abstention", largeur: 1280, hauteur: 900, script: poser("ما هي عاصمة تونس؟", "ar", false), etat },
  { nom: "fr_mobile", largeur: 390, hauteur: 844, mobile: true, script: poser(QFR, "fr", true, ouvrir), etat },
  { nom: "ar_mobile", largeur: 390, hauteur: 844, mobile: true, script: poser(QAR, "ar", true, ouvrir), etat },
  { nom: "fr_clavier", url: app, largeur: 1280, hauteur: 900, attente: 1500, script: poser(QFR, "fr", false), tabs: 9, etat: focus },
];
writeFileSync("design/plan_apres.json", JSON.stringify(apres, null, 1));
writeFileSync("design/plan_reel.json", JSON.stringify(reel, null, 1));
console.log(maquettes.length, reel.length);
