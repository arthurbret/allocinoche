"""
Script d'exploration amélioré du site Pathé avec interception réseau.
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def explore_pathe_network():
    """Explore le site Pathé en interceptant les requêtes réseau"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Capturer les requêtes réseau
        api_calls = []
        
        def handle_response(response):
            url = response.url
            # Capturer les requêtes API
            if 'api' in url or 'json' in url or 'cinema' in url:
                api_calls.append({
                    'url': url,
                    'status': response.status,
                    'method': response.request.method
                })
        
        page.on('response', handle_response)
        
        print("🔍 Exploration avec interception réseau...\n")
        
        # 1. Page des cinémas
        print("1️⃣ Chargement /cinemas...")
        await page.goto("https://www.pathe.fr/cinemas", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print(f"\n📡 Requêtes API capturées ({len(api_calls)}):")
        for call in api_calls[:10]:
            print(f"   {call['method']} {call['status']} - {call['url']}")
        
        # 2. Examiner la structure HTML
        print("\n2️⃣ Structure HTML...")
        
        # Chercher des attributs data-* qui pourraient contenir des infos
        elements_with_data = await page.query_selector_all('[data-cinema], [data-id], [data-slug]')
        print(f"   Éléments avec data-*: {len(elements_with_data)}")
        
        for elem in elements_with_data[:3]:
            attrs = await page.evaluate('el => Array.from(el.attributes).map(a => ({name: a.name, value: a.value}))', elem)
            print(f"      {attrs}")
        
        # 3. Chercher des scripts avec données JSON
        print("\n3️⃣ Scripts JSON...")
        scripts = await page.query_selector_all('script[type="application/json"], script[type="application/ld+json"]')
        print(f"   Scripts JSON trouvés: {len(scripts)}")
        
        for i, script in enumerate(scripts[:2]):
            try:
                content = await script.inner_text()
                data = json.loads(content)
                print(f"\n   Script {i+1}:")
                print(f"      Type: {data.get('@type', 'N/A')}")
                print(f"      Clés: {list(data.keys())[:5]}")
            except:
                pass
        
        # 4. Essayer de cliquer sur un cinéma et intercepter les requêtes
        print("\n4️⃣ Test de navigation vers un cinéma...")
        api_calls.clear()
        
        try:
            # Chercher le premier lien de cinéma
            cinema_link = await page.query_selector('a[href*="/cinemas/cinema-"]')
            if cinema_link:
                href = await cinema_link.get_attribute('href')
                print(f"   Navigation vers: {href}")
                
                await cinema_link.click()
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                print(f"\n📡 Nouvelles requêtes API ({len(api_calls)}):")
                for call in api_calls[:10]:
                    print(f"   {call['method']} {call['status']} - {call['url']}")
                
                # Chercher les horaires
                print("\n   Recherche des horaires...")
                
                # Chercher des boutons/liens qui ressemblent à des horaires
                time_elements = await page.query_selector_all('button, a, span, div')
                potential_times = []
                
                for elem in time_elements:
                    try:
                        text = await elem.inner_text()
                        text = text.strip()
                        # Pattern horaire: XX:XX
                        if text and ':' in text and len(text) <= 10:
                            import re
                            if re.match(r'\d{1,2}:\d{2}', text):
                                potential_times.append(text)
                    except:
                        pass
                
                print(f"   Horaires potentiels trouvés: {len(potential_times)}")
                for time in potential_times[:10]:
                    print(f"      - {time}")
        
        except Exception as e:
            print(f"   Erreur: {e}")
        
        await browser.close()
        print("\n✅ Exploration terminée!")


if __name__ == "__main__":
    asyncio.run(explore_pathe_network())
