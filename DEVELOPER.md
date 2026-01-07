# Documentation Développeur - AllocinoChe

## 🏗️ Architecture du système

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrateur (ugc.py)                   │
│                                                               │
│  ┌──────────────┐         ┌───────────────────────────┐    │
│  │   --cinemas  │────────▶│  scrape_ugc_cinemas.py    │    │
│  └──────────────┘         └───────────────────────────┘    │
│                                       │                       │
│  ┌──────────────┐                    ▼                       │
│  │ --showtimes  │          ┌─────────────────┐              │
│  └──────────────┘───────┐  │  Supabase DB   │              │
│                          │  │   (groups)      │              │
│  ┌──────────────┐        │  │   (cinemas)    │              │
│  │    --all     │────────┼─▶│   (movies)     │              │
│  └──────────────┘        │  │   (showtimes)  │              │
│                          │  └─────────────────┘              │
│                          │           ▲                        │
│                          └───────────┤                        │
│                                      │                        │
│                        ┌─────────────┴─────────────┐         │
│                        │  scrape_ugc_showtimes.py  │         │
│                        └───────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘

                                │
                                ▼
                    ┌───────────────────────┐
                    │      API (api.py)     │
                    │   FastAPI + Uvicorn   │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Clients (Web/App)   │
                    └───────────────────────┘
```

### Flux de données

#### 1. Récupération des cinémas
```
Site UGC → Playwright → scrape_ugc_cinemas.py → Supabase (groups + cinemas)
```

#### 2. Récupération des séances
```
Supabase (cinemas) → scrape_ugc_showtimes.py → Site UGC → Playwright → Supabase (movies + showtimes)
```

#### 3. Consultation des données
```
Client → FastAPI → Supabase → JSON Response
```

## 📂 Structure des fichiers

```
allocinoche/
├── ugc.py                      # Orchestrateur principal
├── scrape_ugc_cinemas.py       # Scraper des cinémas
├── scrape_ugc_showtimes.py     # Scraper des séances
├── api.py                      # API FastAPI
├── check_config.py             # Script de vérification
├── requirements.txt            # Dépendances Python
├── .env.example                # Template des variables d'env
├── .gitignore                  # Fichiers à ignorer
├── README.md                   # Documentation utilisateur
├── MIGRATION_GUIDE.md          # Guide de migration
├── DEVELOPER.md                # Cette documentation
├── migrations/
│   └── 001_add_groups_table.sql  # Migration SQL
└── .github/
    └── workflows/
        └── scrape.yml          # GitHub Actions workflow
```

## 🗄️ Schéma de base de données

### Table `groups`
Représente les réseaux de cinémas (UGC, Pathé, Gaumont, etc.)

```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Index :**
- `PRIMARY KEY (id)`
- `UNIQUE (name)`

### Table `cinemas`
Représente les cinémas individuels

```sql
CREATE TABLE cinemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    url VARCHAR(255) UNIQUE NOT NULL,
    group_id UUID REFERENCES groups(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Index :**
- `PRIMARY KEY (id)`
- `UNIQUE (url)`
- `INDEX (group_id)`

### Table `movies`
Représente les films

```sql
CREATE TABLE movies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Index :**
- `PRIMARY KEY (id)`
- `UNIQUE (title)`

### Table `showtimes`
Représente les séances

```sql
CREATE TABLE showtimes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cinema_id UUID REFERENCES cinemas(id) NOT NULL,
    movie_id UUID REFERENCES movies(id) NOT NULL,
    showtime_date DATE NOT NULL,
    time VARCHAR(10) NOT NULL,
    details VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Index :**
- `PRIMARY KEY (id)`
- `INDEX (cinema_id)`
- `INDEX (movie_id)`
- `INDEX (showtime_date)`

### Relations

```
groups (1) ──< (N) cinemas
cinemas (1) ──< (N) showtimes
movies (1) ──< (N) showtimes
```

## 🔧 API Endpoints

### `GET /health`
Vérification de l'état de l'API

**Réponse :**
```json
{
  "status": "ok"
}
```

### `GET /showtimes`
Liste des séances avec filtres

**Paramètres :**
- `day` (optionnel) : Date au format YYYY-MM-DD
- `cinema_id` (optionnel) : ID du cinéma

**Exemple :**
```bash
curl "http://localhost:8000/showtimes?day=2025-01-07&cinema_id=123"
```

**Réponse :**
```json
[
  {
    "id": 1,
    "showtime_date": "2025-01-07",
    "time": "20:30",
    "details": "IMAX 3D",
    "cinema": {
      "id": 123,
      "name": "UGC Ciné Cité Les Halles",
      "address": "7 Place de la Rotonde, 75001 Paris",
      "url": "https://www.ugc.fr/cinema.html?id=..."
    },
    "movie": {
      "id": 456,
      "title": "Dune: Part Two"
    }
  }
]
```

## 🛠️ Fonctions principales

### scrape_ugc_cinemas.py

#### `get_or_create_ugc_group()`
Récupère ou crée le groupe UGC dans la base de données.

**Retour :** `group_id` (UUID)

#### `scrape_ugc_cinemas()`
Scrape la liste des cinémas UGC.

**Retour :** Liste de dictionnaires
```python
[
    {
        "name": "UGC Ciné Cité Les Halles",
        "address": "7 Place de la Rotonde, 75001 Paris",
        "url": "https://www.ugc.fr/cinema.html?id=..."
    }
]
```

#### `insert_cinemas_to_supabase(cinemas, group_id)`
Insère ou met à jour les cinémas dans Supabase.

### scrape_ugc_showtimes.py

#### `get_ugc_cinemas_from_db()`
Récupère la liste des cinémas UGC depuis la base de données.

**Retour :** Liste de cinémas (objets Supabase)

#### `scrape_showtimes_for_cinema(page, cinema, target_dates)`
Scrape les séances pour un cinéma donné.

**Paramètres :**
- `page` : Instance Playwright
- `cinema` : Objet cinéma
- `target_dates` : Liste de dates à scraper

**Retour :** Dictionnaire `{titre_film: [séances]}`

#### `insert_showtimes_to_supabase(cinema_id, movie_title, showtimes)`
Insère les séances dans Supabase.

## 🔍 Sélecteurs Playwright

### Site UGC - Sélecteurs importants

```python
# Bouton cookies
'.hagreed__continue'

