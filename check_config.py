"""
Script utilitaire pour vérifier la configuration de la base de données Supabase.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Charger les variables d'environnement
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def check_env_vars():
    """Vérifie que les variables d'environnement sont configurées"""
    print("🔍 Vérification des variables d'environnement...")
    
    if not SUPABASE_URL:
        print("   ❌ SUPABASE_URL n'est pas définie")
        return False
    
    if not SUPABASE_KEY:
        print("   ❌ SUPABASE_KEY n'est pas définie")
        return False
    
    print(f"   ✅ SUPABASE_URL: {SUPABASE_URL}")
    print(f"   ✅ SUPABASE_KEY: {'*' * 20}...{SUPABASE_KEY[-4:]}")
    
    days_ahead = os.getenv("UGC_DAYS_AHEAD", "1")
    print(f"   ℹ️  UGC_DAYS_AHEAD: {days_ahead}")
    
    return True


def check_connection(supabase: Client):
    """Vérifie la connexion à Supabase"""
    print("\n🔌 Vérification de la connexion à Supabase...")
    
    try:
        # Tenter une requête simple
        response = supabase.table("groups").select("count").execute()
        print("   ✅ Connexion réussie")
        return True
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False


def check_tables(supabase: Client):
    """Vérifie que les tables nécessaires existent"""
    print("\n📊 Vérification des tables...")
    
    tables = ["groups", "cinemas", "movies", "showtimes"]
    all_ok = True
    
    for table in tables:
        try:
            response = supabase.table(table).select("*").limit(1).execute()
            print(f"   ✅ Table '{table}' accessible")
        except Exception as e:
            print(f"   ❌ Table '{table}' inaccessible: {e}")
            all_ok = False
    
    return all_ok


def check_groups(supabase: Client):
    """Vérifie l'existence du groupe UGC"""
    print("\n🎬 Vérification du groupe UGC...")
    
    try:
        response = supabase.table("groups").select("*").eq("name", "UGC").execute()
        
        if response.data and len(response.data) > 0:
            group = response.data[0]
            print(f"   ✅ Groupe UGC trouvé (ID: {group['id']})")
            return True
        else:
            print("   ⚠️  Groupe UGC non trouvé")
            print("   💡 Le groupe sera créé automatiquement lors du premier scraping")
            return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_cinemas(supabase: Client):
    """Vérifie les cinémas en base"""
    print("\n🏢 Vérification des cinémas...")
    
    try:
        # Compter tous les cinémas
        response = supabase.table("cinemas").select("*").execute()
        total_cinemas = len(response.data) if response.data else 0
        print(f"   ℹ️  Total de cinémas: {total_cinemas}")
        
        # Compter les cinémas UGC
        group_response = supabase.table("groups").select("id").eq("name", "UGC").execute()
        if group_response.data and len(group_response.data) > 0:
            group_id = group_response.data[0]["id"]
            ugc_response = supabase.table("cinemas").select("*").eq("group_id", group_id).execute()
            ugc_count = len(ugc_response.data) if ugc_response.data else 0
            print(f"   ℹ️  Cinémas UGC: {ugc_count}")
        
        if total_cinemas == 0:
            print("   ⚠️  Aucun cinéma en base")
            print("   💡 Exécutez: python ugc.py --cinemas")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_showtimes(supabase: Client):
    """Vérifie les séances en base"""
    print("\n📅 Vérification des séances...")
    
    try:
        response = supabase.table("showtimes").select("*").limit(1).execute()
        
        # Compter le total
        count_response = supabase.table("showtimes").select("*").execute()
        total = len(count_response.data) if count_response.data else 0
        
        print(f"   ℹ️  Total de séances: {total}")
        
        if total == 0:
            print("   ⚠️  Aucune séance en base")
            print("   💡 Exécutez: python ugc.py --showtimes")
        else:
            # Afficher les dates disponibles
            dates_response = supabase.table("showtimes").select("showtime_date").execute()
            if dates_response.data:
                dates = sorted(set([s["showtime_date"] for s in dates_response.data]))
                print(f"   ℹ️  Dates disponibles: {', '.join(dates[:5])}")
                if len(dates) > 5:
                    print(f"      ... et {len(dates) - 5} autres dates")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def main():
    """Fonction principale"""
    print("=" * 70)
    print("🔍 VÉRIFICATION DE LA CONFIGURATION - ALLOCINOCHE")
    print("=" * 70)
    
    # Vérifier les variables d'environnement
    if not check_env_vars():
        print("\n❌ Configuration incomplète")
        print("💡 Créez un fichier .env avec SUPABASE_URL et SUPABASE_KEY")
        sys.exit(1)
    
    # Créer le client Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"\n❌ Impossible de créer le client Supabase: {e}")
        sys.exit(1)
    
    # Vérifier la connexion
    if not check_connection(supabase):
        print("\n❌ Impossible de se connecter à Supabase")
        sys.exit(1)
    
    # Vérifier les tables
    if not check_tables(supabase):
        print("\n❌ Certaines tables sont manquantes")
        print("💡 Exécutez le script SQL: migrations/001_add_groups_table.sql")
        sys.exit(1)
    
    # Vérifications additionnelles
    check_groups(supabase)
    check_cinemas(supabase)
    check_showtimes(supabase)
    
    print("\n" + "=" * 70)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 70)
    print("\n💡 Prochaines étapes:")
    print("   1. python ugc.py --cinemas    # Récupérer les cinémas")
    print("   2. python ugc.py --showtimes  # Récupérer les séances")
    print("   3. uvicorn api:app --reload   # Lancer l'API")


if __name__ == "__main__":
    main()
