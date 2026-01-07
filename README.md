# AllocinoChe - Système de Scraping UGC

Système de récupération automatisée des cinémas et séances du réseau UGC, avec stockage dans Supabase.

## 📋 Architecture

Le système est maintenant séparé en **deux étapes distinctes** pour une meilleure pérennité :

### 1. Récupération des Cinémas (`scrape_ugc_cinemas.py`)
- Extrait la liste des cinémas UGC depuis le site web
- Récupère les informations (nom, adresse, URL)
- Les associe automatiquement au groupe "UGC" en base de données
- À exécuter occasionnellement (nouveaux cinémas, mises à jour)

### 2. Récupération des Séances (`scrape_ugc_showtimes.py`)
- Lit la liste des cinémas UGC depuis la base de données
- Récupère les horaires de séances pour chaque cinéma
- Insère les films et leurs séances en base
- À exécuter régulièrement (quotidiennement par exemple)

### 3. Orchestrateur (`ugc.py`)
- Point d'entrée principal pour orchestrer les deux étapes
- Permet d'exécuter les scripts séparément ou ensemble

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Installer les navigateurs Playwright
playwright install chromium

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials Supabase
```

## ⚙️ Configuration

Créez un fichier `.env` avec :

```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-api
UGC_DAYS_AHEAD=1  # Nombre de jours à l'avance (0=aujourd'hui, 1=aujourd'hui+demain)
```

## 📊 Structure de la Base de Données

### Table `groups`
- `id`: UUID
- `name`: VARCHAR (ex: "UGC")
- `description`: TEXT

### Table `cinemas`
- `id`: UUID
- `name`: VARCHAR
- `address`: TEXT
- `url`: VARCHAR (unique)
- `group_id`: UUID (foreign key → groups)

### Table `movies`
- `id`: UUID
- `title`: VARCHAR (unique)

### Table `showtimes`
- `id`: UUID
- `cinema_id`: UUID (foreign key → cinemas)
- `movie_id`: UUID (foreign key → movies)
- `showtime_date`: DATE
- `time`: VARCHAR
- `details`: VARCHAR

## 🎯 Utilisation

### Option 1 : Script Orchestrateur (Recommandé)

```bash
# Récupérer tout (cinémas + séances)
python ugc.py --all

# Récupérer uniquement les cinémas
python ugc.py --cinemas

# Récupérer uniquement les séances
python ugc.py --showtimes
```

### Option 2 : Scripts Individuels

```bash
# 1. Récupérer les cinémas (à faire en premier ou occasionnellement)
python scrape_ugc_cinemas.py

# 2. Récupérer les séances (à faire régulièrement)
python scrape_ugc_showtimes.py
```

## 📅 Utilisation Recommandée

### Première exécution
```bash
# Récupérer les cinémas
python ugc.py --cinemas
```

### Mise à jour quotidienne (via cron/scheduler)
```bash
# Récupérer uniquement les séances
python ugc.py --showtimes
```

### Mise à jour complète (mensuelle ou lors d'ajout de nouveaux cinémas)
```bash
# Tout récupérer
python ugc.py --all
```

## 🔄 Workflow Typique

1. **Installation initiale** : Récupérer tous les cinémas
   ```bash
   python ugc.py --cinemas
   ```

2. **Mise à jour quotidienne** : Récupérer les séances
   ```bash
   python ugc.py --showtimes
   ```

3. **Maintenance** : Mettre à jour les cinémas si besoin
   ```bash
   python ugc.py --cinemas
   ```

## 🤖 Automatisation

### Avec Cron (Linux/Mac)

```bash
# Éditer le crontab
crontab -e

# Ajouter une ligne pour exécution quotidienne à 6h du matin
0 6 * * * cd /path/to/allocinoche && /usr/bin/python3 ugc.py --showtimes >> /var/log/ugc_scraping.log 2>&1

# Mise à jour des cinémas le 1er de chaque mois à 3h
0 3 1 * * cd /path/to/allocinoche && /usr/bin/python3 ugc.py --cinemas >> /var/log/ugc_cinemas.log 2>&1
```

### Avec GitHub Actions

```yaml
# .github/workflows/scrape.yml
name: Scrape UGC Showtimes

on:
  schedule:
    - cron: '0 6 * * *'  # Tous les jours à 6h UTC
  workflow_dispatch:      # Permet l'exécution manuelle

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: playwright install chromium
      - run: python ugc.py --showtimes
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

## 🔍 API

Le fichier `api.py` expose une API FastAPI pour interroger les données :

```bash
# Lancer l'API
uvicorn api:app --reload

# Endpoints disponibles
GET /health              # Vérifier l'état de l'API
GET /showtimes           # Liste toutes les séances
GET /showtimes?day=2025-01-15  # Séances pour un jour donné
GET /showtimes?cinema_id=123   # Séances pour un cinéma donné
```

## 🧪 Tests

```bash
# Tester la récupération des cinémas
python scrape_ugc_cinemas.py

# Tester la récupération des séances
python scrape_ugc_showtimes.py

# Vérifier l'API
curl http://localhost:8000/health
curl http://localhost:8000/showtimes
```

## 📝 Avantages de cette Architecture

1. **Séparation des responsabilités** : Les cinémas et les séances sont gérés indépendamment
2. **Performance** : Les séances sont récupérées uniquement pour les cinémas en DB
3. **Flexibilité** : Possibilité d'exécuter chaque partie séparément
4. **Maintenabilité** : Code plus clair et modulaire
5. **Évolutivité** : Facile d'ajouter d'autres réseaux de cinémas (Pathé, Gaumont, etc.)
6. **Pérennité** : Les données restent cohérentes avec la table groups

## 🔮 Évolutions Futures

- [ ] Ajouter d'autres réseaux (Pathé, Gaumont, MK2...)
- [ ] Système de notifications pour nouveaux films
- [ ] Cache des résultats
- [ ] Interface web de consultation
- [ ] Export iCal des séances

## 📄 Licence

MIT
