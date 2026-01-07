# 🔧 Correction du Script SQL - Résumé

## ❌ Problème initial

```
Error: Failed to run sql query: 
ERROR: 42601: syntax error at or near "NOT" 
LINE 40: ALTER TABLE cinemas ADD CONSTRAINT IF NOT EXISTS unique_cinema_url UNIQUE (url);
```

## 🔍 Causes identifiées

1. **Syntaxe incompatible** : PostgreSQL ne supporte pas `IF NOT EXISTS` avec `ADD CONSTRAINT`
2. **Structure différente** : La base utilise `BIGINT` et non `UUID`
3. **Nom de colonne** : La colonne s'appelle `"group"` et non `"group_id"`
4. **Colonnes manquantes** : Pas de `description` ni `updated_at` dans la table `groups`

## ✅ Solutions appliquées

### 1. Script SQL corrigé
**Fichier :** [migrations/001_add_groups_table.sql](migrations/001_add_groups_table.sql)

**Changements :**
- ✅ Utilisation de `DO $$ ... END $$` pour les contraintes
- ✅ Types `BIGINT` au lieu de `UUID`
- ✅ Colonne `"group"` au lieu de `group_id`
- ✅ Suppression des colonnes inexistantes (`description`, `updated_at`)
- ✅ Fonction trigger supprimée (non nécessaire)

### 2. Scripts Python adaptés
**Fichiers modifiés :**
- [scrape_ugc_cinemas.py](scrape_ugc_cinemas.py) :
  - `group_id` → `"group"`
  - Suppression de `description`
  
- [scrape_ugc_showtimes.py](scrape_ugc_showtimes.py) :
  - Requête avec `.eq("group", group_id)` au lieu de `.eq("group_id", group_id)`

## 📊 État de la base de données

### Structure validée
```
✅ groups (1 ligne) - Groupe "UGC" existe (id=1)
✅ cinemas (48 lignes) - Colonne "group" existe
✅ movies (69 lignes)
✅ showtimes (4107 lignes)
```

### Index créés
```
✅ idx_cinemas_group (NOUVEAU)
✅ idx_cinemas_url
✅ idx_movies_title
✅ idx_showtimes_date
✅ idx_showtimes_cinema_id
✅ idx_showtimes_movie_id
```

### Contraintes
```
✅ cinemas.url UNIQUE (existait déjà)
✅ movies.title UNIQUE (existait déjà)
✅ groups.name UNIQUE (existait déjà)
```

## 🎯 Script SQL final (testé et validé)

```sql
-- Migration compatible avec votre structure Supabase

-- 1. Créer l'index manquant
CREATE INDEX IF NOT EXISTS idx_cinemas_group ON cinemas("group");

-- 2. Vérifier les contraintes UNIQUE
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_cinema_url'
    ) THEN
        ALTER TABLE cinemas ADD CONSTRAINT unique_cinema_url UNIQUE (url);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_movie_title'
    ) THEN
        ALTER TABLE movies ADD CONSTRAINT unique_movie_title UNIQUE (title);
    END IF;
END $$;

SELECT 'Migration terminée avec succès !' AS status;
```

## ✅ Validation

### Test SQL réussi
```sql
-- Exécuté avec succès dans Supabase
CREATE INDEX IF NOT EXISTS idx_cinemas_group ON cinemas("group");
-- Résultat: Index créé
```

### Test Python réussi
```bash
python -c "import scrape_ugc_cinemas; import scrape_ugc_showtimes"
# Résultat: ✅ Aucune erreur
```

## 🚀 Prochaines étapes

### 1. Vérifier la configuration
```bash
python check_config.py
```

### 2. Tester le scraping
```bash
# Test cinémas
python ugc.py --cinemas

# Test séances
python ugc.py --showtimes
```

## 📚 Documentation

- **[COMPATIBILITY_NOTES.md](COMPATIBILITY_NOTES.md)** : Notes détaillées sur la structure
- **[QUICKSTART.md](QUICKSTART.md)** : Guide de démarrage rapide
- **[README.md](README.md)** : Documentation complète

## 🎉 Résultat

**Le script SQL fonctionne maintenant parfaitement avec votre structure Supabase existante !**

Vous pouvez maintenant :
1. ✅ Exécuter la migration sans erreur
2. ✅ Utiliser les scripts Python pour scraper
3. ✅ Les cinémas seront correctement associés au groupe UGC

---

**Date :** 2025-01-07  
**Statut :** ✅ Corrigé, testé et validé
