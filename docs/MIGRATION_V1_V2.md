# 🔄 Guide de migration v1 → v2

Ce guide explique la transition de l'ancienne architecture (fichiers `ugc.py`, `scrape_ugc_*.py`) vers la nouvelle architecture modulaire.

## 🎯 Changements majeurs

### Architecture

**Avant (v1)** :
```
ugc.py                      # Script monolithique
scrape_ugc_cinemas.py       # Séparé mais non modulaire
scrape_ugc_showtimes.py     # Séparé mais non modulaire
```

**Après (v2)** :
```
scrapers/
├── common/
│   ├── base.py            # Classes abstraites
│   └── database.py        # Gestion DB centralisée
├── ugc/
│   ├── cinemas.py         # Scraper cinémas UGC
│   └── showtimes.py       # Scraper séances UGC
└── pathe/                  # Préparé pour futur
main.py                     # Orchestrateur multi-réseaux
```

### Commandes

**Avant** :
```bash
# Cinémas
python scrape_ugc_cinemas.py

# Séances
python scrape_ugc_showtimes.py

# Tout
python ugc.py
```

**Après** :
```bash
# Cinémas
python main.py --cinemas --network ugc

# Séances  
python main.py --showtimes --network ugc

# Tout
python main.py --all --network ugc
```

### Base de données

**Nouveau** :
- Table `groups` ajoutée pour les réseaux de cinémas
- Colonne `group` dans `cinemas` pour associer au réseau
- Déduplication automatique des films par titre

**Migration SQL** :
Exécutez le fichier `migrations/001_add_groups_table.sql` dans Supabase SQL Editor.

## 📝 Checklist de migration

### Étape 1 : Backup
```bash
# Sauvegardez votre base de données Supabase
# Dashboard → Database → Backups → Create backup
```

### Étape 2 : Migration DB
```sql
-- Dans Supabase SQL Editor, exécutez :
-- migrations/001_add_groups_table.sql
```

### Étape 3 : Code
```bash
# Récupérez la dernière version
git pull origin v2

# Mettez à jour les dépendances
pip install -r requirements.txt

# Vérifiez la config
cat .env
```

### Étape 4 : Test
```bash
# Testez le nouveau système
python main.py --cinemas --network ugc

# Vérifiez dans Supabase que les données sont correctes
```

### Étape 5 : Nettoyage (optionnel)
```bash
# Supprimez les anciens fichiers
python cleanup_old_files.py
```

## 🆕 Nouvelles fonctionnalités

### 1. Support multi-réseaux
```bash
# UGC
python main.py --all --network ugc

# Pathé (bientôt disponible)
python main.py --all --network pathe
```

### 2. Déduplication automatique
Les films ne sont plus dupliqués dans la base de données :
```python
# Avant : risque de doublons
movie_id = insert_movie("Inception")

# Après : upsert automatique
movie_id = db.upsert_movie("Inception")  # Même ID si existe déjà
```

### 3. Architecture extensible
Ajouter un nouveau réseau est simple :
```python
# scrapers/<reseau>/cinemas.py
class MK2CinemasScraper(BaseCinemasScraper):
    def get_cinema_list_url(self): ...
    def extract_cinema_links(self): ...
    def extract_cinema_details(self): ...
```

### 4. Gestion centralisée DB
```python
# Avant : Code SQL dupliqué partout
from scrapers.common.database import DatabaseManager

db = DatabaseManager()
db.upsert_movie("Inception")
db.batch_insert_showtimes(showtimes)
```

## ⚠️ Points d'attention

### Groupes de cinémas
Tous les cinémas UGC sont maintenant associés au groupe "UGC" :
```sql
SELECT c.name, g.name as group_name
FROM cinemas c
JOIN groups g ON c.group = g.id;
```

### IDs de films changés
Les IDs des films peuvent avoir changé à cause de la déduplication. Si vous avez des références externes, mettez-les à jour.

### Performance
Le nouveau système utilise :
- Insertion en batch pour les séances (plus rapide)
- Upsert pour éviter les doublons (moins d'erreurs)
- Classes réutilisables (moins de code)

## 🐛 Problèmes connus

### "Relation groups does not exist"
→ Vous n'avez pas exécuté la migration SQL. Exécutez `migrations/001_add_groups_table.sql`.

### "Column group does not exist"  
→ Même problème, exécutez la migration.

### Anciennes séances orphelines
Si vous aviez des séances liées à des films dupliqués, elles peuvent pointer vers des IDs inexistants.

**Solution** :
```sql
-- Supprimez les séances orphelines
DELETE FROM showtimes 
WHERE movie_id NOT IN (SELECT id FROM movies);

-- Rescrappez les séances
python main.py --showtimes --network ugc
```

## 📞 Support

En cas de problème :
1. Consultez `docs/STATUS.md` pour l'état actuel
2. Vérifiez les logs de Supabase
3. Ouvrez une issue sur GitHub

## ✅ Validation

Pour vérifier que la migration s'est bien passée :

```bash
# 1. Vérifier les groupes
psql -h <supabase-host> -U postgres -c "SELECT * FROM groups;"

# 2. Vérifier les cinémas
psql -h <supabase-host> -U postgres -c "SELECT name, \"group\" FROM cinemas LIMIT 5;"

# 3. Tester le scraping
python main.py --cinemas --network ugc
```

---

✨ La migration est terminée ! Profitez de la nouvelle architecture modulaire.
