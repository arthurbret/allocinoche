"""
Script de récupération des séances UGC basé sur les cinémas en base de données.
Ce script récupère uniquement les horaires des séances pour les cinémas UGC déjà présents en DB.
"""
import asyncio
import os
from datetime import date, timedelta
from playwright.async_api import async_playwright
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


async def get_ugc_cinemas_from_db():
    """Récupère la liste des cinémas UGC depuis la base de données"""
    try:
        print("🎬 Récupération des cinémas UGC depuis la base de données...")
        
        # Récupérer d'abord l'ID du groupe UGC
        group_response = supabase.table("groups").select("id").eq("name", "UGC").execute()
        
        if not group_response.data or len(group_response.data) == 0:
            print("❌ Groupe UGC non trouvé dans la base de données")
            print("   💡 Veuillez d'abord exécuter scrape_ugc_cinemas.py")
            return []
        
        group_id = group_response.data[0]["id"]
        print(f"   ✅ Groupe UGC trouvé (ID: {group_id})")
        
        # Récupérer tous les cinémas du groupe UGC
        cinemas_response = supabase.table("cinemas").select("*").eq("group", group_id).execute()
        
        if not cinemas_response.data:
            print("⚠️  Aucun cinéma UGC trouvé dans la base de données")
            return []
        
        cinemas = cinemas_response.data
        print(f"   ✅ {len(cinemas)} cinémas UGC trouvés")
        
        return cinemas
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des cinémas: {e}")
        return []


async def insert_showtimes_to_supabase(cinema_id, movie_title, showtimes):
    """Insère les séances dans Supabase pour un film et un cinéma donnés"""
    try:
        # 1. Créer ou récupérer le film
        movie_response = supabase.table("movies").upsert(
            {"title": movie_title},
            on_conflict="title"
        ).execute()
        
        if not movie_response.data:
            print(f"      ⚠️  Impossible d'insérer le film: {movie_title}")
            return 0
        
        movie_id = movie_response.data[0]["id"]
        
        # 2. Insérer les séances
        inserted_count = 0
        for showtime in showtimes:
            showtime_data = {
                "cinema_id": cinema_id,
                "movie_id": movie_id,
                "showtime_date": showtime.get("date", date.today().isoformat()),
                "time": showtime["time"],
                "details": showtime["details"]
            }
            
            try:
                # Vérifier si la séance existe déjà pour éviter les doublons
                existing = supabase.table("showtimes").select("*").match({
                    "cinema_id": cinema_id,
                    "movie_id": movie_id,
                    "showtime_date": showtime_data["showtime_date"],
                    "time": showtime_data["time"]
                }).execute()
                
                if not existing.data or len(existing.data) == 0:
                    supabase.table("showtimes").insert(showtime_data).execute()
                    inserted_count += 1
                    
            except Exception as e:
                print(f"      ⚠️  Erreur insertion séance: {e}")
        
        return inserted_count
        
    except Exception as e:
        print(f"      ❌ Erreur avec le film {movie_title}: {e}")
        return 0


