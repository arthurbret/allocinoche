"""
Orchestrateur principal pour le scraping multi-réseaux.
Remplace ugc.py et supporte plusieurs réseaux de cinémas (UGC, Pathé, etc.)
"""
import asyncio
import argparse
import sys
from scrapers.ugc import UGCCinemasScraper, UGCShowtimesScraper
# from scrapers.pathe import PatheCinemasScraper, PatheShowtimesScraper  # À activer après implémentation
from scrapers.common.database import DatabaseManager


SUPPORTED_NETWORKS = {
    'ugc': {
        'name': 'UGC',
        'cinemas_scraper': UGCCinemasScraper,
        'showtimes_scraper': UGCShowtimesScraper,
    },
    # 'pathe': {
    #     'name': 'Pathé',
    #     'cinemas_scraper': PatheCinemasScraper,
    #     'showtimes_scraper': PatheShowtimesScraper,
    # },
}


async def scrape_cinemas(network: str):
    """Scrape les cinémas d'un réseau"""
    if network not in SUPPORTED_NETWORKS:
        print(f"❌ Réseau '{network}' non supporté")
        print(f"Réseaux disponibles: {', '.join(SUPPORTED_NETWORKS.keys())}")
        return
    
    config = SUPPORTED_NETWORKS[network]
    print("=" * 70)
    print(f"🏢 SCRAPING DES CINÉMAS {config['name'].upper()}")
    print("=" * 70)
    
    # Initialiser la base de données
    db = DatabaseManager()
    
    # Récupérer ou créer le groupe
    print(f"\n📋 Gestion du groupe {config['name']}...")
    group_id = db.get_or_create_group(config['name'])
    print(f"   ✅ Groupe {config['name']} (ID: {group_id})")
    
    # Scraper les cinémas
    scraper = config['cinemas_scraper']()
    cinemas = await scraper.scrape()
    
    # Insérer dans la base de données
    if cinemas:
        print(f"\n💾 Insertion de {len(cinemas)} cinémas...")
        inserted = 0
        updated = 0
        
        for cinema in cinemas:
            cinema_data = {
                "name": cinema["name"],
                "address": cinema["address"],
                "url": cinema["url"],
                "group": group_id
            }
            
            cinema_id = db.upsert_cinema(cinema_data)
            if cinema_id:
                # Vérifier si c'est une insertion ou une mise à jour
                existing = db.client.table("cinemas").select("*").eq("url", cinema["url"]).execute()
                if len(existing.data) == 1:
                    updated += 1
                    print(f"   ✏️  {cinema['name']}")
                else:
                    inserted += 1
                    print(f"   ✅ {cinema['name']}")
        
        print(f"\n✅ Résumé: {inserted} insérés, {updated} mis à jour")
    else:
        print("⚠️  Aucun cinéma trouvé")
    
    print("\n" + "=" * 70)
    print("✅ TERMINÉ !")
    print("=" * 70)


async def scrape_showtimes(network: str):
    """Scrape les séances d'un réseau"""
    if network not in SUPPORTED_NETWORKS:
        print(f"❌ Réseau '{network}' non supporté")
        print(f"Réseaux disponibles: {', '.join(SUPPORTED_NETWORKS.keys())}")
        return
    
    config = SUPPORTED_NETWORKS[network]
    print("=" * 70)
    print(f"📅 SCRAPING DES SÉANCES {config['name'].upper()}")
    print("=" * 70)
    
    # Initialiser la base de données
    db = DatabaseManager()
    
    # Récupérer le groupe
    print(f"\n📋 Récupération du groupe {config['name']}...")
    try:
        group_id = db.get_or_create_group(config['name'])
    except:
        print(f"❌ Groupe {config['name']} non trouvé")
        print(f"💡 Exécutez d'abord: python main.py --cinemas --network {network}")
        return
    
    # Récupérer les cinémas du groupe
    cinemas = db.get_cinemas_by_group(group_id)
    
    if not cinemas:
        print(f"⚠️  Aucun cinéma {config['name']} en base de données")
        print(f"💡 Exécutez d'abord: python main.py --cinemas --network {network}")
        return
    
    print(f"   ✅ {len(cinemas)} cinémas trouvés")
    
    # Scraper les séances
    scraper = config['showtimes_scraper']()
    results = await scraper.scrape(cinemas)
    
    # Insérer dans la base de données
    total_inserted = 0
    for cinema_id, movies_data in results.items():
        inserted = db.batch_insert_showtimes(cinema_id, movies_data)
        total_inserted += inserted
    
    print(f"\n✅ Total: {total_inserted} séances insérées")
    print("\n" + "=" * 70)
    print("✅ TERMINÉ !")
    print("=" * 70)


async def scrape_all(network: str):
    """Scrape les cinémas ET les séances d'un réseau"""
    print("=" * 70)
    print(f"🎬 SCRAPING COMPLET - {network.upper()}")
    print("=" * 70)
    
    print("\n" + "🏢 ÉTAPE 1/2: CINÉMAS".center(70))
    print("-" * 70)
    await scrape_cinemas(network)
    
    print("\n\n" + "📅 ÉTAPE 2/2: SÉANCES".center(70))
    print("-" * 70)
    await scrape_showtimes(network)


async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Orchestrateur de scraping multi-réseaux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Exemples:
  python main.py --cinemas --network ugc       # Scrape les cinémas UGC
  python main.py --showtimes --network ugc     # Scrape les séances UGC
  python main.py --all --network ugc           # Scrape tout (UGC)
  python main.py --all --network pathe         # Scrape tout (Pathé)

Réseaux supportés: {', '.join(SUPPORTED_NETWORKS.keys())}
        """
    )
    
    # Action à effectuer
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--cinemas",
        action="store_true",
        help="Scrape uniquement les cinémas"
    )
    action_group.add_argument(
        "--showtimes",
        action="store_true",
        help="Scrape uniquement les séances"
    )
    action_group.add_argument(
        "--all",
        action="store_true",
        help="Scrape les cinémas ET les séances"
    )
    
    # Réseau à scraper
    parser.add_argument(
        "--network",
        required=True,
        choices=list(SUPPORTED_NETWORKS.keys()),
        help="Réseau de cinémas à scraper"
    )
    
    args = parser.parse_args()
    
    try:
        if args.all:
            await scrape_all(args.network)
        elif args.cinemas:
            await scrape_cinemas(args.network)
        elif args.showtimes:
            await scrape_showtimes(args.network)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
