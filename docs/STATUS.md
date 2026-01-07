# AllocINoche - État du projet

## ✅ Réalisations

### Architecture modulaire
- ✅ Structure `scrapers/` avec base classes abstraites
- ✅ `BaseCinemasScraper` et `BaseShowtimesScraper` 
- ✅ `DatabaseManager` centralisé avec déduplication des films
- ✅ Orchestrateur `main.py` multi-réseaux
- ✅ Support de la CLI avec `--network`, `--cinemas`, `--showtimes`, `--all`

### Réseau UGC
- ✅ `UGCCinemasScraper` fonctionnel (48 cinémas récupérés)
- ✅ `UGCShowtimesScraper` implémenté
- ✅ Association au groupe "UGC" dans la base de données
- ✅ Gestion des cookies automatique
- ✅ Extraction complète : nom, adresse, ville, URL

### Base de données
- ✅ Table `groups` créée
- ✅ Colonne `group` ajoutée à `cinemas` (référence à `groups.id`)
- ✅ Migrations SQL fonctionnelles sur Supabase
- ✅ Déduplication des films via `upsert_movie()` avec `on_conflict="title"`
- ✅ Insertion en batch des séances pour performance

### API
- ✅ FastAPI opérationnelle
- ✅ Endpoints `/cinemas`, `/movies`, `/showtimes`
- ✅ Fichier `requirements.txt` à jour

## 🚧 En cours / À faire

### Réseau Pathé Gaumont
- ⚠️ Site www.pathe.fr bloqué par protections Akamai
- 📄 Documentation créée : `docs/PATHE_STATUS.md`
- 💡 Squelette de code prêt dans `scrapers/pathe/`
- 🔍 Nécessite :
  - Accès à une API non documentée
  - Ou attente de résolution des problèmes serveur
  - Ou utilisation de proxies/services anti-bot

### Tests et validation
- ⏳ Test complet du scraping UGC séances (en cours, très long)
- 📋 Vérification de la déduplication des films
- 🧪 Tests unitaires à créer (optionnel)

### Nettoyage
- 🗑️ Supprimer les anciens fichiers dépréciés :
  - `ugc.py`
  - `scrape_ugc_cinemas.py`
  - `scrape_ugc_showtimes.py`
  - `explore_pathe.py`
  - `explore_pathe_network.py`

### Documentation
- 📝 README principal à mettre à jour
- 📚 Guide d'utilisation des commandes
- 🔧 Documentation technique des scrapers

## 🎯 Prochaines étapes recommandées

### Court terme (aujourd'hui)
1. Valider que le scraping UGC complet fonctionne (cinemas + showtimes)
2. Vérifier dans Supabase que les données sont correctement insérées
3. Tester l'API pour récupérer les données

### Moyen terme (cette semaine)
1. Explorer les options pour Pathé Gaumont :
   - Rechercher une API mobile
   - Contacter Pathé pour accès officiel
   - Tester avec service anti-bot professionnel
2. Ajouter d'autres réseaux (MK2, Cinéville, etc.)
3. Créer un système de scheduling (cron jobs)

### Long terme
1. Monitoring et alertes en cas d'échec
2. Cache des données pour réduire la charge
3. Dashboard d'administration
4. Application mobile/web pour les utilisateurs finaux

## 📊 Statistiques

- **Cinémas UGC** : 48
- **Groupes configurés** : 1 (UGC)
- **Réseaux prêts** : 1/2 (UGC opérationnel, Pathé en attente)
- **Temps de scraping cinémas** : ~2 minutes
- **Temps de scraping séances** : ~10-15 minutes (estimation)

## 🔥 Points d'attention

1. **Déduplication des films** : Le système utilise uniquement le `title` pour détecter les doublons. Si deux films différents ont le même titre, ils seront fusionnés. Solution possible : ajouter un champ `year` ou `imdb_id`.

2. **Performance** : Le scraping des séances est lent car il visite chaque cinéma individuellement. Optimisations possibles :
   - Scraping parallèle avec asyncio
   - Limitation aux cinémas d'une région
   - Cache des résultats

3. **Robustesse** : Les sélecteurs CSS peuvent changer si le site UGC est mis à jour. Prévoir un système de monitoring.

4. **Pathé** : Bloqué pour l'instant, nécessite une solution technique ou un contact commercial.
