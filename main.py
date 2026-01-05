import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement
load_dotenv()

# Initialiser le client Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Merci de configurer SUPABASE_URL et SUPABASE_KEY dans un fichier .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def insert_into_supabase(results):
    """Insère les données dans Supabase"""
    try:
        # Date du jour pour les séances
        today = date.today().isoformat()
        
        print(f"\n📊 Insertion dans Supabase (date: {today})...")
        
        for cinema in results:
            # 1. Insérer/mettre à jour le cinéma
            cinema_data = {
                "name": cinema["cinema_name"],
                "address": cinema["cinema_address"],
                "url": cinema["url"]
            }
            
            cinema_response = supabase.table("cinemas").upsert(
                cinema_data,
                on_conflict="url"
            ).execute()
            
            cinema_id = cinema_response.data[0]["id"] if cinema_response.data else None
            
            if not cinema_id:
                print(f"   ⚠️  Impossible d'insérer {cinema['cinema_name']}")
                continue
            
            # 2. Insérer les films et les séances
            for movie in cinema["movies"]:
                # Créer ou récupérer le film
                movie_data = {
                    "title": movie["title"]
                }
                
                try:
                    movie_response = supabase.table("movies").upsert(
                        movie_data,
                        on_conflict="title"
                    ).execute()
                    
                    movie_id = movie_response.data[0]["id"] if movie_response.data else None
                    
                    if not movie_id:
                        print(f"   ⚠️  Impossible d'insérer le film {movie['title']}")
                        continue
                    
                    # 3. Insérer les showtimes pour ce film dans ce cinéma
                    for showtime in movie["showtimes"]:
                        showtime_data = {
                            "cinema_id": cinema_id,
                            "movie_id": movie_id,
                            "showtime_date": today,
                            "time": showtime["time"],
                            "details": showtime["details"]
                        }
                        
                        try:
                            supabase.table("showtimes").insert(showtime_data).execute()
                        except Exception as e:
                            print(f"   ⚠️  Erreur insertion séance: {e}")
                
                except Exception as e:
                    print(f"   ⚠️  Erreur avec le film {movie['title']}: {e}")
        
        print("✅ Données insérées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur Supabase: {e}")

async def scrape_ugc_ultimate():
    args = ['--disable-blink-features=AutomationControlled']

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=args)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("1. Récupération de l'annuaire...")
        await page.goto("https://www.ugc.fr/cinemas.html", wait_until="domcontentloaded")

        # --- GESTION COOKIES ---
        try:
            cookie_btn = page.locator('.hagreed__continue')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
        except: pass

        # --- LISTE DES CINÉMAS ---
        print("   -> Chargement de la liste...")
        for _ in range(5):
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(500)

        links = await page.query_selector_all('a[data-keywords]')
        unique_urls = []
        for link in links:
            href = await link.get_attribute('href')
            if href:
                if href.startswith('http'): full = href
                elif href.startswith('/'): full = "https://www.ugc.fr" + href
                else: full = "https://www.ugc.fr/" + href
                if full not in unique_urls and "cinema" in full:
                    unique_urls.append(full)

        print(f"   -> {len(unique_urls)} cinémas à traiter.")

        results = []

        # --- BOUCLE PRINCIPALE ---
        for index, url in enumerate(unique_urls):
            print(f"\n[{index+1}/{len(unique_urls)}] {url}")
            
            try:
                # 1. Navigation sécurisée
                try:
                    await page.goto(url, wait_until="networkidle", timeout=40000)
                except:
                    print("   (Timeout réseau, on tente l'extraction...)")

                # 2. Vérification chargement
                try:
                    await page.wait_for_selector('a.color--dark-blue', timeout=5000)
                except:
                    await page.evaluate("window.scrollTo(0, 500)")
                    await page.wait_for_timeout(2000)

                # Info Cinéma
                try:
                    c_name = await page.inner_text('.block--title h1')
                    c_addr = await page.inner_text('p.text-center')
                except: 
                    c_name, c_addr = "Inconnu", ""

                # --- EXTRACTION INTELLIGENTE DES FILMS ---
                # On repère tous les titres
                titles_loc = page.locator('a.color--dark-blue')
                count = await titles_loc.count()
                
                print(f"   -> {count} titres détectés.", end="")
                
                cinema_movies = []
                films_added = 0

                for i in range(count):
                    try:
                        title_item = titles_loc.nth(i)
                        title_text = await title_item.inner_text()
                        
                        # STRATÉGIE ADAPTATIVE :
                        # On remonte petit à petit jusqu'à trouver un bloc qui contient des boutons
                        # C'est beaucoup plus robuste que "xpath=../../.."
                        card_found = None
                        buttons_found = []
                        
                        # On tente de remonter de 1 à 6 niveaux parents
                        current_parent = title_item
                        for level in range(6):
                            # On remonte d'un cran (xpath=..)
                            current_parent = current_parent.locator('xpath=..')
                            
                            # On regarde si ce parent contient des boutons
                            # On cherche spécifiquement les boutons qui ont une heure (div.screening-start)
                            # pour éviter de cliquer sur des boutons "Voir la fiche" ou autre.
                            btns = current_parent.locator('button:has(div.screening-start)')
                            nb_btns = await btns.count()
                            
                            if nb_btns > 0:
                                card_found = current_parent
                                # On stocke les locators de boutons pour la suite
                                buttons_found = btns
                                break # On a trouvé le bon parent !
                        
                        # Si on a trouvé des boutons valides
                        if card_found and await buttons_found.count() > 0:
                            showtimes = []
                            count_b = await buttons_found.count()
                            
                            for j in range(count_b):
                                btn = buttons_found.nth(j)
                                time_val = await btn.locator('div.screening-start').inner_text()
                                
                                # Gestion optionnelle de la salle/langue
                                info_loc = btn.locator('div.text-capitalize')
                                info_val = await info_loc.inner_text() if await info_loc.count() > 0 else "Standard"
                                
                                showtimes.append({
                                    "time": time_val.strip(),
                                    "details": info_val.strip()
                                })
                            
                            cinema_movies.append({
                                "title": title_text.strip(),
                                "showtimes": showtimes
                            })
                            films_added += 1

                    except Exception as e:
                        continue 

                print(f" -> {films_added} films extraits avec horaires.")
                
                results.append({
                    "cinema_name": c_name.strip(),
                    "cinema_address": c_addr.strip(),
                    "url": url,
                    "movies": cinema_movies
                })

            except Exception as e:
                print(f"   ERREUR: {e}")

        # Sauvegarde locale
        with open('ugc_final_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        # Insérer dans Supabase
        await insert_into_supabase(results)
        
        await browser.close()
        print(f"\n✅ TERMINÉ ! Données sauvegardées en local et dans Supabase")

if __name__ == "__main__":
    asyncio.run(scrape_ugc_ultimate())