# Liste des cinémas
'a[data-keywords]'

# Titre du cinéma
'.block--title h1'

# Adresse du cinéma
'p.text-center'

# Sélection de date
'[data-date="YYYY-MM-DD"]'
'button[data-date="YYYY-MM-DD"]'

# Titres de films
'a.color--dark-blue'

# Boutons de séances
'button:has(div.screening-start)'

# Heure de séance
'div.screening-start'

# Détails de séance (IMAX, 3D, etc.)
'div.text-capitalize'
```

## 🧪 Tests

### Tests manuels

```bash
# Vérifier la configuration
python check_config.py

# Tester le scraping des cinémas
python scrape_ugc_cinemas.py

# Tester le scraping des séances
python scrape_ugc_showtimes.py

# Tester l'orchestrateur
python ugc.py --all

# Tester l'API
uvicorn api:app --reload
curl http://localhost:8000/health
curl http://localhost:8000/showtimes
```

### Tests unitaires (à implémenter)

```python
# tests/test_scrape_cinemas.py
def test_get_or_create_ugc_group():
    # Test création du groupe
    pass

def test_scrape_ugc_cinemas():
    # Test scraping avec mock
    pass

# tests/test_scrape_showtimes.py
def test_get_ugc_cinemas_from_db():
    # Test récupération depuis DB
    pass

# tests/test_api.py
def test_health_endpoint():
    # Test endpoint health
    pass

def test_showtimes_endpoint():
    # Test endpoint showtimes
    pass
```

## 🔒 Sécurité

### Variables d'environnement
- ❌ Ne JAMAIS commiter le fichier `.env`
- ✅ Utiliser `.env.example` comme template
- ✅ Stocker les secrets dans GitHub Secrets pour CI/CD

### Rate limiting
- ⚠️ Ajouter des délais entre les requêtes (`page.wait_for_timeout()`)
- ⚠️ Éviter de surcharger le serveur cible

### Headers
```python
# Éviter la détection
args = ['--disable-blink-features=AutomationControlled']
```

## 📈 Performance

### Optimisations actuelles
- ✅ Scraping séparé des cinémas et des séances
- ✅ Utilisation de `networkidle` pour attendre le chargement
- ✅ Upsert pour éviter les doublons
- ✅ Index sur les colonnes de jointure

### Optimisations futures
- [ ] Cache Redis pour l'API
- [ ] Scraping parallèle avec asyncio
- [ ] Compression des réponses API
- [ ] CDN pour les assets statiques

## 🐛 Debugging

### Activer le mode debug Playwright

```python
# Dans scrape_ugc_cinemas.py ou scrape_ugc_showtimes.py
browser = await p.chromium.launch(
    headless=False,  # Voir le navigateur
    slow_mo=1000     # Ralentir les actions
)
```

### Logs détaillés

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Captures d'écran

```python
# Ajouter dans les scripts de scraping
await page.screenshot(path='debug.png')
```

## 🚀 Déploiement

### Serveur local
```bash
# Avec systemd
sudo systemctl start allocinoche-api
sudo systemctl enable allocinoche-api
```

### Docker (à implémenter)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud (Heroku, Railway, etc.)
Voir les configurations spécifiques dans le README.

## 🎯 Roadmap

### Version 2.1
- [ ] Ajout de tests automatisés
- [ ] Dockerisation
- [ ] Interface web de visualisation

### Version 2.2
- [ ] Support Pathé Gaumont
- [ ] API GraphQL
- [ ] Cache Redis

### Version 3.0
- [ ] Multi-réseaux (Pathé, Gaumont, MK2)
- [ ] Système de notifications
- [ ] Application mobile

## 📞 Contact

Pour toute question :
- GitHub Issues
- Pull Requests welcome !

---

**Dernière mise à jour :** 2025-01-07  
**Version :** 2.0
