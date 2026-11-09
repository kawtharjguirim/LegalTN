/* Outils communs aux trois maquettes (statiques : aucun appel réseau).
   Langue choisie par l'adresse : maquette.html?lang=ar */
(() => {
  const lang = new URLSearchParams(location.search).get("lang") === "ar" ? "ar" : "fr";
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

  const T = {
    fr: {
      titre: "LegalTN", sous_titre: "Code du travail tunisien — recherche d'articles",
      ask: "Posez votre question", send: "Rechercher", dym: "Vouliez-vous dire :",
      article: "Article", page: "page", relevance: "Pertinence",
      rel_high: "élevée", rel_med: "moyenne", rel_low: "faible", raw_score: "score BM25",
      full: "Voir l'article complet", alt_ar: "Voir la version arabe", alt_fr: "Voir la version française",
      steps: "Voir les étapes", detected: "Langue détectée", corrections: "Corrections",
      synonyms: "Synonymes ajoutés", none: "aucune", ms: "ms", results: "articles trouvés",
      debug: "Mode debug", source: "Code du travail, édition bilingue IORT",
      abst_t: "Question hors du Code du travail", disclaimer: "Démo locale — ne remplace pas un avis juridique.",
      lang_names: { fr: "français", ar: "arabe", tunisien: "tunisien", arabizi: "arabizi" },
      cite: "Citer", copy_ref: "Référence",
    },
    ar: {
      titre: "LegalTN", sous_titre: "مجلة الشغل التونسية — البحث في الفصول",
      ask: "اطرح سؤالك", send: "بحث", dym: "هل تقصد:",
      article: "الفصل", page: "صفحة", relevance: "الصلة",
      rel_high: "عالية", rel_med: "متوسطة", rel_low: "ضعيفة", raw_score: "نقاط BM25",
      full: "عرض الفصل كاملاً", alt_ar: "عرض النسخة العربية", alt_fr: "عرض النسخة الفرنسية",
      steps: "عرض المراحل", detected: "اللغة المكتشفة", corrections: "التصحيحات",
      synonyms: "المرادفات المضافة", none: "لا شيء", ms: "م.ث", results: "فصول مطابقة",
      debug: "وضع التصحيح", source: "مجلة الشغل، النسخة الثنائية للمطبعة الرسمية",
      abst_t: "سؤال خارج مجلة الشغل", disclaimer: "عرض محلي — لا يغني عن استشارة قانونية.",
      lang_names: { fr: "الفرنسية", ar: "العربية", tunisien: "التونسية", arabizi: "العربيزي" },
      cite: "اقتباس", copy_ref: "المرجع",
    },
  }[lang];

  const esc = (s) => String(s).replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const MOT = /[\p{L}\p{N}]+/gu;
  const base = (m) => m.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  function surligner(texte, mots) {
    const cibles = new Set((mots || []).map(base));
    texte = String(texte); let html = "", i = 0;
    for (const m of texte.matchAll(MOT)) {
      html += esc(texte.slice(i, m.index));
      html += cibles.has(base(m[0])) ? `<mark>${esc(m[0])}</mark>` : esc(m[0]);
      i = m.index + m[0].length;
    }
    return html + esc(texte.slice(i));
  }
  const estArabe = (s) => /[؀-ۿ]/.test(s || "");
  const attr = (s) => estArabe(s) ? 'dir="rtl" lang="ar"' : 'dir="ltr" lang="fr"';
  const d = window.EXEMPLE[lang];
  const max = Math.max(...d.candidats.map(c => Number(c.score)));
  const niveau = (c) => {
    const pct = Math.max(8, Math.round(Number(c.score) / max * 100));
    return { pct, cls: pct >= 70 ? "high" : pct >= 40 ? "med" : "low",
             lib: pct >= 70 ? T.rel_high : pct >= 40 ? T.rel_med : T.rel_low };
  };
  const corriges = d.corrections.flatMap(c => String(c.apres).match(MOT) || []).filter(m => m.length >= 3);
  const qCorrigee = d.question_corrigee.replace(/[\s?؟]+$/, "");
  const fmtMs = (x) => (Math.round(Number(x) * 10) / 10).toLocaleString(lang === "ar" ? "ar-TN" : "fr-FR");
  window.M = { lang, T, esc, surligner, attr, estArabe, d, niveau, corriges, qCorrigee, fmtMs,
    libAlt: (c) => c.version_alignee.langue === "ar" ? T.alt_ar : T.alt_fr,
    nomLangue: T.lang_names[d.langue_detectee] || d.langue_detectee };
})();
