# Changelog - AllocinoChe

Tous les changements notables de ce projet seront documentés dans ce fichier.

## [2.0.0] - 2025-01-07

### 🎉 Refonte majeure de l'architecture

#### ✨ Ajouté
- **Nouveau système modulaire** : Séparation de la recherche des cinémas et des séances
- **Script `scrape_ugc_cinemas.py`** : Récupération et gestion des cinémas
- **Script `scrape_ugc_showtimes.py`** : Récupération des séances basée sur les cinémas en DB
- **Table `groups`** : Gestion des réseaux de cinémas (UGC, Pathé, etc.)
- **Colonne `group_id`** dans la table `cinemas` pour lier les cinémas à leur réseau
- **Orchestrateur `ugc.py`** : Point d'entrée unifié avec options `--all`, `--cinemas`, `--showtimes`
- **Script `check_config.py`** : Vérification de la configuration et de la base de données
- **Script `cleanup.py`** : Nettoyage des anciennes séances et films orphelins
- **Migration SQL** : `migrations/001_add_groups_table.sql` pour mettre à jour la structure
- **Documentation complète** :
  - `README.md` : Guide utilisateur
  - `MIGRATION_GUIDE.md` : Guide de migration depuis v1.x
  - `DEVELOPER.md` : Documentation développeur
  - `CHANGELOG.md` : Ce fichier
- **GitHub Actions** : Workflow automatisé pour scraping quotidien/mensuel
- **Fichier `.gitignore`** : Exclusion des fichiers sensibles et temporaires

#### 🔄 Modifié
- **`ugc.py`** : Transformé en orchestrateur avec arguments CLI
- **Architecture** : Passage d'un système monolithique à un système modulaire
- **Performance** : Scraping des séances 5-10x plus rapide

#### 🗑️ Déprécié
- L'ancien mode d'utilisation `python ugc.py` sans arguments est remplacé par `python ugc.py --all`

#### 🔧 Améliorations techniques
- **Index de base de données** : Ajout d'index pour optimiser les requêtes
- **Upsert intelligent** : Évite les doublons pour les cinémas
- **Gestion des erreurs** : Meilleure gestion des timeouts et erreurs réseau
- **Validation** : Vérification de l'existence du groupe UGC avant scraping des séances

### 📊 Impact sur les données

#### Compatibilité
- ✅ Les données existantes (cinémas, films, séances) sont préservées
- ✅ Migration automatique lors de la première exécution
- ⚠️ Nécessite l'exécution du script SQL de migration

#### Structure de la base
```sql
-- Avant v2.0
cinemas (id, name, address, url)

-- Après v2.0
groups (id, name, description)
cinemas (id, name, address, url, group_id)
```

### 🚀 Guide de mise à jour

#### Depuis v1.x
```bash
# 1. Exécuter la migration SQL
# migrations/001_add_groups_table.sql

# 2. Vérifier la configuration
python check_config.py

# 3. Mettre à jour les cinémas
python ugc.py --cinemas

# 4. Récupérer les séances
python ugc.py --showtimes
```

Voir `MIGRATION_GUIDE.md` pour plus de détails.

### 📝 Notes de version

Cette version introduit une **séparation claire des responsabilités** :
- La récupération des cinémas est une opération occasionnelle (mensuelle)
- La récupération des séances est une opération régulière (quotidienne)

Cette architecture permet :
- ⚡ **Performance** : Scraping plus rapide
- 🔧 **Maintenabilité** : Code plus clair et modulaire
- 📈 **Évolutivité** : Facile d'ajouter d'autres réseaux
- 💰 **Coûts** : Moins d'appels réseau

### 🐛 Corrections de bugs
- Meilleure gestion des timeouts Playwright
- Sélection de date plus robuste
- Gestion des caractères spéciaux dans les noms de films

---

## [1.0.0] - 2024-XX-XX

### ✨ Version initiale
- Script de scraping UGC monolithique
- Récupération des cinémas et séances en une seule exécution
- API FastAPI pour consultation des données
- Stockage dans Supabase

---

## Format

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

### Types de changements
- `Ajouté` pour les nouvelles fonctionnalités
- `Modifié` pour les changements aux fonctionnalités existantes
- `Déprécié` pour les fonctionnalités bientôt supprimées
- `Supprimé` pour les fonctionnalités supprimées
- `Corrigé` pour les corrections de bugs
- `Sécurité` pour les vulnérabilités

### Versioning
- **MAJOR** (X.0.0) : Changements incompatibles avec l'API
- **MINOR** (1.X.0) : Ajout de fonctionnalités rétrocompatibles
- **PATCH** (1.0.X) : Corrections de bugs rétrocompatibles