async def scrape_showtimes_for_cinema(page, cinema, target_dates):
    """
    Scrape les séances pour un cinéma donné sur plusieurs jours.
    Retourne un dictionnaire de films avec leurs horaires.
    """
    
    async def select_date(date_str: str, label_hint: str | None = None) -> bool:
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
        
        # Ensuite essayer avec le label text
        if label_hint:
            try:
                loc = page.get_by_text(label_hint, exact=False)
                if await loc.count() > 0:
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    return True
            except Exception:
                pass
        
        return False
    
    cinema_movies_map = {}
    cinema_url = cinema["url"]
    
    print(f"\n   🎬 {cinema['name']}")
    print(f"      URL: {cinema_url}")
    
    try:
        for target_date in target_dates:
            date_str = target_date.isoformat()
            label_hint = ""
            if target_date == date.today():
                label_hint = "AUJOURD'HUI"
            elif target_date == date.today() + timedelta(days=1):
                label_hint = "DEMAIN"
            
            print(f"      📅 {date_str}", end="")
            
            # 1. Navigation vers la page du cinéma
            try:
                await page.goto(cinema_url, wait_until="networkidle", timeout=40000)
            except:
                print(f" (Timeout réseau, on tente l'extraction...)")
            
            # 2. Sélectionner la date
            try:
                selected = await select_date(date_str, label_hint or None)
                if not selected:
                    print(f" ⚠️  Date non sélectionnable, on reste sur la date par défaut")
            except Exception as e:
                print(f" ⚠️  Erreur sélection date: {e}")
            
            # 3. Attendre le chargement
            try:
                await page.wait_for_selector('a.color--dark-blue', timeout=5000)
            except:
                await page.evaluate("window.scrollTo(0, 500)")
                await page.wait_for_timeout(2000)
            
            # 4. Extraction des films et séances
            titles_loc = page.locator('a.color--dark-blue')
            count = await titles_loc.count()
            
            films_extracted = 0
            for i in range(count):
                try:
                    title_item = titles_loc.nth(i)
                    title_text = await title_item.inner_text()
                    
                    # Trouver le container parent avec les boutons de séances
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
                        films_extracted += 1
                
                except Exception:
                    continue
            
            print(f" → {films_extracted} films extraits")
    
    except Exception as e:
        print(f"      ❌ Erreur: {e}")
    
    return cinema_movies_map


async def scrape_ugc_showtimes():
    """
    Scrape les séances pour tous les cinémas UGC en base de données.
    """
    # Configuration
    args = ['--disable-blink-features=AutomationControlled']
    days_ahead = int(os.getenv("UGC_DAYS_AHEAD", "1"))  # par défaut: aujourd'hui + demain
    target_dates = [date.today() + timedelta(days=i) for i in range(days_ahead + 1)]
    
    print(f"📅 Récupération des séances pour {days_ahead + 1} jour(s)")
    print(f"   Dates: {', '.join([d.isoformat() for d in target_dates])}")
    
    # Récupérer les cinémas depuis la DB
    cinemas = await get_ugc_cinemas_from_db()
    
    if not cinemas:
        print("⚠️  Aucun cinéma à traiter")
        return
    
    # Scraping
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=args)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Gestion des cookies
        try:
            await page.goto("https://www.ugc.fr", wait_until="domcontentloaded")
            cookie_btn = page.locator('.hagreed__continue')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
                print("✅ Cookies acceptés\n")
        except:
            pass
        
        total_showtimes = 0
        
        # Traiter chaque cinéma
        for i, cinema in enumerate(cinemas):
            print(f"\n[{i+1}/{len(cinemas)}] {cinema['name']}")
            
            # Scraper les séances
            movies_map = await scrape_showtimes_for_cinema(page, cinema, target_dates)
            
            # Insérer dans la base de données
            if movies_map:
                print(f"      💾 Insertion en base de données...")
                cinema_total = 0
                for movie_title, showtimes in movies_map.items():
                    inserted = await insert_showtimes_to_supabase(cinema["id"], movie_title, showtimes)
                    cinema_total += inserted
                
                print(f"      ✅ {cinema_total} séances insérées")
                total_showtimes += cinema_total
            else:
                print(f"      ⚠️  Aucune séance trouvée")
        
        await browser.close()
        
        print(f"\n" + "=" * 60)
        print(f"✅ TOTAL: {total_showtimes} séances insérées")
        print("=" * 60)


async def main():
    """Fonction principale"""
    print("=" * 60)
    print("🎬 SCRAPER DES SÉANCES UGC")
    print("=" * 60)
    
    await scrape_ugc_showtimes()
    
    print("\n✅ TERMINÉ !")


if __name__ == "__main__":
    asyncio.run(main())
