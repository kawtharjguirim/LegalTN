/* LegalTN — logique frontend (consomme GET /health et POST /repondre). */
(() => {
  "use strict";

  const I18N = {
    fr: {
      new_search: "Nouvelle recherche", sections: "Rubriques",
      home: "Accueil", search: "Recherche juridique",
      about: "À propos du corpus", corpus_title: "Corpus indexé",
      art_fr: "Articles français", art_ar: "Articles arabes",
      status: "Statut", online: "en ligne", offline: "hors ligne",
      disclaimer: "Démo locale — ne remplace pas un avis juridique.",
      demo_badge: "Démo locale",
      eyebrow: "Assistant juridique intelligent",
      hero_title: "Votre copilote pour le Code du travail tunisien",
      hero_sub: "Interrogez le corpus bilingue arabe/français en langage naturel. Chaque réponse cite l'article, sa page et son extrait — ou s'abstient honnêtement.",
      cta_start: "Commencer une recherche", cta_corpus: "Voir le corpus",
      stat_bil: "2 langues", stat_bil_l: "Corpus bilingue aligné",
      f1_t: "Réponses sourcées",
      f1_d: "Chaque réponse affiche l'article, sa page PDF et l'extrait exact du texte.",
      f2_t: "Bilingue FR / AR",
      f2_d: "Posez votre question en français ou en arabe : le corpus correspondant est interrogé.",
      f3_t: "Abstention honnête",
      f3_d: "Hors périmètre, l'assistant refuse de répondre plutôt que d'inventer un article.",
      ask: "Posez votre question juridique", send: "Envoyer",
      placeholder: "Ex. : Quel est le délai de préavis en cas de licenciement ?",
      // Questions d'exemple vérifiées (bon article en tête ; la dernière doit s'abstenir).
      suggestions: [
        "Quel est le préavis de rupture d'un CDI ?",
        "Quelle est la durée maximale du travail effectif par semaine ?",
        "Un salarié a-t-il droit à un congé à la naissance de son enfant ?",
        "Quelle est la capitale de la Tunisie ?",
      ],
      thinking: "Recherche dans le corpus…",
      results_title: "Articles trouvés",
      abs_title: "Question hors du Code du travail",
      did_you_mean: "Vouliez-vous dire :",
      show_steps: "Voir les étapes", detected: "Langue détectée",
      debug_mode: "Mode debug", full_article: "Voir l'article complet", short_extract: "Voir l'extrait",
      show_ar: "Voir la version arabe", show_fr: "Voir la version française", hide_alt: "Masquer la traduction",
      no_alt: "Pas d'article équivalent dans l'alignement AR/FR.",
      relevance: "Pertinence", rel_high: "élevée", rel_med: "moyenne", rel_low: "faible", raw_score: "score BM25",
      corrections_l: "Corrections", synonyms_l: "Synonymes ajoutés", steps_l: "Question après chaque étape", none: "aucune",
      abs_polite: "Votre question ne semble pas porter sur le Code du travail tunisien. Plutôt que de citer un article sans rapport, l'assistant préfère ne pas répondre. Essayez de reformuler avec des termes du droit du travail (contrat, congé, salaire, préavis…).",
      lang_names: { fr: "français", ar: "arabe", tunisien: "tunisien (arabe)", arabizi: "arabizi" },
      err_title: "Une erreur est survenue",
      err_conn: "Impossible de joindre le serveur local. Relancez l'API puis réessayez.",
      empty: "Les articles correspondants s'afficheront ici avec leur citation.",
      page: "page", score: "pertinence", ms: "ms", article: "Article",
      about_t: "À propos du corpus",
      about_p1: "LegalTN interroge l'édition bilingue du Code du travail tunisien (291 pages, arabe et français) avec un moteur de recherche lexical BM25 et un appariement des articles par numérotation.",
      ab_k1: "Corpus français", ab_k2: "Corpus arabe",
      ab_k3: "Couverture", ab_v3: "Code du travail uniquement",
      ab_k4: "Comportement", ab_v4: "Citation + abstention hors périmètre",
      about_note: "Outil de démonstration scientifique. Les réponses sont des extraits d'articles, pas un avis juridique. En cas de doute, consultez un professionnel.",
    },
    ar: {
      new_search: "بحث جديد", sections: "الأقسام",
      home: "الرئيسية", search: "بحث قانوني",
      about: "حول المجموعة", corpus_title: "المحتوى المفهرس",
      art_fr: "فصول بالفرنسية", art_ar: "فصول بالعربية",
      status: "الحالة", online: "متصل", offline: "غير متصل",
      disclaimer: "عرض محلي — لا يغني عن استشارة قانونية.",
      demo_badge: "عرض محلي",
      eyebrow: "مساعد قانوني ذكي",
      hero_title: "مرافقك الذكي لمجلة الشغل التونسية",
      hero_sub: "اطرح سؤالك باللغة الطبيعية على النص الثنائي عربي/فرنسي. كل إجابة تذكر الفصل وصفحته ونصه الحرفي — أو تمتنع بصدق.",
      cta_start: "ابدأ بحثاً", cta_corpus: "اطلع على المحتوى",
      stat_bil: "لغتان", stat_bil_l: "نص ثنائي اللغة مطابق",
      f1_t: "إجابات موثقة",
      f1_d: "كل إجابة تعرض الفصل ورقم الصفحة والمقطع الحرفي من النص.",
      f2_t: "ثنائي اللغة FR / AR",
      f2_d: "اطرح سؤالك بالفرنسية أو العربية : يُستجوب النص المناسب.",
      f3_t: "امتناع صادق",
      f3_d: "خارج المجال، يرفض المساعد الإجابة بدل اختلاق فصل.",
      ask: "اطرح سؤالك القانوني", send: "إرسال",
      placeholder: "مثال : ما هي مدة الإعلام قبل الفسخ ؟",
      // أمثلة تم التحقق منها
      suggestions: [
        "ما هي مدة الإعلام بإنهاء عقد الشغل؟",
        "ما هي المدة القصوى للعمل الفعلي في الأسبوع؟",
        "Quel est le préavis de rupture d'un CDI ?",
      ],
      thinking: "جارٍ البحث في المحتوى…",
      results_title: "الفصول المطابقة",
      abs_title: "سؤال خارج مجلة الشغل",
      did_you_mean: "هل تقصد:",
      show_steps: "عرض المراحل", detected: "اللغة المكتشفة",
      debug_mode: "وضع التصحيح", full_article: "عرض الفصل كاملاً", short_extract: "عرض المقتطف",
      show_ar: "عرض النسخة العربية", show_fr: "عرض النسخة الفرنسية", hide_alt: "إخفاء الترجمة",
      no_alt: "لا يوجد فصل مقابل في المطابقة عربي/فرنسي.",
      relevance: "الصلة", rel_high: "عالية", rel_med: "متوسطة", rel_low: "ضعيفة", raw_score: "نقاط BM25",
      corrections_l: "التصحيحات", synonyms_l: "المرادفات المضافة", steps_l: "السؤال بعد كل مرحلة", none: "لا شيء",
      abs_polite: "لا يبدو أن سؤالك يتعلق بمجلة الشغل التونسية. يفضّل المساعد عدم الإجابة بدل ذكر فصل لا علاقة له بالسؤال. حاول إعادة الصياغة بمصطلحات قانون الشغل (عقد، عطلة، أجر، إعلام…).",
      lang_names: { fr: "الفرنسية", ar: "العربية", tunisien: "التونسية (بالحروف العربية)", arabizi: "العربيزي" },
      err_title: "حدث خطأ",
      err_conn: "تعذر الاتصال بالخادم المحلي. أعد تشغيل الواجهة ثم حاول مجدداً.",
      empty: "ستظهر الفصول المطابقة هنا مع مصادرها.",
      page: "صفحة", score: "الصلة", ms: "م.ث", article: "الفصل",
      about_t: "حول المجموعة",
      about_p1: "يستجوب LegalTN النسخة الثنائية من مجلة الشغل التونسية (291 صفحة بالعربية والفرنسية) بمحرك بحث معجمي BM25 ومطابقة للفصول حسب الترقيم.",
      ab_k1: "النص الفرنسي", ab_k2: "النص العربي",
      ab_k3: "التغطية", ab_v3: "مجلة الشغل فقط",
      ab_k4: "السلوك", ab_v4: "اقتباس + امتناع خارج المجال",
      about_note: "أداة عرض علمية. الإجابات مقتطفات من فصول وليست استشارة قانونية. عند الشك استشر مختصاً.",
    },
  };

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const state = { lang: "fr", vue: "accueil", charge: false, debug: false, dernier: null };
  try { state.debug = localStorage.getItem("legaltn-debug") === "1"; } catch { /* stockage indisponible */ }
  const t = (k) => I18N[state.lang][k] ?? k;

  /* ---------- i18n ---------- */
  function appliquerLangue(lang) {
    state.lang = lang;
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    $$("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
    $$("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
    $$(".lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === lang));
    titre();
    rendreSuggestions();
    if (state.dernier) rendre(state.dernier);   // réafficher le résultat dans la nouvelle langue
  }

  /* ---------- navigation ---------- */
  const TITRES = { accueil: "home", recherche: "search", apropos: "about" };
  function titre() { $("#page-title").textContent = t(TITRES[state.vue]); }
  function naviguer(vue) {
    state.vue = vue;
    $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${vue}`));
    $$(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.nav === vue));
    titre();
    fermerSidebar();
    if (vue === "recherche") { $("#input-q").focus(); }
    $(".content").scrollTop = 0;
  }

  /* ---------- sidebar mobile ---------- */
  const sidebar = $("#sidebar"), overlay = $("#overlay");
  const fermerSidebar = () => { sidebar.classList.remove("open"); overlay.classList.remove("show"); };
  $("#btn-menu").onclick = () => {
    if (window.innerWidth > 900) sidebar.classList.toggle("collapsed");
    else { sidebar.classList.add("open"); overlay.classList.add("show"); }
  };
  $("#btn-close").onclick = fermerSidebar;
  overlay.onclick = fermerSidebar;

  /* ---------- santé API ---------- */
  async function chargerSante() {
    try {
      const r = await fetch("/health");
      const d = await r.json();
      const fr = d.articles_indexes.fr, ar = d.articles_indexes.ar;
      ["st-fr", "h-fr", "a-fr"].forEach(id => { $("#" + id).textContent = fr; });
      ["st-ar", "h-ar", "a-ar"].forEach(id => { $("#" + id).textContent = ar; });
      $("#st-dot").className = "dot ok";
      $("#st-ok").textContent = t("online");
    } catch {
      $("#st-dot").className = "dot ko";
      $("#st-ok").textContent = t("offline");
    }
  }

  /* ---------- suggestions ---------- */
  function rendreSuggestions() {
    $("#suggestions").innerHTML = I18N[state.lang].suggestions
      .map(q => `<button type="button" class="chip" dir="auto">${esc(q)}</button>`).join("");
    $$(".chip", $("#suggestions")).forEach(c =>
      c.onclick = () => { $("#input-q").value = c.textContent; soumettre(); });
  }

  /* ---------- recherche ---------- */
  const results = $("#results");
  const ICON_WARN = '<svg viewBox="0 0 24 24" class="i"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>';
  const ICON_ERR = '<svg viewBox="0 0 24 24" class="i"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>';
  const ICON_DOC = '<svg viewBox="0 0 24 24" class="i"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 13h6M9 17h6"/></svg>';

  const esc = (s) => String(s).replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function etatVide() {
    results.innerHTML = `<div class="card empty-state">${ICON_DOC}
      <p>${esc(t("empty"))}</p></div>`;
  }

  function etatChargement() {
    bandeauCorrection(null);
    results.innerHTML = `<div class="result-meta">${esc(t("thinking"))}</div>` +
      "<div class='skel'></div>".repeat(3);
  }

  function etatErreur(msg) {
    results.innerHTML = `<div class="err-card">${ICON_ERR}<div>
      <h3>${esc(t("err_title"))}</h3><p>${esc(msg)}</p></div></div>`;
  }

  /* ---------- rendu des résultats ---------- */
  const MOT = /[\p{L}\p{N}]+/gu;
  const sansAccents = (m) => m.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

  // Échappe le texte et entoure de <mark> les mots présents dans `mots`.
  function surligner(texte, mots) {
    const cibles = new Set((mots || []).map(sansAccents));
    texte = String(texte);
    if (!cibles.size) return esc(texte);
    let html = "", i = 0;
    for (const m of texte.matchAll(MOT)) {
      html += esc(texte.slice(i, m.index));
      html += cibles.has(sansAccents(m[0])) ? `<mark>${esc(m[0])}</mark>` : esc(m[0]);
      i = m.index + m[0].length;
    }
    return html + esc(texte.slice(i));
  }

  const fmtMs = (x) => (Math.round(Number(x) * 10) / 10).toLocaleString(state.lang === "ar" ? "ar-TN" : "fr-FR");
  const estArabe = (s) => /[؀-ۿ]/.test(s || "");
  const attrTexte = (s) => estArabe(s) ? 'dir="rtl" lang="ar"' : 'dir="ltr" lang="fr"';
  const classeTexte = (s) => estArabe(s) ? " ar-text" : "";

  // Bandeau « Vouliez-vous dire » sous la barre de recherche, mots corrigés en évidence.
  function bandeauCorrection(d) {
    const el = $("#did-you-mean");
    if (!d || !d.corrections || !d.corrections.length) { el.hidden = true; el.innerHTML = ""; return; }
    const corriges = d.corrections.flatMap(c => String(c.apres).match(MOT) || []).filter(m => m.length >= 3);
    const q = d.question_corrigee.replace(/[\s?؟]+$/, "");
    el.innerHTML = `${esc(t("did_you_mean"))} <span class="dym-q${classeTexte(q)}" ${attrTexte(q)}>${surligner(q, corriges)}</span> ?`;
    el.hidden = false;
  }

  // Mode debug : langue, corrections, synonymes et question après chaque étape.
  function panneauEtapes(d) {
    if (!state.debug || !d.etapes || !d.etapes.length) return "";
    const nomLangue = (I18N[state.lang].lang_names || {})[d.langue_detectee] || d.langue_detectee || d.langue;
    const corr = (d.corrections || []).map(c =>
      `<li><code dir="auto">${esc(c.avant)}</code> → <code dir="auto">${esc(c.apres)}</code></li>`).join("");
    const syn = (d.synonymes_ajoutes || []).map(x => `<code dir="auto">${esc(x)}</code>`).join(" ");
    const etapes = d.etapes.map(e =>
      `<li><span class="step-name">${esc(e.etape)}</span><code dir="auto">${esc(e.sortie || "∅")}</code></li>`).join("");
    return `<details class="steps" open><summary>${esc(t("show_steps"))}</summary>
      <dl class="steps-meta">
        <dt>${esc(t("detected"))}</dt><dd>${esc(nomLangue)}</dd>
        <dt>${esc(t("corrections_l"))}</dt><dd>${corr ? `<ul>${corr}</ul>` : esc(t("none"))}</dd>
        <dt>${esc(t("synonyms_l"))}</dt><dd>${syn || esc(t("none"))}</dd>
      </dl>
      <p class="steps-sub">${esc(t("steps_l"))}</p><ol>${etapes}</ol></details>`;
  }

  function niveau(pct) {
    return pct >= 70 ? ["high", t("rel_high")] : pct >= 40 ? ["med", t("rel_med")] : ["low", t("rel_low")];
  }

  function carte(c, i, max) {
    // Barre relative au meilleur résultat (le score BM25 brut n'a pas d'unité lisible).
    const pct = Math.max(8, Math.round((c.score / max) * 100));
    const [cls, lib] = niveau(pct);
    const va = c.version_alignee || {};
    const libAlt = va.langue === "ar" ? t("show_ar") : t("show_fr");
    const brut = state.debug ? `<span class="score-raw">${esc(t("raw_score"))} ${esc(String(c.score))}</span>` : "";
    const extrait = c.extrait || c.texte;
    const aussiComplet = extrait !== c.texte;
    const altHtml = va.disponible
      ? `<p class="alt-meta">${esc(t("article"))} <bdi>${esc(va.article || va.article_id)}</bdi> · ${esc(t("page"))} ${esc(String(va.page))}</p>
         <p class="answer-text${classeTexte(va.texte)}" ${attrTexte(va.texte)}>${esc(va.texte)}</p>`
      : `<p class="alt-none">${esc(t("no_alt"))}</p>`;
    return `<article class="card card-answer" style="animation-delay:${i * 60}ms">
      <div class="answer-head">
        <span class="badge-article">${esc(t("article"))} <bdi>${esc(c.article)}</bdi></span>
        <span class="badge-page">${esc(t("page"))} ${esc(String(c.page))}</span>
        <span class="rel rel-${cls}">
          <span class="rel-label">${esc(t("relevance"))} : ${esc(lib)}</span>
          <span class="score-bar" role="meter" aria-label="${esc(t("relevance"))}"
                aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}">
            <span class="score-fill" style="width:${pct}%"></span></span>
          ${brut}
        </span>
      </div>
      <p class="answer-text js-court${classeTexte(extrait)}" ${attrTexte(extrait)}>${surligner(extrait, c.surligner)}</p>
      <p class="answer-text js-complet${classeTexte(c.texte)}" ${attrTexte(c.texte)} hidden>${surligner(c.texte, c.surligner)}</p>
      <div class="alt-text" hidden>${altHtml}</div>
      <div class="answer-actions">
        ${aussiComplet ? `<button type="button" class="btn-link js-toggle-full">${esc(t("full_article"))}</button>` : ""}
        <button type="button" class="btn-link js-toggle-alt" data-lib="${esc(libAlt)}">${esc(libAlt)}</button>
      </div>
    </article>`;
  }

  function rendre(d) {
    state.dernier = d;
    bandeauCorrection(d);
    if (d.abstention) {
      results.innerHTML = panneauEtapes(d) + `<div class="abs-card" role="status">${ICON_WARN}<div>
        <h3>${esc(t("abs_title"))}</h3>
        <p>${esc(t("abs_polite"))}</p></div></div>
        <p class="latency">${esc(fmtMs(d.latence_ms))} ${esc(t("ms"))}</p>`;
      return;
    }
    const max = Math.max(...d.candidats.map(c => c.score), 1);
    results.innerHTML = panneauEtapes(d) + `<div class="result-meta">
        <span>${esc(t("results_title"))} — ${d.candidats.length}</span>
        <span class="latency-inline">${esc(fmtMs(d.latence_ms))} ${esc(t("ms"))}</span>
      </div>${d.candidats.map((c, i) => carte(c, i, max)).join("")}`;
  }

  // Boutons des cartes (délégation d'événements).
  results.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const card = b.closest(".card-answer");
    if (!card) return;
    if (b.classList.contains("js-toggle-full")) {
      const complet = card.querySelector(".js-complet");
      const ouvrir = complet.hidden;
      complet.hidden = !ouvrir;
      card.querySelector(".js-court").hidden = ouvrir;
      b.textContent = ouvrir ? t("short_extract") : t("full_article");
    } else if (b.classList.contains("js-toggle-alt")) {
      const alt = card.querySelector(".alt-text");
      alt.hidden = !alt.hidden;
      b.textContent = alt.hidden ? b.dataset.lib : t("hide_alt");
    }
  });

  async function soumettre() {
    const q = $("#input-q").value.trim();
    if (!q || state.charge) return;
    state.charge = true;
    $("#btn-send").disabled = true;
    etatChargement();
    try {
      const r = await fetch("/repondre", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, k: 3 }),
      });
      const d = await r.json();
      if (!r.ok) etatErreur(d.erreur || String(r.status));
      else rendre(d);
    } catch {
      etatErreur(t("err_conn"));
    } finally {
      state.charge = false;
      $("#btn-send").disabled = false;
    }
  }

  /* ---------- câblage ---------- */
  $("#form-search").onsubmit = (e) => { e.preventDefault(); soumettre(); };
  const chk = $("#chk-debug");
  chk.checked = state.debug;
  chk.onchange = () => {
    state.debug = chk.checked;
    try { localStorage.setItem("legaltn-debug", state.debug ? "1" : "0"); } catch { /* ignoré */ }
    if (state.dernier) rendre(state.dernier);
  };
  $("#btn-new").onclick = () => {
    $("#input-q").value = ""; state.dernier = null; bandeauCorrection(null); etatVide(); naviguer("recherche");
  };
  $$("[data-nav]").forEach(el =>
    el.addEventListener("click", e => { e.preventDefault(); naviguer(el.dataset.nav); }));
  $$(".lang-btn").forEach(b => b.onclick = () => appliquerLangue(b.dataset.lang));

  etatVide();
  chargerSante();
  appliquerLangue("fr");
})();
