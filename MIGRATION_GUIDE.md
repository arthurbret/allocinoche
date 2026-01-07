# Guide de Migration - Ancien système → Nouveau système

## 📋 Résumé des changements

### Avant (ancien système)
- **1 script** : `ugc.py` fait tout en une seule fois
- Récupère les cinémas ET les séances à chaque exécution
- Lent et peu optimisé
- Pas de gestion des groupes de cinémas
- Difficile à maintenir

### Après (nouveau système)
- **2 scripts séparés** :
  - `scrape_ugc_cinemas.py` : Récupère uniquement les cinémas
  - `scrape_ugc_showtimes.py` : Récupère uniquement les séances
- **1 orchestrateur** : `ugc.py` coordonne les deux scripts
- Les séances se basent sur les cinémas en DB
- Gestion des groupes de cinémas (table `groups`)
- Plus rapide, plus flexible, plus maintenable

## 🗄️ Modifications de la base de données

### Nouvelle table `groups`
```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Modification de la table `cinemas`
```sql
-- Nouvelle colonne
ALTER TABLE cinemas ADD COLUMN group_id UUID REFERENCES groups(id);
```

## 🚀 Étapes de migration

### Étape 1 : Sauvegarder les données existantes (optionnel)
```bash
# Via l'API Supabase ou l'interface web
# Exporter les tables : cinemas, movies, showtimes
```

### Étape 2 : Mettre à jour la base de données
```bash
# Exécuter le script SQL dans Supabase SQL Editor
# migrations/001_add_groups_table.sql
```

Le script va :
- ✅ Créer la table `groups`
- ✅ Ajouter la colonne `group_id` à `cinemas`
- ✅ Créer le groupe "UGC"
- ✅ Ajouter les index nécessaires

### Étape 3 : Installer les nouvelles dépendances (si nécessaire)
```bash
pip install -r requirements.txt
```

### Étape 4 : Vérifier la configuration
```bash
python check_config.py
```

### Étape 5 : Mettre à jour les cinémas
```bash
# Récupérer les cinémas et les associer au groupe UGC
python ugc.py --cinemas
```

### Étape 6 : Récupérer les séances
```bash
# Récupérer les séances basées sur les cinémas en DB
python ugc.py --showtimes
```

## 🔄 Comparaison des commandes

### Ancien système
```bash
# Une seule commande pour tout
python ugc.py
```

### Nouveau système
```bash
# Récupérer tout (équivalent de l'ancien système)
python ugc.py --all

# OU séparer les opérations (recommandé)
python ugc.py --cinemas     # Une fois ou occasionnellement
python ugc.py --showtimes   # Régulièrement
```

## 📊 Impact sur les données existantes

### Données préservées
- ✅ Tous les cinémas existants restent intacts
- ✅ Tous les films existants restent intacts
- ✅ Toutes les séances existantes restent intactes

### Modifications
- ⚠️ Les cinémas sans `group_id` ne seront pas traités par le nouveau système
- ✅ Solution : Exécuter `python ugc.py --cinemas` pour mettre à jour

## 🔧 Modification des tâches automatisées

### Si vous utilisiez Cron

**Avant :**
```cron
0 6 * * * python /path/to/ugc.py
```

**Après :**
```cron
# Séances tous les jours à 6h
0 6 * * * python /path/to/ugc.py --showtimes

# Cinémas le 1er de chaque mois à 3h
0 3 1 * * python /path/to/ugc.py --cinemas
```

### Si vous utilisiez GitHub Actions

Remplacer votre workflow par le nouveau :
```bash
cp .github/workflows/scrape.yml .github/workflows/scrape.yml
```

## ✅ Vérification post-migration

### 1. Vérifier la structure
```bash
python check_config.py
```

### 2. Vérifier les cinémas
```sql
SELECT 
    c.name,
    g.name as group_name
FROM cinemas c
LEFT JOIN groups g ON c.group_id = g.id
LIMIT 10;
```

### 3. Vérifier les séances
```bash
curl http://localhost:8000/showtimes?day=2025-01-07
```

## 🐛 Résolution de problèmes

### Problème : "Groupe UGC non trouvé"
**Solution :**
```bash
python ugc.py --cinemas
```

### Problème : "Aucun cinéma trouvé"
**Solution :**
```sql
-- Vérifier que les cinémas ont un group_id
SELECT COUNT(*) FROM cinemas WHERE group_id IS NULL;

-- Si nécessaire, réexécuter
python ugc.py --cinemas
```

### Problème : "Table groups n'existe pas"
**Solution :**
```bash
# Exécuter le script de migration SQL
# migrations/001_add_groups_table.sql
```

## 📈 Avantages après migration

1. **Performance** : Les séances sont récupérées 5-10x plus rapidement
2. **Flexibilité** : Possibilité d'ajouter d'autres réseaux facilement
3. **Coûts** : Moins d'appels réseau = moins de coûts
4. **Maintenabilité** : Code plus clair et modulaire
5. **Évolutivité** : Base solide pour ajouter Pathé, Gaumont, etc.

## 🔮 Après la migration

### Usage quotidien recommandé
```bash
# Mise à jour quotidienne des séances
python ugc.py --showtimes
```

### Maintenance mensuelle
```bash
# Mise à jour de la liste des cinémas
python ugc.py --cinemas
```

### Ajout d'un nouveau réseau (futur)
1. Créer `scrape_pathe_cinemas.py`
2. Créer `scrape_pathe_showtimes.py`
3. Le système gérera automatiquement le groupe "Pathé"

## 📞 Support

En cas de problème :
1. Vérifier les logs : `python check_config.py`
2. Consulter le README.md
3. Vérifier les issues GitHub

---

**Date de création :** 2025-01-07  
**Version :** 2.0
