#!/usr/bin/env python3
"""
AlloCiné Cinema Scraper
Scrapes cinema listings and showtimes from AlloCiné for a specific city
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
import sys


class AllocineScaper:
    """Scraper for AlloCiné cinema listings"""
    
    def __init__(self, city_url: str):
        """
        Initialize the scraper
        
        Args:
            city_url: URL of the city page on AlloCiné
        """
        self.city_url = city_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_tomorrow_date(self) -> str:
        """Get tomorrow's date in YYYY-MM-DD format"""
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse a page
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object of the page
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return None
    
    def get_cinema_list(self) -> List[Dict[str, str]]:
        """
        Get list of all cinemas from the city page
        
        Returns:
            List of dictionaries with cinema information
        """
        soup = self.fetch_page(self.city_url)
        if not soup:
            return []
        
        cinemas = []
        
        # Find all cinema links
        cinema_links = soup.find_all('a', href=re.compile(r'/seance/salle_gen_csalle='))
        
        for link in cinema_links:
            cinema_url = link.get('href', '')
            if cinema_url and not cinema_url.startswith('http'):
                cinema_url = 'https://www.allocine.fr' + cinema_url
            
            # Get cinema name
            cinema_name = link.get_text(strip=True)
            
            if cinema_url and cinema_name:
                # Check if this cinema is already in the list
                if not any(c['url'] == cinema_url for c in cinemas):
                    cinemas.append({
                        'name': cinema_name,
                        'url': cinema_url
                    })
        
        # Alternative: Look for cinema cards
        if not cinemas:
            cinema_cards = soup.find_all(['div', 'article'], class_=re.compile(r'.*cinema.*|.*theater.*', re.I))
            for card in cinema_cards:
                link = card.find('a', href=re.compile(r'/seance/salle_gen_csalle='))
                if link:
                    cinema_url = link.get('href', '')
                    if not cinema_url.startswith('http'):
                        cinema_url = 'https://www.allocine.fr' + cinema_url
                    
                    cinema_name = link.get_text(strip=True)
                    
                    if cinema_url and cinema_name:
                        if not any(c['url'] == cinema_url for c in cinemas):
                            cinemas.append({
                                'name': cinema_name,
                                'url': cinema_url
                            })
        
        return cinemas
    
    def extract_film_info(self, film_element) -> Dict[str, Any]:
        """
        Extract film information from a film element
        
        Args:
            film_element: BeautifulSoup element containing film information
            
        Returns:
            Dictionary with film information
        """
        film_info = {
            'titre': '',
            'url': '',
            'date_sortie': '',
            'realisateur': '',
            'genre': '',
            'duree': '',
            'seances': []
        }
        
        # Extract title and URL
        title_link = film_element.find('a', class_=re.compile(r'.*meta-title.*'))
        if not title_link:
            title_link = film_element.find('a', href=re.compile(r'/film/fichefilm_gen_cfilm='))
        
        if title_link:
            film_info['titre'] = title_link.get_text(strip=True)
            film_url = title_link.get('href', '')
            if film_url and not film_url.startswith('http'):
                film_url = 'https://www.allocine.fr' + film_url
            film_info['url'] = film_url
        
        # Extract release date
        release_date = film_element.find(text=re.compile(r'Date de sortie|Sortie'))
        if release_date:
            parent = release_date.parent
            if parent:
                date_text = parent.get_text(strip=True)
                # Extract date from text
                date_match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date_text)
                if date_match:
                    film_info['date_sortie'] = date_match.group(0)
        
        # Look for metadata in spans or divs
        meta_elements = film_element.find_all(['span', 'div'], class_=re.compile(r'.*meta.*|.*info.*'))
        for meta in meta_elements:
            text = meta.get_text(strip=True)
            
            # Check for director
            if 'De ' in text or 'réalisateur' in text.lower():
                film_info['realisateur'] = text.replace('De ', '').strip()
            
            # Check for genre
            if any(genre in text.lower() for genre in ['drame', 'comédie', 'action', 'thriller', 'science-fiction', 'animation', 'documentaire']):
                if not film_info['genre']:
                    film_info['genre'] = text
            
            # Check for duration
            if re.search(r'\d+h\s*\d*', text):
                film_info['duree'] = text
        
        # Extract showtimes
        showtime_elements = film_element.find_all(['span', 'div', 'a'], class_=re.compile(r'.*seance.*|.*showtime.*'))
        if not showtime_elements:
            # Look for time patterns
            showtime_elements = film_element.find_all(text=re.compile(r'\d{1,2}:\d{2}'))
        
        for showtime in showtime_elements:
            time_text = showtime if isinstance(showtime, str) else showtime.get_text(strip=True)
            # Extract time in HH:MM format
            times = re.findall(r'\d{1,2}:\d{2}', time_text)
            for time in times:
                if time not in film_info['seances']:
                    film_info['seances'].append(time)
        
        return film_info
    
    def scrape_cinema_showtimes(self, cinema: Dict[str, str], date: str) -> Dict[str, Any]:
        """
        Scrape showtimes for a specific cinema and date
        
        Args:
            cinema: Dictionary with cinema information
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with cinema and film information
        """
        # Add date parameter to URL
        cinema_url = cinema['url']
        if '?' in cinema_url:
            cinema_url += f'&date={date}'
        else:
            cinema_url += f'?date={date}'
        
        # Also try the hash format mentioned in requirements
        cinema_url_hash = cinema['url'] + f'#shwt_date={date}'
        
        print(f"Scraping {cinema['name']}...")
        
        # Try the regular URL first
        soup = self.fetch_page(cinema_url)
        
        # If that doesn't work, try the hash version
        if not soup or not soup.find_all(class_=re.compile(r'.*film.*|.*movie.*')):
            soup = self.fetch_page(cinema_url_hash)
        
        if not soup:
            return {
                'cinema': cinema['name'],
                'url': cinema['url'],
                'films': []
            }
        
        films = []
        
        # Find all film containers
        film_containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'.*film.*|.*movie.*'))
        
        # If no film containers found, try different selectors
        if not film_containers:
            film_containers = soup.find_all(['div', 'article'], attrs={'data-film': True})
        
        if not film_containers:
            # Try finding by film links
            film_links = soup.find_all('a', href=re.compile(r'/film/fichefilm_gen_cfilm='))
            # Group by parent elements
            parents = set()
            for link in film_links:
                parent = link.find_parent(['div', 'article', 'section'])
                if parent and parent not in parents:
                    parents.add(parent)
                    film_containers.append(parent)
        
        for container in film_containers:
            film_info = self.extract_film_info(container)
            if film_info['titre']:  # Only add if we got at least a title
                films.append(film_info)
        
        return {
            'cinema': cinema['name'],
            'url': cinema['url'],
            'date': date,
            'films': films
        }
    
    def scrape_all(self) -> Dict[str, Any]:
        """
        Scrape all cinemas and their showtimes
        
        Returns:
            Dictionary with all scraped data
        """
        tomorrow_date = self.get_tomorrow_date()
        
        print(f"Fetching cinema list from {self.city_url}...")
        cinemas = self.get_cinema_list()
        
        print(f"Found {len(cinemas)} cinemas")
        
        results = {
            'date': tomorrow_date,
            'city_url': self.city_url,
            'cinemas': []
        }
        
        for cinema in cinemas:
            cinema_data = self.scrape_cinema_showtimes(cinema, tomorrow_date)
            results['cinemas'].append(cinema_data)
        
        return results
    
    def save_to_json(self, data: Dict[str, Any], filename: str = 'allocine_data.json'):
        """
        Save scraped data to JSON file
        
        Args:
            data: Data to save
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nData saved to {filename}")


def main():
    """Main function"""
    # Default city URL (Ville-113315 from the requirements)
    city_url = "https://www.allocine.fr/salle/cinema/ville-113315/"
    
    # Allow custom URL from command line
    if len(sys.argv) > 1:
        city_url = sys.argv[1]
    
    scraper = AllocineScaper(city_url)
    
    print("Starting AlloCiné scraper...")
    print("=" * 50)
    
    data = scraper.scrape_all()
    
    print("=" * 50)
    print(f"Scraping complete!")
    print(f"Total cinemas: {len(data['cinemas'])}")
    total_films = sum(len(cinema['films']) for cinema in data['cinemas'])
    print(f"Total films found: {total_films}")
    
    scraper.save_to_json(data)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
