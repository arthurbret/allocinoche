"""
Module de scraping pour le réseau UGC.
"""
from .cinemas import UGCCinemasScraper
from .showtimes import UGCShowtimesScraper

__all__ = ['UGCCinemasScraper', 'UGCShowtimesScraper']
