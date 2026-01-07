"""
Script de récupération des cinémas UGC et insertion en base de données.
Ce script extrait uniquement les cinémas du réseau UGC et les associe au groupe UGC.
"""
import asyncio
import os
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


async def get_or_create_ugc_group():
    """Récupère ou crée le groupe UGC dans la table groups"""
    try:
        # Vérifier si le groupe UGC existe
        response = supabase.table("groups").select("*").eq("name", "UGC").execute()
        
        if response.data and len(response.data) > 0:
            group_id = response.data[0]["id"]
            print(f"✅ Groupe UGC trouvé (ID: {group_id})")
            return group_id
        
        # Créer le groupe s'il n'existe pas
        print("📝 Création du groupe UGC...")
        response = supabase.table("groups").insert({
            "name": "UGC"
        }).execute()
        
        if response.data and len(response.data) > 0:
            group_id = response.data[0]["id"]
            print(f"✅ Groupe UGC créé (ID: {group_id})")
            return group_id
        else:
            raise Exception("Impossible de créer le groupe UGC")
            
    except Exception as e:
        print(f"❌ Erreur lors de la gestion du groupe UGC: {e}")
        raise


async def insert_cinemas_to_supabase(cinemas, group_id):
    """Insère les cinémas dans Supabase avec leur association au groupe UGC"""
    try:
        print(f"\n📊 Insertion de {len(cinemas)} cinémas dans Supabase...")
        
        inserted_count = 0
        updated_count = 0
        
        for cinema in cinemas:
            cinema_data = {
                "name": cinema["name"],
                "address": cinema["address"],
                "url": cinema["url"],
                "group": group_id
            }
            
            # Vérifier si le cinéma existe déjà
            existing = supabase.table("cinemas").select("*").eq("url", cinema["url"]).execute()
            
            if existing.data and len(existing.data) > 0:
                # Mise à jour du cinéma existant
                cinema_id = existing.data[0]["id"]
                supabase.table("cinemas").update(cinema_data).eq("id", cinema_id).execute()
                updated_count += 1
                print(f"   ✏️  Mis à jour: {cinema['name']}")
            else:
                # Insertion d'un nouveau cinéma
                response = supabase.table("cinemas").insert(cinema_data).execute()
                if response.data:
                    inserted_count += 1
                    print(f"   ✅ Inséré: {cinema['name']}")
        
        print(f"\n✅ Résumé: {inserted_count} cinémas insérés, {updated_count} mis à jour")
        return inserted_count + updated_count
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des cinémas: {e}")
        raise


async def scrape_ugc_cinemas():
    """
    Scrape la liste des cinémas UGC depuis le site web.
    Retourne une liste de dictionnaires avec les informations des cinémas.
    """
    args = ['--disable-blink-features=AutomationControlled']
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=args)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("🎬 Récupération de l'annuaire des cinémas UGC...")
        await page.goto("https://www.ugc.fr/cinemas.html", wait_until="domcontentloaded")

        # --- GESTION COOKIES ---
        try:
            cookie_btn = page.locator('.hagreed__continue')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
                print("   ✅ Cookies acceptés")
        except:
            pass

        # --- CHARGEMENT COMPLET DE LA LISTE ---
        print("   📜 Chargement de la liste des cinémas...")
        for i in range(5):
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(500)

        # --- EXTRACTION DES LIENS ---
        links = await page.query_selector_all('a[data-keywords]')
        cinemas = []
        unique_urls = set()
        
        for link in links:
            href = await link.get_attribute('href')
            if href:
                # Construire l'URL complète
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = "https://www.ugc.fr" + href
                else:
                    full_url = "https://www.ugc.fr/" + href
                
                # Filtrer uniquement les pages de cinémas
                if "cinema" in full_url and full_url not in unique_urls:
                    unique_urls.add(full_url)
                    
                    # Extraire le nom depuis le lien
                    try:
                        name = await link.inner_text()
                        name = name.strip()
                    except:
                        name = "Cinéma UGC"
                    
                    cinemas.append({
                        "name": name,
                        "url": full_url,
                        "address": ""  # L'adresse sera extraite ultérieurement si nécessaire
                    })

        print(f"   ✅ {len(cinemas)} cinémas UGC trouvés")

        # --- EXTRACTION DÉTAILLÉE (OPTIONNEL) ---
        # On peut visiter chaque page pour extraire l'adresse exacte
        print("\n📍 Extraction des détails de chaque cinéma...")
        for i, cinema in enumerate(cinemas):
            print(f"   [{i+1}/{len(cinemas)}] {cinema['name']}", end="")
            
            try:
                await page.goto(cinema["url"], wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1000)
                
                # Extraire l'adresse
                try:
                    address = await page.inner_text('p.text-center')
                    cinema["address"] = address.strip()
                    print(f" ✅")
                except:
                    print(f" ⚠️  (adresse non trouvée)")
                    
            except Exception as e:
                print(f" ❌ Erreur: {e}")
                continue

        await browser.close()
        
        return cinemas


async def main():
    """Fonction principale"""
    print("=" * 60)
    print("🎬 SCRAPER DES CINÉMAS UGC")
    print("=" * 60)
    
    # 1. Récupérer ou créer le groupe UGC
    group_id = await get_or_create_ugc_group()
    
    # 2. Scraper les cinémas
    cinemas = await scrape_ugc_cinemas()
    
    # 3. Insérer dans Supabase
    if cinemas:
        await insert_cinemas_to_supabase(cinemas, group_id)
    else:
        print("⚠️  Aucun cinéma trouvé")
    
    print("\n" + "=" * 60)
    print("✅ TERMINÉ !")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
