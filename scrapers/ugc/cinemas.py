"""
Scraper des cinémas UGC.
Extrait la liste des cinémas depuis https://www.ugc.fr/cinemas.html
"""
from typing import List, Dict, Any
from playwright.async_api import Page
from ..common.base import BaseCinemasScraper


class UGCCinemasScraper(BaseCinemasScraper):
    """Scraper pour les cinémas UGC"""
    
    def __init__(self):
        super().__init__(group_name="UGC")
    
    async def get_cinema_list_url(self) -> str:
        """URL de la page d'annuaire UGC"""
        return "https://www.ugc.fr/cinemas.html"
    
    async def accept_cookies(self, page: Page) -> None:
        """Accepte les cookies sur le site UGC"""
        try:
            cookie_btn = page.locator('.hagreed__continue')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
                print("   ✅ Cookies acceptés")
        except:
            pass
    
    async def extract_cinema_links(self, page: Page) -> List[str]:
        """Extrait les URLs des cinémas depuis la page d'annuaire"""
        # Scroll pour charger tous les cinémas
        print("   📜 Chargement de la liste...")
        for i in range(5):
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(500)
        
        # Extraire les liens
        links = await page.query_selector_all('a[data-keywords]')
        unique_urls = []
        
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
                    unique_urls.append(full_url)
        
        return unique_urls
    
    async def extract_cinema_details(self, page: Page, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un cinéma UGC"""
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        
        # Extraire le nom
        try:
            name = await page.inner_text('.block--title h1')
            name = name.strip()
        except:
            name = "Cinéma UGC"
        
        # Extraire l'adresse
        try:
            address = await page.inner_text('p.text-center')
            address = address.strip()
        except:
            address = ""
        
        return {
            "name": name,
            "address": address,
            "url": url
        }
