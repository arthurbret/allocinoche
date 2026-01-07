"""
Script d'exploration du site Pathé.
Analyse la structure pour implémenter le scraper.
"""
import asyncio
from playwright.async_api import async_playwright


async def explore_pathe():
    """Explore le site Pathé"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True
        )
        page = await context.new_page()
        
        print("🔍 Exploration du site Pathé...")
        
        # 1. Page d'accueil
        print("\n1️⃣ Chargement de la page d'accueil...")
        try:
            await page.goto("https://www.pathe.fr/cinemas", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            print(f"   URL finale: {page.url}")
            
            # Sauvegarder le HTML pour analyse
            html = await page.content()
            print(f"   Taille HTML: {len(html)} caractères")
            
            # Extraire le title
            title = await page.title()
            print(f"   Titre: {title}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            await browser.close()
            return
        
        # 2. Chercher les cinémas
        print("\n2️⃣ Recherche des cinémas...")
        
        # Essayer différents sélecteurs pour les cinémas
        cinema_selectors = [
            'a[href*="/cinemas/"]',
            'a[href*="/cinema/"]',
            '.cinema-card a',
            '[class*="cinema"] a',
            'article a'
        ]
        
        cinema_links = []
        for selector in cinema_selectors:
            links = await page.query_selector_all(selector)
            if links:
                print(f"   Sélecteur '{selector}': {len(links)} liens")
                for link in links[:3]:
                    try:
                        text = await link.inner_text()
                        href = await link.get_attribute('href')
                        print(f"      - {text.strip()[:40]}: {href}")
                        cinema_links.append(href)
                    except:
                        pass
                if cinema_links:
                    break
        
        # 3. Essayer d'aller sur un cinéma spécifique
        if cinema_links:
            test_url = cinema_links[0]
            if not test_url.startswith('http'):
                test_url = f"https://www.pathe.fr{test_url}"
            
            print(f"\n3️⃣ Test sur un cinéma: {test_url}")
            try:
                await page.goto(test_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Cookies
                print("   Gestion des cookies...")
                cookie_selectors = [
                    'button:has-text("Accepter")',
                    'button:has-text("Tout accepter")',
                    'button:has-text("J\'accepte")',
                    '#didomi-notice-agree-button',
                    '.didomi-button',
                    '[id*="accept"]'
                ]
                
                for sel in cookie_selectors:
                    try:
                        btn = page.locator(sel).first
                        if await btn.count() > 0:
                            print(f"      Bouton cookie trouvé: {sel}")
                            await btn.click()
                            await page.wait_for_timeout(1000)
                            break
                    except:
                        pass
                
                # Nom du cinéma
                name_selectors = ['h1', '.cinema-name', '.cinema-title', '[class*="cinema-name"]']
                for sel in name_selectors:
                    try:
                        name = await page.inner_text(sel)
                        print(f"   ✅ Nom du cinéma: {name.strip()}")
                        break
                    except:
                        pass
                
                # Adresse
                address_selectors = ['.address', '.cinema-address', '[class*="address"]', 'address']
                for sel in address_selectors:
                    try:
                        address = await page.inner_text(sel)
                        print(f"   📍 Adresse: {address.strip()}")
                        break
                    except:
                        pass
                
                # Films et horaires
                print("\n   Films affichés:")
                
                # Chercher les films
                movie_selectors = [
                    '[class*="movie"]',
                    '[class*="film"]',
                    'article',
                    '.card'
                ]
                
                for sel in movie_selectors:
                    try:
                        movies = await page.query_selector_all(sel)
                        if movies and len(movies) > 0:
                            print(f"      Sélecteur '{sel}': {len(movies)} films potentiels")
                            
                            # Analyser les 2 premiers films
                            for i, movie in enumerate(movies[:2]):
                                print(f"\n      Film {i+1}:")
                                
                                # Titre
                                title_tags = ['h2', 'h3', 'h4', '[class*="title"]']
                                for tag in title_tags:
                                    try:
                                        title_el = await movie.query_selector(tag)
                                        if title_el:
                                            title = await title_el.inner_text()
                                            print(f"         Titre: {title.strip()}")
                                            break
                                    except:
                                        pass
                                
                                # Horaires
                                time_tags = ['button', 'a', '[class*="time"]', '[class*="seance"]']
                                for tag in time_tags:
                                    try:
                                        times = await movie.query_selector_all(tag)
                                        if times:
                                            print(f"         Horaires potentiels ({tag}): {len(times)}")
                                            for t in times[:3]:
                                                text = await t.inner_text()
                                                if text.strip():
                                                    print(f"            - {text.strip()}")
                                            break
                                    except:
                                        pass
                            break
                    except Exception as e:
                        print(f"      Erreur avec '{sel}': {e}")
            
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        await browser.close()
        print("\n✅ Exploration terminée!")


if __name__ == "__main__":
    asyncio.run(explore_pathe())
