/* Données d'exemple des maquettes : réponses RÉELLES de l'API locale (POST /repondre, k=3),
   enregistrées le 9 novembre 2026 sur la branche design-et-demo. Aucune donnée inventée. */
window.EXEMPLE = {
 "fr": {
  "question_originale": "quel est le préavi de rupture d'un contart CDI ?",
  "question_corrigee": "quel est le préavis de rupture d'un contrat à durée indéterminée ?",
  "corrections": [
   {
    "type": "sigle",
    "avant": "CDI",
    "apres": "à durée indéterminée"
   },
   {
    "type": "orthographe",
    "avant": "préavi",
    "apres": "préavis"
   },
   {
    "type": "orthographe",
    "avant": "contart",
    "apres": "contrat"
   }
  ],
  "langue": "fr",
  "langue_detectee": "fr",
  "etapes": [
   {
    "etape": "1. langue",
    "sortie": "fr"
   },
   {
    "etape": "2. translittération arabizi",
    "sortie": "quel est le préavi de rupture d'un contart CDI ?"
   },
   {
    "etape": "3. mots vides",
    "sortie": "préavi rupture contart CDI"
   },
   {
    "etape": "4. normalisation",
    "sortie": "preavi rupture contart cdi"
   },
   {
    "etape": "5. lexique tunisien et sigles",
    "sortie": "preavi rupture contart duree indeterminee"
   },
   {
    "etape": "6. racinisation arabe",
    "sortie": "preavi rupture contart duree indeterminee"
   },
   {
    "etape": "7. correction SymSpell",
    "sortie": "preavis rupture contrat duree indeterminee"
   },
   {
    "etape": "8. synonymes",
    "sortie": "preavis rupture contrat duree indeterminee"
   }
  ],
  "synonymes_ajoutes": [],
  "abstention": false,
  "candidats": [
   {
    "article": "14 bis",
    "texte": "Article 14 bis. (Ajouté par la loi n° 94-29 du 21 février 1994).- Le préavis de rupture du contrat de travail à durée indéterminée est notifié par lettre recommandée adressée à l’autre partie un mois avant la rupture du contrat. Les travailleurs sont autorisés à s’absenter durant toute la deuxième moitié de la durée du préavis en vue de leur permettre de chercher un autre emploi. La durée d’absence est considérée comme travail effectif et n’entraîne aucune réduction de salaires ou d’indemnités. Le tout sans préjudice des prescriptions plus avantageuses pour le travailleur résultant de dispositions spéciales prévues par l’accord des parties, la convention collective ou l’usage.",
    "page": "279",
    "ligne": 22,
    "article_id": "FR-14",
    "score": 18.46,
    "extrait": "(Ajouté par la loi n° 94-29 du 21 février 1994).- Le préavis de rupture du contrat de travail à durée indéterminée est notifié par lettre recommandée adressée à l’autre partie un mois avant la rupture du contrat.",
    "surligner": [
     "contrat",
     "durée",
     "indéterminée",
     "préavis",
     "rupture"
    ],
    "version_alignee": {
     "langue": "ar",
     "disponible": true,
     "article_id": "AR-14-مكرر",
     "article": "14 bis",
     "page": "14",
     "texte": "الفصل 14 مكرر (أضيف بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- يتم الإعلام بإنهاء عقد الشغل المبرم لمدة غير معينة برسالة مضمونة الوصول توجه إلى الطرف الآخر قبل شهر من إنهاء العقد. ويرخص للعملة بالتغيب كامل النصف الثاني من مدّة أجل الإعلام ليتسنى لهم السعي للحصول على شغل آخر. وتعتبر مدة التغيب عملا فعليا ولا ينجر عنه أي وكل هذا لا يمس بالمقتضيات الأكثر فائدة للعامل والناتجة عن أحكام خاصة تضمنها اتفاق الطرفين أو الاتفاقية المشتركة أو العرف."
    }
   },
   {
    "article": "14",
    "texte": "Article 14.- (Modifié par la loi n° 94-29 du 21 février 1994). .- Le contrat de travail à durée déterminée prend fin par l’expiration de la durée convenue ou par l’accomplissement du travail objet du contrat. Le contrat à durée indéterminée prend fin par l’expiration du délai de préavis. Le contrat de travail à durée déterminée ou à durée indéterminée prend fin : a) par l’accord des parties; b) par la volonté de l’une des parties suite à une faute grave commise par l’autre partie; c) en cas d’empêchement d’exécution résultant soit d’un cas fortuit ou de force majeure survenu avant ou pendant l’exécution du contrat, soit du décès du travailleur; d) par la résolution prononcée par le juge dans les cas déterminés par la loi; e) dans les autres cas prévus par la loi.",
    "page": "279",
    "ligne": 21,
    "article_id": "FR-14",
    "score": 14.59,
    "extrait": "Le contrat à durée indéterminée prend fin par l’expiration du délai de préavis.",
    "surligner": [
     "contrat",
     "durée",
     "indéterminée",
     "préavis"
    ],
    "version_alignee": {
     "langue": "ar",
     "disponible": true,
     "article_id": "AR-14",
     "article": "14",
     "page": "14",
     "texte": "الفصل 14 (نقح بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- ينتهي عقد الشغل المبرم لمدة معينة بانتهاء المدة المتفق عليها أو بإتمام والعقد المبرم لمدة غير معينة ينتهي بانتهاء أجل الإعلام بإنهاء العمل. كما ينتهى عقد الشغل سواء كان مبرما لمدة معينة أو لمدة غير معينة : أ) باتفاق الطرفين ب) بإرادة أحد الطرفين تبعا لارتكاب خطإ فادح من الطرف الآخر ج) عند تعذر الإنجاز الناتج إما عن أمر طارئ أو قوة قاهرة حدثت قبل أو أثناء تنفيذ العقد أو عن وفاة العامل, د) بالفسخ المصرح به من طرف القاضي في الصور التي يُبِيَنها القانون, ه) في الحالات الأخرى التى ينص عليها القانون."
    }
   },
   {
    "article": "6",
    "texte": "Article 6-2 (Ajouté par la loi n° 96-62 du 15 juillet 1996).- Le contrat de travail est conclu pour une durée indéterminée ou pour une durée déterminée. Le contrat de travail à durée déterminée peut comporter une limitation de la durée de son exécution ou l’indication du travail dont l’accomplissement met fin au contrat.",
    "page": "282",
    "ligne": 11,
    "article_id": "FR-6",
    "score": 11.89,
    "extrait": "Article 6-2 (Ajouté par la loi n° 96-62 du 15 juillet 1996).- Le contrat de travail est conclu pour une durée indéterminée ou pour une durée déterminée.",
    "surligner": [
     "contrat",
     "durée",
     "indéterminée"
    ],
    "version_alignee": {
     "langue": "ar",
     "disponible": true,
     "article_id": "AR-6-2",
     "article": "6",
     "page": "12",
     "texte": "الفصل 6 - 2 (أضيف بالقانون عدد 62 لسنة 1996 المؤرخ في 15 جويلية 1996).- يبرم عقد الشغل لمدة غير معيّنة أو لمدة معيّنة. ويمكن أن يتضمن عقد الشغل لمدة معيّنة تحديدا لفترة زمنية لتنفيذه أو تعبينا للعمل الذي ينتهي العقد بإنجازه."
    }
   }
  ],
  "latence_ms": 4.113
 },
 "ar": {
  "question_originale": "ما هي مدة الاعلام بانهاء عقد الشغلل؟",
  "question_corrigee": "ما هي مدة الاعلام بانهاء عقد الشغل؟",
  "corrections": [
   {
    "type": "orthographe",
    "avant": "الشغلل",
    "apres": "الشغل"
   }
  ],
  "langue": "ar",
  "langue_detectee": "ar",
  "etapes": [
   {
    "etape": "1. langue",
    "sortie": "ar"
   },
   {
    "etape": "2. translittération arabizi",
    "sortie": "ما هي مدة الاعلام بانهاء عقد الشغلل؟"
   },
   {
    "etape": "3. mots vides",
    "sortie": "مدة الاعلام بانهاء عقد الشغلل"
   },
   {
    "etape": "4. normalisation",
    "sortie": "مده الاعلام بانهاء عقد الشغلل"
   },
   {
    "etape": "5. lexique tunisien et sigles",
    "sortie": "مده الاعلام بانهاء عقد الشغلل"
   },
   {
    "etape": "6. racinisation arabe",
    "sortie": "مده اعلام انهاء عقد شغلل"
   },
   {
    "etape": "7. correction SymSpell",
    "sortie": "مده اعلام انهاء عقد شغل"
   },
   {
    "etape": "8. synonymes",
    "sortie": "مده اعلام انهاء عقد شغل"
   }
  ],
  "synonymes_ajoutes": [],
  "abstention": false,
  "candidats": [
   {
    "article": "14 bis",
    "texte": "الفصل 14 مكرر (أضيف بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- يتم الإعلام بإنهاء عقد الشغل المبرم لمدة غير معينة برسالة مضمونة الوصول توجه إلى الطرف الآخر قبل شهر من إنهاء العقد. ويرخص للعملة بالتغيب كامل النصف الثاني من مدّة أجل الإعلام ليتسنى لهم السعي للحصول على شغل آخر. وتعتبر مدة التغيب عملا فعليا ولا ينجر عنه أي وكل هذا لا يمس بالمقتضيات الأكثر فائدة للعامل والناتجة عن أحكام خاصة تضمنها اتفاق الطرفين أو الاتفاقية المشتركة أو العرف.",
    "page": "14",
    "ligne": 18,
    "article_id": "AR-14-مكرر",
    "score": 15.26,
    "extrait": "الفصل 14 مكرر (أضيف بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- يتم الإعلام بإنهاء عقد الشغل المبرم لمدة غير معينة برسالة مضمونة الوصول توجه إلى الطرف الآخر قبل شهر من إنهاء العقد.",
    "surligner": [
     "إنهاء",
     "الإعلام",
     "الشغل",
     "العقد",
     "بإنهاء",
     "شغل",
     "عقد",
     "لمدة",
     "مدة"
    ],
    "version_alignee": {
     "langue": "fr",
     "disponible": true,
     "article_id": "FR-14",
     "article": "14 bis",
     "page": "279",
     "texte": "Article 14 bis. (Ajouté par la loi n° 94-29 du 21 février 1994).- Le préavis de rupture du contrat de travail à durée indéterminée est notifié par lettre recommandée adressée à l’autre partie un mois avant la rupture du contrat. Les travailleurs sont autorisés à s’absenter durant toute la deuxième moitié de la durée du préavis en vue de leur permettre de chercher un autre emploi. La durée d’absence est considérée comme travail effectif et n’entraîne aucune réduction de salaires ou d’indemnités. Le tout sans préjudice des prescriptions plus avantageuses pour le travailleur résultant de dispositions spéciales prévues par l’accord des parties, la convention collective ou l’usage."
    }
   },
   {
    "article": "14",
    "texte": "الفصل 14 (نقح بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- ينتهي عقد الشغل المبرم لمدة معينة بانتهاء المدة المتفق عليها أو بإتمام والعقد المبرم لمدة غير معينة ينتهي بانتهاء أجل الإعلام بإنهاء العمل. كما ينتهى عقد الشغل سواء كان مبرما لمدة معينة أو لمدة غير معينة : أ) باتفاق الطرفين ب) بإرادة أحد الطرفين تبعا لارتكاب خطإ فادح من الطرف الآخر ج) عند تعذر الإنجاز الناتج إما عن أمر طارئ أو قوة قاهرة حدثت قبل أو أثناء تنفيذ العقد أو عن وفاة العامل, د) بالفسخ المصرح به من طرف القاضي في الصور التي يُبِيَنها القانون, ه) في الحالات الأخرى التى ينص عليها القانون.",
    "page": "14",
    "ligne": 17,
    "article_id": "AR-14",
    "score": 12.81,
    "extrait": "الفصل 14 (نقح بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- ينتهي عقد الشغل المبرم لمدة معينة بانتهاء المدة المتفق عليها أو بإتمام والعقد المبرم لمدة غير معينة ينتهي بانتهاء أجل الإعلام بإنهاء العمل.",
    "surligner": [
     "الإعلام",
     "الشغل",
     "العقد",
     "المدة",
     "بإنهاء",
     "عقد",
     "لمدة",
     "والعقد"
    ],
    "version_alignee": {
     "langue": "fr",
     "disponible": true,
     "article_id": "FR-14",
     "article": "14",
     "page": "279",
     "texte": "Article 14.- (Modifié par la loi n° 94-29 du 21 février 1994). .- Le contrat de travail à durée déterminée prend fin par l’expiration de la durée convenue ou par l’accomplissement du travail objet du contrat. Le contrat à durée indéterminée prend fin par l’expiration du délai de préavis. Le contrat de travail à durée déterminée ou à durée indéterminée prend fin : a) par l’accord des parties; b) par la volonté de l’une des parties suite à une faute grave commise par l’autre partie; c) en cas d’empêchement d’exécution résultant soit d’un cas fortuit ou de force majeure survenu avant ou pendant l’exécution du contrat, soit du décès du travailleur; d) par la résolution prononcée par le juge dans les cas déterminés par la loi; e) dans les autres cas prévus par la loi."
    }
   },
   {
    "article": "23",
    "texte": "الفصل 23 (نقح بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- القطع التعسفي لعقد الشغل من أحد الطرفين يخول المطالبة بغرامة خارجة عن المنحة المستحقة لعدم مراعاة أجل الإعلام بإنهاء العمل أو مكافأة نهاية الخدمة المشار إليها بالفصل 22 من هذه المجلة. لا يجوز التخلي مسبقا عن حق المطالبة بغرم الضرر عملا بهذا الفصل. كل دعوى للتحصيل على الغرم من أجل القطع التعسفي لعقد الشغل من أحد الطرفين يجب تقديمها لدى كتابة دائرة الشغل خلال العام الذي يلي القطع وإلا سقطت هذه الدعوى.",
    "page": "21",
    "ligne": 42,
    "article_id": "AR-23",
    "score": 10.3,
    "extrait": "الفصل 23 (نقح بالقانون عدد 29 لسنة 1994 المؤرخ في 21 فيفري 1994).- القطع التعسفي لعقد الشغل من أحد الطرفين يخول المطالبة بغرامة خارجة عن المنحة المستحقة لعدم مراعاة أجل الإعلام بإنهاء العمل أو مكافأة نهاية الخدمة المشار إليها بالفصل 22 من هذه المجلة.",
    "surligner": [
     "الإعلام",
     "الشغل",
     "بإنهاء",
     "لعقد"
    ],
    "version_alignee": {
     "langue": "fr",
     "disponible": true,
     "article_id": "FR-23",
     "article": "23",
     "page": "271",
     "texte": "Article 23 (Modifié par la loi n° 94-29 du 21 février 1994).- La rupture abusive du contrat du travail par l’une des parties ouvre droit à des dommages-intérêts qui ne se confondent pas avec l’indemnité due pour inobservation du délai de préavis ou avec la gratification de fin de service visée à l’article 22 du présent code. Il n’est pas permis de renoncer préalablement au droit éventuel de demander des dommages-intérêts en vertu du présent article. Toute demande en vue d’obtenir des dommages-intérêts pour rupture abusive du contrat de travail par l’une des parties doit être, à peine de déchéance, introduite auprès du greffe du conseil de prud’hommes dans l’année qui suit la rupture."
    }
   }
  ],
  "latence_ms": 5.829
 }
};
