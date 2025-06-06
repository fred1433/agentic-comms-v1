#!/bin/bash
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
