#!/usr/bin/env python3
"""
Example usage of the AlloCiné scraper
Demonstrates different ways to use the scraper
"""

from scraper import AllocineScaper
import json


def example_basic_usage():
    """Example: Basic usage with default city"""
    print("Example 1: Basic usage")
    print("-" * 50)
    
    scraper = AllocineScaper("https://www.allocine.fr/salle/cinema/ville-113315/")
    data = scraper.scrape_all()
    scraper.save_to_json(data, "output_basic.json")
    
    print(f"Scraped {len(data['cinemas'])} cinemas")
    print()


def example_custom_city():
    """Example: Scraping a different city"""
    print("Example 2: Custom city")
    print("-" * 50)
    
    # Example with Paris (ville-1)
    scraper = AllocineScaper("https://www.allocine.fr/salle/cinema/ville-1/")
    data = scraper.scrape_all()
    
    print(f"Date: {data['date']}")
    print(f"Found {len(data['cinemas'])} cinemas")
    
    # Show summary
    for cinema in data['cinemas'][:3]:  # Show first 3
        print(f"  - {cinema['cinema']}: {len(cinema['films'])} films")
    
    print()


def example_processing_data():
    """Example: Processing the scraped data"""
    print("Example 3: Processing data")
    print("-" * 50)
    
    # Load example data
    with open('example_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count total showtimes
    total_showtimes = 0
    for cinema in data['cinemas']:
        for film in cinema['films']:
            total_showtimes += len(film['seances'])
    
    print(f"Total cinemas: {len(data['cinemas'])}")
    print(f"Total films: {sum(len(c['films']) for c in data['cinemas'])}")
    print(f"Total showtimes: {total_showtimes}")
    
    # Find film with most showtimes
    all_films = []
    for cinema in data['cinemas']:
        for film in cinema['films']:
            all_films.append({
                'titre': film['titre'],
                'cinema': cinema['cinema'],
                'nb_seances': len(film['seances'])
            })
    
    if all_films:
        most_showtimes = max(all_films, key=lambda x: x['nb_seances'])
        print(f"\nFilm with most showtimes:")
        print(f"  '{most_showtimes['titre']}' at {most_showtimes['cinema']}")
        print(f"  {most_showtimes['nb_seances']} showtimes")
    
    print()


def example_filter_by_time():
    """Example: Filter showtimes by time of day"""
    print("Example 4: Filter evening showtimes")
    print("-" * 50)
    
    with open('example_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find evening shows (after 18:00)
    evening_films = []
    for cinema in data['cinemas']:
        for film in cinema['films']:
            evening_times = [s for s in film['seances'] if s >= '18:00']
            if evening_times:
                evening_films.append({
                    'titre': film['titre'],
                    'cinema': cinema['cinema'],
                    'seances': evening_times
                })
    
    print(f"Found {len(evening_films)} films with evening showtimes:")
    for film in evening_films[:5]:  # Show first 5
        print(f"  {film['titre']} ({film['cinema']})")
        print(f"    Showtimes: {', '.join(film['seances'])}")
    
    print()


if __name__ == '__main__':
    print("AlloCiné Scraper - Usage Examples")
    print("=" * 50)
    print()
    
    # Note: Examples 1 and 2 require network access
    # They are shown for reference but won't work in restricted environments
    
    # example_basic_usage()
    # example_custom_city()
    
    # These examples use the example data file
    example_processing_data()
    example_filter_by_time()
    
    print("=" * 50)
    print("Check the generated JSON files for full data!")
