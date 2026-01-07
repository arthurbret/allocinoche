"""
Script utilitaire pour nettoyer les anciennes séances de la base de données.
Les séances passées peuvent être supprimées pour optimiser les performances.
"""
import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Merci de configurer SUPABASE_URL et SUPABASE_KEY dans un fichier .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def count_old_showtimes(days_old=7):
    """Compte les séances plus anciennes que X jours"""
    try:
        cutoff_date = (date.today() - timedelta(days=days_old)).isoformat()
        response = supabase.table("showtimes").select("*").lt("showtime_date", cutoff_date).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0


def delete_old_showtimes(days_old=7, dry_run=True):
    """
    Supprime les séances plus anciennes que X jours
    
    Args:
        days_old: Nombre de jours d'ancienneté
        dry_run: Si True, simule la suppression sans l'exécuter
    """
    try:
        cutoff_date = (date.today() - timedelta(days=days_old)).isoformat()
        
        # Compter d'abord
        response = supabase.table("showtimes").select("*").lt("showtime_date", cutoff_date).execute()
        count = len(response.data) if response.data else 0
        
        if count == 0:
            print(f"✅ Aucune séance à supprimer (plus de {days_old} jours)")
            return 0
        
        print(f"📊 {count} séances trouvées (antérieures au {cutoff_date})")
        
        if dry_run:
            print("   ℹ️  Mode simulation (dry-run) - Aucune suppression effectuée")
            print("   💡 Utilisez --confirm pour supprimer réellement")
            return 0
        
        # Supprimer
        print("   🗑️  Suppression en cours...")
        supabase.table("showtimes").delete().lt("showtime_date", cutoff_date).execute()
        print(f"   ✅ {count} séances supprimées")
        
        return count
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return 0


def clean_orphaned_movies():
    """Supprime les films qui n'ont plus de séances associées"""
    try:
        # Récupérer tous les films
        movies_response = supabase.table("movies").select("id, title").execute()
        if not movies_response.data:
            print("✅ Aucun film en base")
            return 0
        
        orphaned = []
        
        for movie in movies_response.data:
            # Vérifier s'il a des séances
            showtimes_response = supabase.table("showtimes").select("id").eq("movie_id", movie["id"]).limit(1).execute()
            
            if not showtimes_response.data or len(showtimes_response.data) == 0:
                orphaned.append(movie)
        
        if len(orphaned) == 0:
            print("✅ Aucun film orphelin trouvé")
            return 0
        
        print(f"📊 {len(orphaned)} films orphelins trouvés")
        for movie in orphaned[:5]:
            print(f"   - {movie['title']}")
        if len(orphaned) > 5:
            print(f"   ... et {len(orphaned) - 5} autres")
        
        print("\n   ⚠️  Cette opération nécessite une confirmation manuelle")
        print("   💡 Utilisez l'interface Supabase pour supprimer manuellement")
        
        return len(orphaned)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 0


def show_database_stats():
    """Affiche les statistiques de la base de données"""
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("-" * 60)
    
    try:
        # Groupes
        groups_response = supabase.table("groups").select("*").execute()
        groups_count = len(groups_response.data) if groups_response.data else 0
        print(f"   Groupes de cinémas: {groups_count}")
        
        # Cinémas
        cinemas_response = supabase.table("cinemas").select("*").execute()
        cinemas_count = len(cinemas_response.data) if cinemas_response.data else 0
        print(f"   Cinémas: {cinemas_count}")
        
        # Films
        movies_response = supabase.table("movies").select("*").execute()
        movies_count = len(movies_response.data) if movies_response.data else 0
        print(f"   Films: {movies_count}")
        
        # Séances totales
        showtimes_response = supabase.table("showtimes").select("*").execute()
        showtimes_count = len(showtimes_response.data) if showtimes_response.data else 0
        print(f"   Séances (total): {showtimes_count}")
        
        # Séances futures
        today = date.today().isoformat()
        future_response = supabase.table("showtimes").select("*").gte("showtime_date", today).execute()
        future_count = len(future_response.data) if future_response.data else 0
        print(f"   Séances futures: {future_count}")
        
        # Séances passées
        past_count = showtimes_count - future_count
        print(f"   Séances passées: {past_count}")
        
        # Séances très anciennes (> 7 jours)
        old_count = count_old_showtimes(7)
        print(f"   Séances > 7 jours: {old_count}")
        
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Nettoyage de la base de données AllocinoChe",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python cleanup.py --stats                    # Afficher les statistiques
  python cleanup.py --clean                    # Simuler le nettoyage
  python cleanup.py --clean --confirm          # Nettoyer réellement
  python cleanup.py --clean --days 14          # Nettoyer > 14 jours
  python cleanup.py --orphaned                 # Trouver les films orphelins
        """
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Afficher les statistiques de la base de données"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Nettoyer les anciennes séances"
    )
    parser.add_argument(
        "--orphaned",
        action="store_true",
        help="Trouver les films orphelins"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Nombre de jours d'ancienneté pour le nettoyage (défaut: 7)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirmer la suppression (sinon mode simulation)"
    )
    
    args = parser.parse_args()
    
    # Si aucune option, afficher les stats par défaut
    if not (args.stats or args.clean or args.orphaned):
        args.stats = True
    
    print("=" * 60)
    print("🧹 NETTOYAGE DE LA BASE DE DONNÉES - ALLOCINOCHE")
    print("=" * 60)
    print()
    
    try:
        if args.stats:
            show_database_stats()
            print()
        
        if args.clean:
            print("🗑️  NETTOYAGE DES ANCIENNES SÉANCES")
            print("-" * 60)
            deleted = delete_old_showtimes(args.days, dry_run=not args.confirm)
            print()
        
        if args.orphaned:
            print("🔍 RECHERCHE DES FILMS ORPHELINS")
            print("-" * 60)
            clean_orphaned_movies()
            print()
        
        print("=" * 60)
        print("✅ TERMINÉ")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
