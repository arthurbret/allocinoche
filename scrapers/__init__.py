"""
Module de scraping pour différents réseaux de cinémas.
"""
from .ugc import UGCCinemasScraper, UGCShowtimesScraper
# from .pathe import PatheCinemasScraper, PatheShowtimesScraper  # À implémenter

__all__ = [
    'UGCCinemasScraper',
    'UGCShowtimesScraper',
]
