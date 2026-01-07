# 🚀 Guide de Démarrage Rapide - AllocinoChe v2.0

## Installation en 5 minutes

### 1️⃣ Prérequis
```bash
# Python 3.11+
python --version

# Git
git --version
```

### 2️⃣ Installation
```bash
# Cloner le projet
git clone https://github.com/arthurbret/allocinoche.git
cd allocinoche

# Installer les dépendances
pip install -r requirements.txt

# Installer Playwright
playwright install chromium
```

### 3️⃣ Configuration
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos credentials Supabase
nano .env  # ou votre éditeur préféré
```

**.env requis :**
```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-cle-api
UGC_DAYS_AHEAD=1
```

### 4️⃣ Base de données
```bash
# Ouvrir Supabase SQL Editor
# Copier/coller le contenu de :
migrations/001_add_groups_table.sql
# Et exécuter
```

### 5️⃣ Vérification
```bash
# Vérifier que tout est OK
python check_config.py
```

## Première utilisation

### Récupérer les cinémas
```bash
python ugc.py --cinemas
```
⏱️ **Durée** : ~5-10 minutes (une seule fois)

### Récupérer les séances
```bash
python ugc.py --showtimes
```
⏱️ **Durée** : ~2-5 minutes

### Lancer l'API
```bash
uvicorn api:app --reload
```

Ouvrir : http://localhost:8000/showtimes

## Utilisation quotidienne

### Mise à jour des séances
```bash
# Chaque jour
python ugc.py --showtimes
```

### Mise à jour des cinémas
```bash
# Une fois par mois
python ugc.py --cinemas
```

## Automatisation

### Avec Cron (Linux/Mac)
```bash
crontab -e
```

Ajouter :
```cron
# Séances tous les jours à 6h
0 6 * * * cd /path/to/allocinoche && python ugc.py --showtimes

# Cinémas le 1er du mois à 3h
0 3 1 * * cd /path/to/allocinoche && python ugc.py --cinemas
```

### Avec Task Scheduler (Windows)
1. Ouvrir "Planificateur de tâches"
2. Créer une tâche de base
3. Déclencheur : Quotidien à 6h00
4. Action : `python C:\path\to\allocinoche\ugc.py --showtimes`

## Commandes utiles

### Diagnostics
```bash
# Vérifier la config
python check_config.py

# Afficher les stats
python cleanup.py --stats

# Trouver les films orphelins
python cleanup.py --orphaned
```

### Nettoyage
```bash
# Simuler le nettoyage
python cleanup.py --clean

# Nettoyer réellement
python cleanup.py --clean --confirm

# Nettoyer > 14 jours
python cleanup.py --clean --days 14 --confirm
```

### API
```bash
# Démarrer l'API
uvicorn api:app --reload

# Tester
curl http://localhost:8000/health
curl http://localhost:8000/showtimes
curl http://localhost:8000/showtimes?day=2025-01-07
```

## Résolution de problèmes

### "SUPABASE_URL not defined"
➜ Vérifier que `.env` existe et contient les bonnes valeurs

### "Groupe UGC non trouvé"
➜ Exécuter : `python ugc.py --cinemas`

### "Aucun cinéma trouvé"
➜ Exécuter : `python ugc.py --cinemas`

### "Table groups n'existe pas"
➜ Exécuter le script SQL : `migrations/001_add_groups_table.sql`

### Timeout Playwright
➜ Vérifier votre connexion internet  
➜ Réessayer plus tard

## Aide

### Commandes d'aide
```bash
# Aide générale
python ugc.py --help

# Aide nettoyage
python cleanup.py --help
```

### Documentation
- 📘 **README.md** : Documentation complète
- 🔄 **MIGRATION_GUIDE.md** : Si vous migrez depuis v1.x
- 💻 **DEVELOPER.md** : Pour les développeurs
- 📝 **CHANGELOG.md** : Historique des versions

### Support
- 🐛 Issues GitHub
- 💬 Discussions GitHub
- 📧 Contact maintainer

## Checklist de démarrage

- [ ] Python 3.11+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Playwright installé (`playwright install chromium`)
- [ ] Fichier `.env` configuré
- [ ] Script SQL de migration exécuté
- [ ] `check_config.py` validé ✅
- [ ] Cinémas récupérés (`--cinemas`)
- [ ] Séances récupérées (`--showtimes`)
- [ ] API testée (optionnel)
- [ ] Automatisation configurée (optionnel)

## Prêt à démarrer !

```bash
# Tout en une fois (première installation)
python ugc.py --all

# Puis quotidiennement
python ugc.py --showtimes
```

**Bon scraping ! 🎬**

---

Besoin d'aide ? Consultez le [README.md](README.md) complet.
