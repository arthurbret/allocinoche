# ⚠️ Notes de compatibilité - Structure Supabase

## 📋 Structure réelle de votre base de données

Après analyse de votre base Supabase, voici les différences avec la documentation initiale :

### Types de données
- **Utilisation de `BIGINT`** au lieu de `UUID` pour les clés primaires
- Les IDs sont générés avec `IDENTITY` au lieu de `gen_random_uuid()`

### Table `groups`
**Structure actuelle :**
```sql
CREATE TABLE groups (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Différences :**
- ❌ Pas de colonne `description`
- ❌ Pas de colonne `updated_at`

### Table `cinemas`
**Structure actuelle :**
```sql
CREATE TABLE cinemas (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    url TEXT UNIQUE NOT NULL,
    "group" BIGINT REFERENCES groups(id),  -- Note: colonne nommée "group"
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Particularités :**
- ✅ La colonne s'appelle `"group"` (avec guillemets car mot réservé SQL)
- ✅ Pas `group_id` comme dans la doc

### Contraintes et Index existants

**Contraintes UNIQUE :**
- ✅ `cinemas.url` → `cinemas_url_key`
- ✅ `movies.title` → `movies_title_key`
- ✅ `groups.name` → `group_name_key`

**Index de performance :**
- ✅ `idx_cinemas_url`
- ✅ `idx_movies_title`
- ✅ `idx_showtimes_date`
- ✅ `idx_showtimes_cinema_id`
- ✅ `idx_showtimes_movie_id`
- ✅ `idx_cinemas_group` (ajouté par la migration)

## 🔧 Modifications apportées

### 1. Script SQL de migration
**Fichier :** `migrations/001_add_groups_table.sql`

**Corrections :**
- ✅ Utilisation de `BIGINT` au lieu de `UUID`
- ✅ Utilisation de `"group"` au lieu de `group_id`
- ✅ Suppression de la colonne `description`
- ✅ Suppression de la colonne `updated_at`
- ✅ Fix de la syntaxe `ADD CONSTRAINT` (utilisation de `DO $$`)

### 2. Scripts Python

**Fichiers modifiés :**
- `scrape_ugc_cinemas.py`
- `scrape_ugc_showtimes.py`

**Changements :**
- ✅ `group_id` → `"group"` dans les requêtes
- ✅ Suppression de `description` lors de l'insertion

## ✅ État actuel

### Structure validée
```
groups (1 ligne)
├── id: 1
└── name: "UGC"

cinemas (48 lignes)
├── Colonnes: id, name, address, url, "group", created_at, updated_at
└── Index: idx_cinemas_group créé

movies (69 lignes)
showtimes (4107 lignes)
```

## 🚀 Utilisation

### Migration SQL
Le script corrigé est maintenant **idempotent** et **sans erreur** :

```bash
# Dans Supabase SQL Editor
# Copier/coller : migrations/001_add_groups_table.sql
# Exécuter
```

### Scripts Python
Les scripts fonctionnent maintenant avec la structure réelle :

```bash
# Récupérer les cinémas
python ugc.py --cinemas

# Récupérer les séances
python ugc.py --showtimes
```

## 📝 Notes pour les développeurs

### Accès à la colonne group
En SQL :
```sql
SELECT * FROM cinemas WHERE "group" = 1;
```

En Python (Supabase) :
```python
supabase.table("cinemas").select("*").eq("group", group_id).execute()
```

### Création d'un nouveau groupe
```python
supabase.table("groups").insert({"name": "Pathé"}).execute()
```

### Types attendus
- `id` : `int` (pas `str` UUID)
- `"group"` : `int` (référence à `groups.id`)

## ⚠️ Points d'attention

1. **Mot réservé SQL** : La colonne `"group"` est un mot réservé, toujours l'entourer de guillemets doubles en SQL
2. **Types** : Utiliser des `int` pour les IDs, pas des `UUID`
3. **Nom de colonne** : C'est `"group"` et non `"group_id"`

---

**Date :** 2025-01-07  
**Statut :** ✅ Corrigé et validé sur Supabase
