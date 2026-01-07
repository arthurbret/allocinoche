# 🎬 AllocINoche - Agrégateur de séances de cinéma

Plateforme de scraping et d'agrégation des séances de cinéma de plusieurs réseaux français (UGC, Pathé Gaumont, etc.).

## 🚀 Démarrage rapide

### Installation

```bash
# Cloner le repo
git clone <repo-url>
cd allocinoche

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer Playwright
playwright install chromium

# Configuration
cp .env.example .env
# Éditer .env avec vos credentials Supabase
```

### Utilisation

```bash
# Scraper les cinémas UGC
python main.py --cinemas --network ugc

# Scraper les séances UGC
python main.py --showtimes --network ugc

# Scraper tout (cinémas + séances)
python main.py --all --network ugc

# Lancer l'API
uvicorn api:app --reload
```

## 📁 Architecture

```
allocinoche/
├── scrapers/               # Scrapers modulaires par réseau
│   ├── common/
│   │   ├── base.py         # Classes abstraites
│   │   └── database.py     # Gestionnaire DB
│   ├── ugc/
│   │   ├── cinemas.py      # Scraper cinémas UGC
│   │   └── showtimes.py    # Scraper séances UGC
│   └── pathe/
│       ├── cinemas.py      # Scraper cinémas Pathé (TODO)
│       └── showtimes.py    # Scraper séances Pathé (TODO)
├── main.py                 # Orchestrateur principal
├── api.py                  # API FastAPI
└── docs/                   # Documentation
    ├── STATUS.md           # État du projet
    └── PATHE_STATUS.md     # Statut Pathé
```

## 🎯 Fonctionnalités

### ✅ Implémenté

- **Scraping UGC** : 48 cinémas avec séances complètes
- **Base de données Supabase** : Stockage structuré avec groupes et cinémas
- **Déduplication** : Évite les doublons de films
- **API REST** : Endpoints pour cinémas, films, séances
- **Architecture modulaire** : Facile d'ajouter d'autres réseaux

### 🚧 En cours

- **Pathé Gaumont** : Site bloqué, recherche d'alternatives (API mobile, etc.)

### 📋 Prévu

- MK2, Cinéville, Gaumont, autres réseaux
- Système de cache
- Scheduling automatique (cron)
- Dashboard d'administration

## 🔧 Développement

### Ajouter un nouveau réseau

1. Créer le dossier `scrapers/<reseau>/`
2. Implémenter `<Reseau>CinemasScraper(BaseCinemasScraper)`
3. Implémenter `<Reseau>ShowtimesScraper(BaseShowtimesScraper)`
4. Ajouter dans `main.py` SUPPORTED_NETWORKS

Voir [scrapers/ugc/](scrapers/ugc/) pour un exemple complet.

### Méthodes à implémenter

**Pour les cinémas :**
- `get_cinema_list_url()` : URL de la liste des cinémas
- `accept_cookies()` : Gestion des cookies
- `extract_cinema_links()` : Extraction des liens
- `extract_cinema_details()` : Extraction nom, adresse, ville, URL

**Pour les séances :**
- `accept_cookies()` : Gestion des cookies
- `select_date()` : Sélection de la date
- `extract_movies_and_showtimes()` : Extraction films + horaires

## 📊 Base de données

### Tables Supabase

- **groups** : Réseaux de cinémas (UGC, Pathé, etc.)
  - `id` (bigint)
  - `name` (text)
  - `created_at` (timestamp)

- **cinemas** : Salles de cinéma
  - `id` (bigint)
  - `name` (text)
  - `address` (text)
  - `city` (text)
  - `url` (text)
  - `group` (bigint, FK vers groups.id)
  - `created_at`, `updated_at` (timestamp)

- **movies** : Films (dédupliqués par titre)
  - `id` (bigint)
  - `title` (text, unique)
  - `created_at` (timestamp)

- **showtimes** : Séances
  - `id` (bigint)
  - `cinema_id` (bigint, FK vers cinemas.id)
  - `movie_id` (bigint, FK vers movies.id)
  - `showtime` (timestamp)
  - `created_at` (timestamp)

## 🌐 API

### Endpoints

```
GET /cinemas              # Liste tous les cinémas
GET /cinemas/{id}         # Détails d'un cinéma
GET /movies               # Liste tous les films
GET /showtimes            # Liste toutes les séances
GET /showtimes/cinema/{cinema_id}  # Séances d'un cinéma
GET /showtimes/movie/{movie_id}    # Séances d'un film
```

### Exemples

```bash
# Récupérer tous les cinémas
curl http://localhost:8000/cinemas

# Séances d'un cinéma spécifique
curl http://localhost:8000/showtimes/cinema/1

# Tous les films
curl http://localhost:8000/movies
```

## 📝 Limitations connues

1. **Pathé Gaumont** : Actuellement bloqué par protections anti-bot
2. **Déduplication films** : Basée uniquement sur le titre (risque de collision)
3. **Performance** : Scraping séquentiel, peut être lent sur de nombreux cinémas

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 🙏 Remerciements

- UGC pour leur site web structuré
- Supabase pour la base de données
- Playwright pour l'automatisation web

---

**Note** : Ce projet est à but éducatif. Respectez les CGU des sites scrapés et utilisez responsablement.
