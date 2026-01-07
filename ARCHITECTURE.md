# 🏗️ Architecture Multi-Réseaux - AllocinoChe v2.5

## 📁 Nouvelle structure

```
allocinoche/
├── scrapers/                    # Module principal de scraping
│   ├── __init__.py
│   ├── common/                  # Code partagé entre tous les scrapers
│   │   ├── __init__.py
│   │   ├── base.py              # Classes abstraites BaseCinemasScraper & BaseShowtimesScraper
│   │   └── database.py          # DatabaseManager (gestion Supabase centralisée)
│   │
│   ├── ugc/                     # Implémentation UGC
│   │   ├── __init__.py
│   │   ├── cinemas.py           # UGCCinemasScraper
│   │   └── showtimes.py         # UGCShowtimesScraper
│   │
│   └── pathe/                   # Implémentation Pathé (squelette)
│       ├── __init__.py
│       ├── cinemas.py           # PatheCinemasScraper (TODO)
│       └── showtimes.py         # PatheShowtimesScraper (TODO)
│
├── main.py                      # Nouvel orchestrateur multi-réseaux
├── ugc.py                       # Ancien orchestrateur (déprécié, à supprimer)
├── scrape_ugc_cinemas.py        # Ancien script (déprécié, à supprimer)
├── scrape_ugc_showtimes.py      # Ancien script (déprécié, à supprimer)
├── api.py
├── check_config.py
├── cleanup.py
└── ...
```

## 🎯 Principes de l'architecture

### 1. **Modularité**
Chaque réseau de cinémas a son propre module (`ugc/`, `pathe/`, etc.)

### 2. **Héritage et abstraction**
Tous les scrapers héritent de classes de base communes :
- `BaseCinemasScraper` : Pour scraper les cinémas
- `BaseShowtimesScraper` : Pour scraper les séances

### 3. **Centralisation**
- `DatabaseManager` : Gestion unique des opérations Supabase
- Évite la duplication de code

### 4. **Extensibilité**
Pour ajouter un nouveau réseau (ex: MK2) :
1. Créer `scrapers/mk2/`
2. Implémenter `MK2CinemasScraper` et `MK2ShowtimesScraper`
3. Ajouter dans `main.py` → `SUPPORTED_NETWORKS`

## 🔧 Classes principales

### `BaseCinemasScraper` (classe abstraite)

**Méthodes à implémenter :**
```python
async def get_cinema_list_url() -> str
    # Retourne l'URL de la page d'annuaire

async def accept_cookies(page: Page) -> None
    # Gère l'acceptation des cookies

async def extract_cinema_links(page: Page) -> List[str]
    # Extrait les URLs des cinémas

async def extract_cinema_details(page: Page, url: str) -> Dict
    # Extrait nom, adresse, URL d'un cinéma
```

**Méthode fournie :**
```python
async def scrape() -> List[Dict[str, Any]]
    # Orchestre tout le processus de scraping
```

### `BaseShowtimesScraper` (classe abstraite)

**Méthodes à implémenter :**
```python
async def accept_cookies(page: Page) -> None
    # Gère l'acceptation des cookies

async def select_date(page: Page, target_date: date) -> bool
    # Sélectionne une date sur la page

async def extract_movies_and_showtimes(page: Page, target_date: date) -> Dict
    # Extrait films et séances pour une date
```

**Méthodes fournies :**
```python
async def scrape_cinema(page, cinema, target_dates) -> Dict
    # Scrape un cinéma pour plusieurs dates

async def scrape(cinemas: List[Dict]) -> Dict
    # Scrape tous les cinémas fournis
```

### `DatabaseManager`

**Méthodes principales :**
```python
get_or_create_group(name: str) -> int
    # Gère les groupes de cinémas

upsert_cinema(cinema_data: Dict) -> Optional[int]
    # Insère ou met à jour un cinéma

get_cinemas_by_group(group_id: int) -> List[Dict]
    # Récupère les cinémas d'un groupe

upsert_movie(title: str) -> Optional[int]
    # Gère les films

batch_insert_showtimes(cinema_id: int, movies_data: Dict) -> int
    # Insère les séances en batch
```

