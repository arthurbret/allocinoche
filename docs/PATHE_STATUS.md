# Pathé Gaumont - Documentation technique

## Statut actuel

Le site Pathé (www.pathe.fr) rencontre actuellement des problèmes d'accès qui rendent impossible le scraping direct :
- Page d'erreur "Allo Houston ?" affichée
- Protection anti-bot Akamai très stricte  
- Redirections et erreurs réseau

## Solutions alternatives

### Option 1 : API non documentée (recommandé)
Pathé Gaumont pourrait avoir une API interne utilisée par leur application mobile ou leur site web.
À explorer :
- Application mobile Android/iOS (reverse engineering)
- Requêtes réseau du site web (interception)
- API GraphQL ou REST potentielle

### Option 2 : Attendre la résolution des problèmes serveur
Le site semble avoir des problèmes temporaires. Il faudrait réessayer plus tard.

### Option 3 : Scraping avec rotation de proxies
Utiliser un service de proxies résidentiels pour contourner les blocages Akamai.
- ScraperAPI
- Bright Data
- Oxylabs

### Option 4 : Utiliser une source de données tierce
- AlloCiné API (nécessite un partenariat)
- Google Maps Places API (données limitées)
- CinéObs, Première, etc.

## Architecture préparée

Le code est déjà structuré pour supporter Pathé :
```
scrapers/
├── pathe/
│   ├── __init__.py
│   ├── cinemas.py      # PatheCinemasScraper (squelette)
│   └── showtimes.py    # PatheShowtimesScraper (squelette)
```

Une fois l'accès au site résolu, il suffira d'implémenter les méthodes abstraites :
- `get_cinema_list_url()` : URL de la page listant tous les cinémas
- `extract_cinema_links()` : Extraction des liens vers chaque cinéma
- `extract_cinema_details()` : Extraction nom, adresse, ville depuis la page d'un cinéma
- `select_date()` : Sélection de la date pour les séances
- `extract_movies_and_showtimes()` : Extraction films et horaires

## Recommandation

**Action immédiate** : Implémenter un scraper basé sur l'API mobile Pathé Gaumont si elle existe, sinon attendre que le site soit accessible et utiliser Playwright avec des techniques anti-détection avancées.

Pour le moment, concentrons-nous sur UGC qui fonctionne parfaitement.
