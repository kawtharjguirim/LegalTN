# Outils de capture et d'audit de contraste (hors application)

Ces scripts servent uniquement à vérifier l'interface. Ils ne font pas partie de LegalTN. Il faut Node 24 et Microsoft Edge.

1. Lancer le serveur : `.\demarrer.ps1 -Port 18765`.
2. Lancer Edge en mode headless, depuis un dossier de travail qui contient un sous-dossier `design/` :
   `msedge --headless=new --remote-debugging-port=9333 --user-data-dir=<dossier temporaire> about:blank`
3. Générer les plans de capture : `node plans.mjs <racine du dépôt> 18765`.

   Cette commande écrit `design/plan_maquettes.json`, `plan_reel.json` et `plan_apres.json`.
4. Faire les captures et l'audit : `node capturer.mjs 9333 design/plan_apres.json <dossier de sortie>`.

   Cette commande écrit les PNG et `audit.json`, qui contient les échecs de contraste AA et l'état de l'interface.

`echantillon.py <port> <questions…>` enregistre des réponses réelles de l'API ; il a servi à produire les données des maquettes.

Arrêter Edge et le serveur après usage.