## 🚀 Utilisation

### Commandes principales

```bash
# UGC - Cinémas uniquement
python main.py --cinemas --network ugc

# UGC - Séances uniquement
python main.py --showtimes --network ugc

# UGC - Tout
python main.py --all --network ugc

# Pathé (quand implémenté)
python main.py --all --network pathe
```

### Migration depuis l'ancienne architecture

**Avant :**
```bash
python ugc.py --cinemas
python ugc.py --showtimes
python ugc.py --all
```

**Après :**
```bash
python main.py --cinemas --network ugc
python main.py --showtimes --network ugc
python main.py --all --network ugc
```

## 📝 Ajouter un nouveau réseau

### Exemple : Ajouter MK2

#### 1. Créer la structure
```bash
mkdir -p scrapers/mk2
touch scrapers/mk2/__init__.py
touch scrapers/mk2/cinemas.py
touch scrapers/mk2/showtimes.py
```

#### 2. Implémenter `MK2CinemasScraper`

```python
# scrapers/mk2/cinemas.py
from ..common.base import BaseCinemasScraper

class MK2CinemasScraper(BaseCinemasScraper):
    def __init__(self):
        super().__init__(group_name="MK2")
    
    async def get_cinema_list_url(self) -> str:
        return "https://www.mk2.com/cinemas"
    
    async def accept_cookies(self, page):
        # Implémenter selon le site MK2
        pass
    
    async def extract_cinema_links(self, page):
        # Implémenter selon le site MK2
        pass
    
    async def extract_cinema_details(self, page, url):
        # Implémenter selon le site MK2
        pass
```

#### 3. Implémenter `MK2ShowtimesScraper`

```python
# scrapers/mk2/showtimes.py
from ..common.base import BaseShowtimesScraper

class MK2ShowtimesScraper(BaseShowtimesScraper):
    def __init__(self, days_ahead: int = None):
        super().__init__(group_name="MK2", days_ahead=days_ahead or 1)
    
    async def accept_cookies(self, page):
        # Implémenter
        pass
    
    async def select_date(self, page, target_date):
        # Implémenter
        pass
    
    async def extract_movies_and_showtimes(self, page, target_date):
        # Implémenter
        pass
```

#### 4. Ajouter dans `main.py`

```python
from scrapers.mk2 import MK2CinemasScraper, MK2ShowtimesScraper

SUPPORTED_NETWORKS = {
    'ugc': { ... },
    'pathe': { ... },
    'mk2': {
        'name': 'MK2',
        'cinemas_scraper': MK2CinemasScraper,
        'showtimes_scraper': MK2ShowtimesScraper,
    },
}
```

#### 5. Utiliser
```bash
python main.py --all --network mk2
```

## 🧪 Tests

```bash
# Vérifier les imports
python -c "from scrapers.ugc import UGCCinemasScraper, UGCShowtimesScraper; print('✅ OK')"

# Tester le scraping UGC
python main.py --cinemas --network ugc

# Vérifier l'aide
python main.py --help
```

## 📊 Avantages de cette architecture

| Aspect | Avant | Après |
|--------|-------|-------|
| **Ajout de réseau** | Dupliquer tout le code | Hériter des classes de base |
| **Maintenance** | Modifier chaque script | Modifier une seule classe |
| **Code partagé** | Copié-collé | Centralisé dans `common/` |
| **Tests** | Difficiles | Faciles (classes isolées) |
| **CLI** | Par réseau (`ugc.py`, `pathe.py`) | Unifié (`main.py --network`) |

## 🔮 Prochaines étapes

1. ✅ Architecture créée
2. ✅ UGC migré
3. ⏳ Implémenter Pathé (`scrapers/pathe/`)
4. ⏳ Ajouter d'autres réseaux (MK2, Gaumont, etc.)
5. ⏳ Tests automatisés
6. ⏳ Supprimer les anciens fichiers dépréciés

---

**Version :** 2.5  
**Date :** 2025-01-07  
**Statut :** ✅ Prêt pour développement Pathé
