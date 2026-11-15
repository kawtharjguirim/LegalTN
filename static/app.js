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
      suggestions: [
        "Quel est le délai de préavis en cas de licenciement ?",
        "Quelle est la durée légale du travail hebdomadaire ?",
        "Quels sont les droits du salarié en cas de congé maladie ?",
        "Quelle est la capitale de la Tunisie ?",
      ],
      thinking: "Recherche dans le corpus…",
      results_title: "Articles trouvés",
      abs_title: "Aucune réponse trouvée",
      err_title: "Une erreur est survenue",
      err_conn: "Impossible de joindre le serveur local. Relancez l'API puis réessayez.",
      empty: "Les articles correspondants s'afficheront ici avec leur citation.",
      page: "page", score: "pertinence", ms: "ms",
      steps: "Étapes du traitement", engine: "Moteur",
      other_fr: "Version française", other_ar: "Version arabe",
      eng_bm25: "BM25 (Bronze)", eng_hybride: "Hybride BM25 + e5 (Silver)",
      answer_title: "Réponse rédigée", llm_by: "Rédigée par",
      summary_btn: "Résumé en langage clair", summary_wait: "Résumé en cours…",
      summary_err: "Résumé indisponible.",
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
      suggestions: [
        "ما هي مدة الإعلام قبل الفسخ ؟",
        "ما هو نظام العمل الأسبوعي ؟",
        "Quel est le délai de préavis en cas de licenciement ?",
      ],
      thinking: "جارٍ البحث في المحتوى…",
      results_title: "الفصول المطابقة",
      abs_title: "لا توجد إجابة",
      err_title: "حدث خطأ",
      err_conn: "تعذر الاتصال بالخادم المحلي. أعد تشغيل الواجهة ثم حاول مجدداً.",
      empty: "ستظهر الفصول المطابقة هنا مع مصادرها.",
      page: "صفحة", score: "الصلة", ms: "م.ث",
      steps: "مراحل المعالجة", engine: "المحرك",
      other_fr: "النص الفرنسي", other_ar: "النص العربي",
      eng_bm25: "BM25 (برونزي)", eng_hybride: "هجين BM25 + e5 (فضي)",
      answer_title: "إجابة محررة", llm_by: "حررها",
      summary_btn: "ملخص بلغة واضحة", summary_wait: "جارٍ التلخيص…",
      summary_err: "الملخص غير متاح.",
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
  const state = { lang: "fr", vue: "accueil", charge: false, llm: false };
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
      state.llm = Boolean(d.llm);
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
      .map(q => `<button type="button" class="chip">${q}</button>`).join("");
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
    results.innerHTML = `<div class="result-meta">${esc(t("thinking"))}</div>` +
      "<div class='skel'></div>".repeat(3);
  }

  function etatErreur(msg) {
    results.innerHTML = `<div class="err-card">${ICON_ERR}<div>
      <h3>${esc(t("err_title"))}</h3><p>${esc(msg)}</p></div></div>`;
  }

  /* Étapes visibles et moteur utilisé (renvoyés par l'API). */
  function blocEtapes(d) {
    if (!d.etapes || !d.etapes.length) return "";
    const moteur = d.moteur ? `<span class="badge-engine">${esc(t("engine"))} : ${esc(t("eng_" + d.moteur))}</span>` : "";
    return `<details class="steps"><summary>${esc(t("steps"))} ${moteur}</summary>
      <ol>${d.etapes.map(e => `<li>${esc(e)}</li>`).join("")}</ol></details>`;
  }

  /* Article de même intitulé dans l'autre langue (citation bilingue). */
  function blocAutreLangue(c) {
    const a = c.autre_langue;
    if (!a) return "";
    const cls = a.langue === "ar" ? " ar-text" : "";
    return `<details class="other-lang"><summary>${esc(t("other_" + a.langue))}
        · ${esc(t("page"))} ${esc(String(a.page))}</summary>
      <p class="answer-text${cls}" dir="${a.langue === "ar" ? "rtl" : "ltr"}">${esc(a.texte)}</p></details>`;
  }

  /* Réponse rédigée par le LLM, citation vérifiée côté serveur. */
  function blocRedaction(d) {
    const r = d.reponse_redigee;
    if (!r) return "";
    const cls = d.langue === "ar" ? " ar-text" : "";
    return `<article class="card card-llm">
      <div class="answer-head"><span class="badge-llm">${esc(t("answer_title"))}</span>
        <span class="score-txt">${esc(t("llm_by"))} ${esc(r.modele)} · ${r.latence_ms} ${esc(t("ms"))}</span></div>
      <p class="answer-text${cls}" dir="${d.langue === "ar" ? "rtl" : "ltr"}">${esc(r.texte)}</p>
      <p class="llm-warn">${esc(r.avertissement)}</p></article>`;
  }

  function boutonResume(c, langue) {
    if (!state.llm) return "";
    return `<button type="button" class="btn-summary" data-article="${esc(c.article)}"
      data-langue="${esc(langue)}">${esc(t("summary_btn"))}</button><div class="summary"></div>`;
  }

  async function resumer(btn) {
    const zone = btn.nextElementSibling;
    btn.disabled = true;
    zone.textContent = t("summary_wait");
    try {
      const r = await fetch("/resumer", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ article: btn.dataset.article, langue: btn.dataset.langue }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.erreur);
      zone.dir = d.langue === "ar" ? "rtl" : "ltr";
      zone.innerHTML = `<p>${esc(d.resume)}</p><p class="llm-warn">${esc(d.avertissement)}</p>`;
      btn.remove();
    } catch {
      zone.textContent = t("summary_err");
      btn.disabled = false;
    }
  }

  function rendre(d) {
    if (d.abstention) {
      results.innerHTML = `<div class="abs-card">${ICON_WARN}<div>
        <h3>${esc(t("abs_title"))}</h3>
        <p>${esc(d.message || "")}</p></div></div>${blocEtapes(d)}`;
      return;
    }
    const max = Math.max(...d.candidats.map(c => c.score), 1e-9);
    const cartes = d.candidats.map((c, i) => {
      const pct = Math.round((c.score / max) * 100);
      const ar = d.langue === "ar" ? " ar-text" : "";
      return `<article class="card card-answer" style="animation-delay:${i * 60}ms">
        <div class="answer-head">
          <span class="badge-article">${esc("Article " + c.article)}</span>
          <span class="badge-page">${esc(t("page"))} ${esc(String(c.page))}</span>
          <span class="score-wrap">
            <span class="score-txt">${esc(t("score"))} ${c.score}</span>
            <span class="score-bar"><span class="score-fill" style="width:${pct}%"></span></span>
          </span>
        </div>
        <p class="answer-text${ar}" dir="${d.langue === "ar" ? "rtl" : "ltr"}">${esc(c.texte)}</p>
        ${boutonResume(c, d.langue)}
        ${blocAutreLangue(c)}
      </article>`;
    }).join("");
    results.innerHTML = `<div class="result-meta">
        ${esc(t("results_title"))} — ${d.candidats.length}
      </div>${blocEtapes(d)}${blocRedaction(d)}${cartes}
      <p class="latency">${d.latence_ms} ${esc(t("ms"))}</p>`;
    $$(".btn-summary", results).forEach(b => b.onclick = () => resumer(b));
  }

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
  $("#btn-new").onclick = () => {
    $("#input-q").value = ""; etatVide(); naviguer("recherche");
  };
  $$("[data-nav]").forEach(el =>
    el.addEventListener("click", e => { e.preventDefault(); naviguer(el.dataset.nav); }));
  $$(".lang-btn").forEach(b => b.onclick = () => appliquerLangue(b.dataset.lang));

  etatVide();
  chargerSante();
  appliquerLangue("fr");
})();
