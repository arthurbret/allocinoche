# Utilisation de l'image officielle Playwright qui contient Python et les navigateurs
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Répertoire de travail
WORKDIR /app

# Copie des fichiers
COPY requirements.txt .
COPY main.py .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installation des navigateurs (au cas où l'image de base ne les a pas tous liés)
RUN playwright install chromium

# Commande par défaut
CMD ["python", "main.py"]
