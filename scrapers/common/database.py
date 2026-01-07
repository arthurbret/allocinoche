"""
Gestionnaire de base de données pour tous les scrapers.
Centralise les opérations Supabase.
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class DatabaseManager:
    """Gestionnaire centralisé pour les opérations Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL et SUPABASE_KEY doivent être définis dans .env")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def get_or_create_group(self, name: str) -> int:
        """
        Récupère ou crée un groupe de cinémas.
        
        Args:
            name: Nom du groupe (ex: "UGC", "Pathé")
            
        Returns:
            ID du groupe
        """
        # Vérifier si le groupe existe
        response = self.client.table("groups").select("*").eq("name", name).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        
        # Créer le groupe
        response = self.client.table("groups").insert({"name": name}).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        
        raise Exception(f"Impossible de créer le groupe {name}")
    
    def upsert_cinema(self, cinema_data: Dict[str, Any]) -> Optional[int]:
        """
        Insère ou met à jour un cinéma.
        
        Args:
            cinema_data: Données du cinéma (name, address, url, group)
            
        Returns:
            ID du cinéma ou None en cas d'erreur
        """
        try:
            # Vérifier si le cinéma existe
            existing = self.client.table("cinemas").select("*").eq("url", cinema_data["url"]).execute()
            
            if existing.data and len(existing.data) > 0:
                # Mise à jour
                cinema_id = existing.data[0]["id"]
                self.client.table("cinemas").update(cinema_data).eq("id", cinema_id).execute()
                return cinema_id
            else:
                # Insertion
                response = self.client.table("cinemas").insert(cinema_data).execute()
                return response.data[0]["id"] if response.data else None
        except Exception as e:
            print(f"Erreur upsert cinéma: {e}")
            return None
    
    def get_cinemas_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Récupère tous les cinémas d'un groupe.
        
        Args:
            group_id: ID du groupe
            
        Returns:
            Liste des cinémas
        """
        response = self.client.table("cinemas").select("*").eq("group", group_id).execute()
        return response.data if response.data else []
    
    def upsert_movie(self, title: str) -> Optional[int]:
        """
        Insère ou récupère un film.
        
        Args:
            title: Titre du film
            
        Returns:
            ID du film ou None
        """
        try:
            response = self.client.table("movies").upsert(
                {"title": title},
                on_conflict="title"
            ).execute()
            
            return response.data[0]["id"] if response.data else None
        except Exception as e:
            print(f"Erreur upsert film: {e}")
            return None
    
    def insert_showtime(self, showtime_data: Dict[str, Any]) -> bool:
        """
        Insère une séance.
        
        Args:
            showtime_data: Données de la séance (cinema_id, movie_id, showtime_date, time, details)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Vérifier si la séance existe déjà
            existing = self.client.table("showtimes").select("*").match({
                "cinema_id": showtime_data["cinema_id"],
                "movie_id": showtime_data["movie_id"],
                "showtime_date": showtime_data["showtime_date"],
                "time": showtime_data["time"]
            }).execute()
            
            if not existing.data or len(existing.data) == 0:
                self.client.table("showtimes").insert(showtime_data).execute()
                return True
            
            return False  # Séance déjà existante
        except Exception as e:
            print(f"Erreur insertion séance: {e}")
            return False
    
    def batch_insert_showtimes(self, cinema_id: int, movies_data: Dict[str, List[Dict]]) -> int:
        """
        Insère les séances pour plusieurs films d'un cinéma.
        
        Args:
            cinema_id: ID du cinéma
            movies_data: Dictionnaire {titre_film: [séances]}
            
        Returns:
            Nombre de séances insérées
        """
        total_inserted = 0
        
        for movie_title, showtimes in movies_data.items():
            movie_id = self.upsert_movie(movie_title)
            
            if not movie_id:
                continue
            
            for showtime in showtimes:
                showtime_data = {
                    "cinema_id": cinema_id,
                    "movie_id": movie_id,
                    "showtime_date": showtime.get("date"),
                    "time": showtime["time"],
                    "details": showtime["details"]
                }
                
                if self.insert_showtime(showtime_data):
                    total_inserted += 1
        
        return total_inserted
