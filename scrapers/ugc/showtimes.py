"""
Scraper des séances UGC.
Extrait les horaires de séances depuis les pages des cinémas UGC.
"""
import os
from typing import List, Dict
from datetime import date, timedelta
from playwright.async_api import Page
from ..common.base import BaseShowtimesScraper


class UGCShowtimesScraper(BaseShowtimesScraper):
    """Scraper pour les séances UGC"""
    
    def __init__(self, days_ahead: int = None):
        days = days_ahead if days_ahead is not None else int(os.getenv("UGC_DAYS_AHEAD", "1"))
        super().__init__(group_name="UGC", days_ahead=days)
    
    async def accept_cookies(self, page: Page) -> None:
        """Accepte les cookies sur le site UGC"""
        try:
            cookie_btn = page.locator('.hagreed__continue')
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await page.wait_for_timeout(1000)
        except:
            pass
    
    async def select_date(self, page: Page, target_date: date) -> bool:
        """Sélectionne une date sur la page du cinéma UGC"""
        date_str = target_date.isoformat()
        
        # Déterminer le label
        label_hint = None
        if target_date == date.today():
            label_hint = "AUJOURD'HUI"
        elif target_date == date.today() + timedelta(days=1):
            label_hint = "DEMAIN"
        
        # Essayer les sélecteurs data-date
        selectors = [
            f"[data-date='{date_str}']",
            f"button[data-date='{date_str}']",
            f"li[data-date='{date_str}'] button",
            f"button[value='{date_str}']",
        ]
        
        for sel in selectors:
            loc = page.locator(sel)
            if await loc.count() > 0:
                try:
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    return True
                except:
                    continue
        
        # Essayer avec le label text
        if label_hint:
            try:
                loc = page.get_by_text(label_hint, exact=False)
                if await loc.count() > 0:
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    return True
            except:
                pass
        
        return False
    
    async def extract_movies_and_showtimes(self, page: Page, target_date: date) -> Dict[str, List[Dict]]:
        """Extrait les films et séances pour une date donnée sur UGC"""
        date_str = target_date.isoformat()
        
        # Attendre le chargement
        try:
            await page.wait_for_selector('a.color--dark-blue', timeout=5000)
        except:
            await page.evaluate("window.scrollTo(0, 500)")
            await page.wait_for_timeout(2000)
        
        # Extraire les films
        titles_loc = page.locator('a.color--dark-blue')
        count = await titles_loc.count()
        
        movies_map = {}
        
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
                    
                    if showtimes:
                        key = title_text.strip()
                        movies_map[key] = showtimes
            
            except:
                continue
        
        return movies_map
