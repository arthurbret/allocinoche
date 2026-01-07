"""
Classes de base abstraites pour les scrapers de cinémas.
Toutes les implémentations spécifiques (UGC, Pathé, etc.) doivent hériter de ces classes.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date
from playwright.async_api import Page, async_playwright


class BaseCinemasScraper(ABC):
    """Classe de base pour scraper les cinémas d'un réseau"""
    
    def __init__(self, group_name: str):
        """
        Args:
            group_name: Nom du réseau (ex: "UGC", "Pathé")
        """
        self.group_name = group_name
        self.browser_args = ['--disable-blink-features=AutomationControlled']
    
    @abstractmethod
    async def get_cinema_list_url(self) -> str:
        """Retourne l'URL de la page listant tous les cinémas du réseau"""
        pass
    
    @abstractmethod
    async def accept_cookies(self, page: Page) -> None:
        """Gère l'acceptation des cookies sur le site"""
        pass
    
    @abstractmethod
    async def extract_cinema_links(self, page: Page) -> List[str]:
        """
        Extrait les URLs de tous les cinémas depuis la page d'annuaire.
        
        Returns:
            Liste des URLs des cinémas
        """
        pass
    
    @abstractmethod
    async def extract_cinema_details(self, page: Page, url: str) -> Dict[str, Any]:
        """
        Extrait les détails d'un cinéma (nom, adresse).
        
        Args:
            page: Page Playwright
            url: URL du cinéma
            
        Returns:
            Dict avec name, address, url
        """
        pass
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Point d'entrée principal pour scraper tous les cinémas.
        
        Returns:
            Liste des cinémas avec leurs détails
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=self.browser_args)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            print(f"🎬 Récupération de l'annuaire des cinémas {self.group_name}...")
            
            # Naviguer vers la page d'annuaire
            list_url = await self.get_cinema_list_url()
            await page.goto(list_url, wait_until="domcontentloaded")
            
            # Gérer les cookies
            await self.accept_cookies(page)
            
            # Extraire les liens des cinémas
            cinema_urls = await self.extract_cinema_links(page)
            print(f"   ✅ {len(cinema_urls)} cinémas {self.group_name} trouvés")
            
            # Extraire les détails de chaque cinéma
            cinemas = []
            for i, url in enumerate(cinema_urls):
                print(f"   [{i+1}/{len(cinema_urls)}] Extraction des détails...", end="")
                try:
                    details = await self.extract_cinema_details(page, url)
                    cinemas.append(details)
                    print(" ✅")
                except Exception as e:
                    print(f" ❌ Erreur: {e}")
            
            await browser.close()
            return cinemas


class BaseShowtimesScraper(ABC):
    """Classe de base pour scraper les séances d'un réseau"""
    
    def __init__(self, group_name: str, days_ahead: int = 1):
        """
        Args:
            group_name: Nom du réseau (ex: "UGC", "Pathé")
            days_ahead: Nombre de jours à récupérer (0=aujourd'hui, 1=aujourd'hui+demain)
        """
        self.group_name = group_name
        self.days_ahead = days_ahead
        self.browser_args = ['--disable-blink-features=AutomationControlled']
    
    @abstractmethod
    async def accept_cookies(self, page: Page) -> None:
        """Gère l'acceptation des cookies sur le site"""
        pass
    
    @abstractmethod
    async def select_date(self, page: Page, target_date: date) -> bool:
        """
        Sélectionne une date sur la page du cinéma.
        
        Args:
            page: Page Playwright
            target_date: Date à sélectionner
            
        Returns:
            True si la date a été sélectionnée, False sinon
        """
        pass
    
    @abstractmethod
    async def extract_movies_and_showtimes(self, page: Page, target_date: date) -> Dict[str, List[Dict]]:
        """
        Extrait les films et leurs séances pour une date donnée.
        
        Args:
            page: Page Playwright
            target_date: Date des séances
            
        Returns:
            Dict {titre_film: [{"time": "20:30", "details": "IMAX", "date": "2025-01-07"}]}
        """
        pass
    
    async def scrape_cinema(
        self, 
        page: Page, 
        cinema: Dict[str, Any], 
        target_dates: List[date]
    ) -> Dict[str, List[Dict]]:
        """
        Scrape les séances d'un cinéma pour plusieurs dates.
        
        Args:
            page: Page Playwright
            cinema: Informations du cinéma (dict avec 'url', 'name', etc.)
            target_dates: Liste des dates à scraper
            
        Returns:
            Dict {titre_film: [séances]}
        """
        movies_map = {}
        
        for target_date in target_dates:
            try:
                # Naviguer vers la page du cinéma
                await page.goto(cinema["url"], wait_until="networkidle", timeout=40000)
                
                # Sélectionner la date
                await self.select_date(page, target_date)
                
                # Extraire les films et séances
                date_movies = await self.extract_movies_and_showtimes(page, target_date)
                
                # Fusionner avec les séances déjà trouvées
                for movie_title, showtimes in date_movies.items():
                    if movie_title not in movies_map:
                        movies_map[movie_title] = []
                    movies_map[movie_title].extend(showtimes)
                
            except Exception as e:
                print(f"      ⚠️  Erreur date {target_date}: {e}")
        
        return movies_map
    
    async def scrape(self, cinemas: List[Dict[str, Any]]) -> Dict[int, Dict[str, List[Dict]]]:
        """
        Point d'entrée principal pour scraper les séances de plusieurs cinémas.
        
        Args:
            cinemas: Liste des cinémas à scraper (dicts avec 'id', 'url', 'name')
            
        Returns:
            Dict {cinema_id: {titre_film: [séances]}}
        """
        from datetime import timedelta
        
        target_dates = [date.today() + timedelta(days=i) for i in range(self.days_ahead + 1)]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=self.browser_args)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            # Accepter les cookies une fois
            try:
                await page.goto(cinemas[0]["url"] if cinemas else "https://example.com")
                await self.accept_cookies(page)
            except:
                pass
            
            results = {}
            
            for i, cinema in enumerate(cinemas):
                print(f"\n   [{i+1}/{len(cinemas)}] 🎬 {cinema['name']}")
                
                movies_map = await self.scrape_cinema(page, cinema, target_dates)
                
                if movies_map:
                    results[cinema["id"]] = movies_map
                    total_showtimes = sum(len(showtimes) for showtimes in movies_map.values())
                    print(f"      ✅ {len(movies_map)} films, {total_showtimes} séances")
                else:
                    print(f"      ⚠️  Aucune séance trouvée")
            
            await browser.close()
            
        return results
