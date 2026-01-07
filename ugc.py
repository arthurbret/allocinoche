"""
Script orchestrateur pour la récupération des données UGC.
Ce script coordonne l'extraction des cinémas et des séances en deux étapes distinctes.

Usage:
    python ugc.py --all          # Récupère les cinémas ET les séances
    python ugc.py --cinemas      # Récupère uniquement les cinémas
    python ugc.py --showtimes    # Récupère uniquement les séances
"""
import asyncio
import argparse
import sys
from scrape_ugc_cinemas import main as scrape_cinemas
from scrape_ugc_showtimes import main as scrape_showtimes



async def run_full_scraping():
    """Exécute le scraping complet: cinémas puis séances"""
    print("=" * 70)
    print("🎬 SCRAPING COMPLET UGC - CINÉMAS + SÉANCES")
    print("=" * 70)
    
    print("\n" + "🏢 ÉTAPE 1/2: RÉCUPÉRATION DES CINÉMAS".center(70))
    print("-" * 70)
    await scrape_cinemas()
    
    print("\n\n" + "📅 ÉTAPE 2/2: RÉCUPÉRATION DES SÉANCES".center(70))
    print("-" * 70)
    await scrape_showtimes()
    
    print("\n" + "=" * 70)
    print("✅ SCRAPING COMPLET TERMINÉ !")
    print("=" * 70)


async def main():
    """Point d'entrée principal avec gestion des arguments"""
    parser = argparse.ArgumentParser(
        description="Orchestrateur de scraping UGC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ugc.py --all          # Récupère tout (cinémas + séances)
  python ugc.py --cinemas      # Récupère uniquement les cinémas
  python ugc.py --showtimes    # Récupère uniquement les séances
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Récupère les cinémas ET les séances (complet)"
    )
    group.add_argument(
        "--cinemas",
        action="store_true",
        help="Récupère uniquement les cinémas"
    )
    group.add_argument(
        "--showtimes",
        action="store_true",
        help="Récupère uniquement les séances"
    )
    
    args = parser.parse_args()
    
    try:
        if args.all:
            await run_full_scraping()
        elif args.cinemas:
            print("=" * 70)
            print("🏢 SCRAPING DES CINÉMAS UGC UNIQUEMENT")
            print("=" * 70)
            await scrape_cinemas()
        elif args.showtimes:
            print("=" * 70)
            print("📅 SCRAPING DES SÉANCES UGC UNIQUEMENT")
            print("=" * 70)
            await scrape_showtimes()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
