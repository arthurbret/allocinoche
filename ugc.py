import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import date, timedelta
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
        print(f"\n📊 Insertion dans Supabase...")
        
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
                            "showtime_date": showtime.get("date", date.today().isoformat()),
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
    days_ahead = int(os.getenv("UGC_DAYS_AHEAD", "1"))  # par défaut: aujourd'hui + demain
    target_dates = [date.today() + timedelta(days=i) for i in range(days_ahead + 1)]

    async def select_date(page, date_str: str, label_hint: str | None = None) -> bool:
        """Essaie de sélectionner une date sur la page cinéma."""
        selectors = [
            f"[data-date='{date_str}']",
            f"button[data-date='{date_str}']",
            f"li[data-date='{date_str}'] button",
            f"button[value='{date_str}']",
        ]
        
        # Essayer d'abord les sélecteurs data-date
        for sel in selectors:
            loc = page.locator(sel)
            if await loc.count() > 0:
                try:
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    return True
                except Exception:
                    continue
        
        # Ensuite essayer avec le label text (méthode plus fiable)
        if label_hint:
            try:
                # Utiliser get_by_text qui gère mieux les caractères spéciaux
                loc = page.get_by_text(label_hint, exact=False)
                if await loc.count() > 0:
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    return True
            except Exception:
                pass
        
        return False

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
                # Accumulate showtimes for all requested dates
                cinema_movies_map = {}
                c_name, c_addr = "Inconnu", ""

                for target_date in target_dates:
                    date_str = target_date.isoformat()
                    label_hint = ""
                    if target_date == date.today():
                        label_hint = "AUJOURD'HUI"
                    elif target_date == date.today() + timedelta(days=1):
                        label_hint = "DEMAIN"

                    # 1. Navigation sécurisée (toujours sur l'URL de base)
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=40000)
                    except:
                        print(f"   (Timeout réseau {date_str}, on tente l'extraction...)")

                    # 1b. Sélectionner la date via l'UI
                    try:
                        selected = await select_date(page, date_str, label_hint or None)
                        if not selected:
                            print(f"   ⚠️  Impossible de sélectionner la date {date_str}, on reste sur la date par défaut")
                    except Exception as e:
                        print(f"   ⚠️  Erreur sélection date {date_str}: {e}")

                    # 2. Vérification chargement
                    try:
                        await page.wait_for_selector('a.color--dark-blue', timeout=5000)
                    except:
                        await page.evaluate("window.scrollTo(0, 500)")
                        await page.wait_for_timeout(2000)

                    # Info Cinéma (on prend la dernière valeur connue)
                    try:
                        c_name = await page.inner_text('.block--title h1')
                        c_addr = await page.inner_text('p.text-center')
                    except:
                        pass

                    # --- EXTRACTION INTELLIGENTE DES FILMS ---
                    titles_loc = page.locator('a.color--dark-blue')
                    count = await titles_loc.count()
                    print(f"   -> {count} titres détectés pour {date_str}.", end="")

                    films_added = 0

                    for i in range(count):
                        try:
                            title_item = titles_loc.nth(i)
                            title_text = await title_item.inner_text()
                            
                            card_found = None
                            buttons_found = []
                            
                            current_parent = title_item
                            for level in range(6):
                                current_parent = current_parent.locator('xpath=..')
                                btns = current_parent.locator('button:has(div.screening-start)')
                                nb_btns = await btns.count()
                                
                                if nb_btns > 0:
                                    card_found = current_parent
                                    buttons_found = btns
                                    break
                            
                            if card_found and await buttons_found.count() > 0:
                                showtimes = []
                                count_b = await buttons_found.count()
                                
                                for j in range(count_b):
                                    btn = buttons_found.nth(j)
                                    time_val = await btn.locator('div.screening-start').inner_text()
                                    info_loc = btn.locator('div.text-capitalize')
                                    info_val = await info_loc.inner_text() if await info_loc.count() > 0 else "Standard"
                                    showtimes.append({
                                        "time": time_val.strip(),
                                        "details": info_val.strip(),
                                        "date": date_str
                                    })
                                
                                key = title_text.strip()
                                if key not in cinema_movies_map:
                                    cinema_movies_map[key] = []
                                cinema_movies_map[key].extend(showtimes)
                                films_added += 1

                        except Exception:
                            continue

                    print(f" -> {films_added} films extraits avec horaires.")

                # Transformation map -> liste
                cinema_movies = [
                    {"title": title, "showtimes": showtimes}
                    for title, showtimes in cinema_movies_map.items()
                ]

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