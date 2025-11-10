# AllocInoché - AlloCiné Cinema Scraper

Un scraper Python pour récupérer les informations des cinémas et séances de films depuis AlloCiné.

## Description

Ce scraper permet de :
- Récupérer la liste de tous les cinémas d'une ville donnée depuis AlloCiné
- Pour chaque cinéma, extraire tous les films à l'affiche pour le lendemain
- Pour chaque film, récupérer :
  - Le titre
  - L'URL de la fiche film
  - La date de sortie
  - Le réalisateur
  - Le genre
  - La durée
  - Toutes les séances disponibles
- Exporter toutes ces données dans un fichier JSON

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/arthurbret/allocinoche.git
cd allocinoche
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Utilisation basique

Pour scraper les cinémas de la ville par défaut (ville-113315) :
```bash
python scraper.py
```

### Utilisation avec une URL personnalisée

Pour scraper une autre ville, passer l'URL en argument :
```bash
python scraper.py "https://www.allocine.fr/salle/cinema/ville-XXXXX/"
```

## Sortie

Le scraper génère un fichier `allocine_data.json` contenant :

```json
{
  "date": "2025-11-11",
  "city_url": "https://www.allocine.fr/salle/cinema/ville-113315/",
  "cinemas": [
    {
      "cinema": "Nom du cinéma",
      "url": "https://www.allocine.fr/seance/salle_gen_csalle=XXXXX.html",
      "date": "2025-11-11",
      "films": [
        {
          "titre": "Titre du film",
          "url": "https://www.allocine.fr/film/fichefilm_gen_cfilm=XXXXX.html",
          "date_sortie": "1 janvier 2025",
          "realisateur": "Nom du réalisateur",
          "genre": "Genre du film",
          "duree": "2h 30min",
          "seances": [
            "14:00",
            "17:30",
            "20:45"
          ]
        }
      ]
    }
  ]
}
```

## Fonctionnalités

- **Date automatique** : Le scraper récupère automatiquement les séances du lendemain
- **Format de date** : Utilise le format `#shwt_date=YYYY-MM-DD` pour cibler les séances du jour souhaité
- **Gestion d'erreurs** : Gère les erreurs de connexion et les pages manquantes
- **User-Agent** : Utilise un User-Agent réaliste pour éviter les blocages
- **Extraction intelligente** : Utilise plusieurs stratégies pour extraire les informations même si la structure HTML varie

## Structure du code

- `scraper.py` : Script principal contenant la classe `AllocineScaper`
  - `get_cinema_list()` : Récupère la liste des cinémas
  - `scrape_cinema_showtimes()` : Scrape les séances d'un cinéma
  - `extract_film_info()` : Extrait les informations d'un film
  - `scrape_all()` : Orchestre le scraping complet
  - `save_to_json()` : Sauvegarde les données en JSON

## Dépendances

- `requests` : Pour les requêtes HTTP
- `beautifulsoup4` : Pour le parsing HTML
- `lxml` : Parser HTML rapide

## Notes

- Le scraper respecte la structure actuelle du site AlloCiné
- Les données sont sauvegardées en UTF-8 pour préserver les accents français
- Le fichier JSON est formaté avec indentation pour faciliter la lecture

## License

MIT