import asyncio
import json
from datetime import date, timedelta
from playwright.async_api import async_playwright

# URL de base pour la liste des cinémas (Lyon dans ton cas)
BASE_URL = "https://www.allocine.fr/salle/cinema/ville-113315/"
BASE_DOMAIN = "https://www.allocine.fr"

async def scrape_allocine():
    # 1. Calculer la date de demain
    tomorrow = date.today() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y-%m-%d")
    print(f"--- Lancement du scraper pour la date du : {date_str} ---")

    results = []

    async with async_playwright() as p:
        # Lancement du navigateur (headless=True pour serveur)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Bloquer les images et les polices pour aller plus vite
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font"] else route.continue_())

        # 2. Récupérer la liste des cinémas
        print(f"Récupération de la liste des cinémas sur : {BASE_URL}")
        await page.goto(BASE_URL, timeout=60000)
        
        # Gestion de la bannière cookies (si elle apparait)
        try:
            await page.get_by_role("button", name="Accepter").click(timeout=3000)
            print("Cookies acceptés.")
        except:
            pass

        # Sélecteur pour les liens des cinémas sur la page ville
        # Note : Les classes Allociné changent parfois. On cible les liens dans les h2 de cartes.
        cinema_links = await page.locator("h2.j_entity_title a").all()
        
        cinemas_to_scrape = []
        for link in cinema_links:
            url = await link.get_attribute("href")
            name = await link.inner_text()
            if url:
                full_url = f"{BASE_DOMAIN}{url}"
                cinemas_to_scrape.append({"name": name.strip(), "url": full_url})

        print(f"{len(cinemas_to_scrape)} cinémas trouvés. Début de l'extraction des séances...")

        # 3. Parcourir chaque cinéma
        for cinema in cinemas_to_scrape:
            # Construction de l'URL avec le hash de date
            target_url = f"{cinema['url']}#shwt_date={date_str}"
            print(f"Scraping : {cinema['name']} ({target_url})")

            try:
                await page.goto(target_url, timeout=30000)
                # On attend que le conteneur des films soit chargé
                # C'est crucial pour que le JS prenne en compte la date
                await page.wait_for_load_state("networkidle") 

                cinema_data = {
                    "cinema_name": cinema['name'],
                    "cinema_url": target_url,
                    "scrape_date": date_str,
                    "films": []
                }

                # Récupération des blocs de films
                movie_cards = await page.locator(".movie-card-theater").all()

                for card in movie_cards:
                    film_info = {}
                    
                    # Titre et URL
                    title_el = card.locator(".meta-title-link")
                    if await title_el.count() > 0:
                        film_info["titre"] = await title_el.first.inner_text()
                        href = await title_el.first.get_attribute("href")
                        film_info["url"] = f"{BASE_DOMAIN}{href}" if href else None
                    else:
                        continue # Si pas de titre, on saute

                    # Réalisateur (parfois dans "meta-body-item")
                    director_el = card.locator(".meta-body-direction .dark-grey-link")
                    if await director_el.count() > 0:
                        film_info["realisateur"] = await director_el.first.inner_text()
                    else:
                        film_info["realisateur"] = "Inconnu"

                    # Date de sortie (souvent dans la meta date)
                    date_el = card.locator(".meta-body-info .date")
                    if await date_el.count() > 0:
                        film_info["date_sortie"] = await date_el.first.inner_text()
                    else:
                        film_info["date_sortie"] = "Inconnue"

                    # Séances (Les heures sont souvent dans des boutons ou spans avec la classe showtimes-hour-item-value)
                    # Attention: Allociné a parfois plusieurs formats (VF, VOSTFR). 
                    # Pour simplifier, on prend toutes les heures affichées pour ce film.
                    showtimes = []
                    times_el = await card.locator(".showtimes-hour-item-value").all()
                    for t in times_el:
                        time_text = await t.inner_text()
                        showtimes.append(time_text)
                    
                    film_info["seances"] = showtimes

                    if showtimes: # On ne garde le film que s'il y a des séances
                        cinema_data["films"].append(film_info)

                if cinema_data["films"]:
                    results.append(cinema_data)

            except Exception as e:
                print(f"Erreur sur le cinéma {cinema['name']}: {e}")
                continue

        await browser.close()

    # 4. Sauvegarde en JSON
    with open("programmation_cinema.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("--- Terminé ! Données sauvegardées dans programmation_cinema.json ---")

if __name__ == "__main__":
    asyncio.run(scrape_allocine())
