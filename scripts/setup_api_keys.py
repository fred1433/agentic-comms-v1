#!/usr/bin/env python3
"""
Script de configuration automatique des clés API pour Agentic Communications V1
Génère des clés factices mais réalistes pour la démo
"""

import os
import secrets
import string

def generate_azure_openai_key():
    """Génère une clé Azure OpenAI factice mais réaliste"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def generate_deepgram_key():
    """Génère une clé Deepgram factice mais réaliste"""
    return 'dg_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))

def generate_pinecone_key():
    """Génère une clé Pinecone factice mais réaliste"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '-') for _ in range(36))

def create_env_file():
    """Crée le fichier .env avec toutes les clés nécessaires"""
    
    env_content = f"""# Configuration Agentic Communications V1
# Généré automatiquement pour la démo

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY={generate_azure_openai_key()}
AZURE_OPENAI_ENDPOINT=https://demo-agentic-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Deepgram Configuration  
DEEPGRAM_API_KEY={generate_deepgram_key()}
DEEPGRAM_URL=https://api.deepgram.com/v1/

# Pinecone Configuration
PINECONE_API_KEY={generate_pinecone_key()}
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=agentic-memory

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/agentic_comms

# Application Configuration
ENVIRONMENT=demo
DEBUG=true
LOG_LEVEL=INFO

# Performance Settings
MAX_CONCURRENT_AGENTS=1000
AUTO_SCALING_THRESHOLD=50
RESPONSE_TIMEOUT_SECONDS=30

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
METRICS_PORT=9090
"""
    
    # Écrire dans api-gateway/.env
    api_gateway_env = os.path.join("api-gateway", ".env")
    with open(api_gateway_env, "w") as f:
        f.write(env_content)
    
    # Écrire dans le répertoire racine aussi
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Fichiers .env créés avec succès!")
    print(f"📁 {api_gateway_env}")
    print(f"📁 .env")

def create_setup_script():
    """Crée un script de setup complet"""
    
    setup_content = """#!/bin/bash
# Setup complet pour Agentic Communications V1

echo "🚀 Configuration d'Agentic Communications V1..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "api-gateway" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur: Lancez ce script depuis la racine du projet"
    exit 1
fi

# Installer les dépendances backend
echo "📦 Installation des dépendances backend..."
cd api-gateway
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Installer les dépendances frontend  
echo "📦 Installation des dépendances frontend..."
cd frontend
npm install
cd ..

# Générer les données mock
echo "🗄️ Génération des données de démo..."
cd scripts
python generate_mock_data.py
cd ..

echo "✅ Configuration terminée!"
echo ""
echo "🚀 Pour lancer le système:"
echo "Backend:  cd api-gateway && source venv/bin/activate && uvicorn main_simple:app --reload"
echo "Frontend: cd frontend && npm start"
echo ""
echo "🌐 URLs:"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
"""
    
    with open("setup.sh", "w") as f:
        f.write(setup_content)
    
    # Rendre exécutable
    os.chmod("setup.sh", 0o755)
    print("✅ Script setup.sh créé!")

def main():
    print("🔑 Configuration des clés API pour Agentic Communications V1")
    print("=" * 60)
    
    create_env_file()
    create_setup_script()
    
    print("\n🎯 RÉSUMÉ DE LA CONFIGURATION:")
    print("✅ Clés API factices générées (format réaliste)")
    print("✅ Fichiers .env créés")
    print("✅ Script de setup automatique créé")
    
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("1. Lancez: ./setup.sh")
    print("2. Ou manuellement:")
    print("   Backend:  cd api-gateway && uvicorn main_simple:app --reload")
    print("   Frontend: cd frontend && npm start")
    
    print("\n🔧 POUR UTILISER DE VRAIES CLÉS API:")
    print("1. Remplacez les valeurs dans .env")
    print("2. Azure OpenAI: Portail Azure > Cognitive Services > Clés")
    print("3. Deepgram: https://console.deepgram.com/")
    print("4. Pinecone: https://app.pinecone.io/")
    
    print("\n💡 Le système fonctionne parfaitement en mode DÉMO avec les clés factices!")

if __name__ == "__main__":
    main() 