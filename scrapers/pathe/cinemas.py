"""
Scraper des cinémas Pathé.
Extrait la liste des cinémas depuis le site Pathé Gaumont.

TODO: Implémenter les méthodes concrètes en analysant le site pathegaumont.com
"""
from typing import List, Dict, Any
from playwright.async_api import Page
from ..common.base import BaseCinemasScraper


class PatheCinemasScraper(BaseCinemasScraper):
    """Scraper pour les cinémas Pathé"""
    
    def __init__(self):
        super().__init__(group_name="Pathé")
    
    async def get_cinema_list_url(self) -> str:
        """URL de la page d'annuaire Pathé"""
        # TODO: Vérifier l'URL exacte
        return "https://www.pathegaumont.com/cinemas"
    
    async def accept_cookies(self, page: Page) -> None:
        """Accepte les cookies sur le site Pathé"""
        # TODO: Implémenter selon le site Pathé
        try:
            # À adapter selon les sélecteurs du site Pathé
            cookie_btn = page.locator('button:has-text("Accepter")')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
                print("   ✅ Cookies acceptés")
        except:
            pass
    
    async def extract_cinema_links(self, page: Page) -> List[str]:
        """Extrait les URLs des cinémas depuis la page d'annuaire"""
        # TODO: Implémenter l'extraction des liens Pathé
        # Exemple de structure (à adapter):
        print("   📜 Extraction des liens Pathé...")
        
        # À adapter selon la structure HTML du site
        links = await page.query_selector_all('a[href*="/cinema/"]')
        unique_urls = []
        
        for link in links:
            href = await link.get_attribute('href')
            if href:
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = "https://www.pathegaumont.com" + href
                else:
                    full_url = "https://www.pathegaumont.com/" + href
                
                if full_url not in unique_urls:
                    unique_urls.append(full_url)
        
        return unique_urls
    
    async def extract_cinema_details(self, page: Page, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un cinéma Pathé"""
        # TODO: Implémenter l'extraction des détails
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)
        
        # À adapter selon la structure HTML du site
        try:
            name = await page.inner_text('h1')  # Sélecteur à adapter
            name = name.strip()
        except:
            name = "Cinéma Pathé"
        
        try:
            address = await page.inner_text('.address')  # Sélecteur à adapter
            address = address.strip()
        except:
            address = ""
        
        return {
            "name": name,
            "address": address,
            "url": url
        }
