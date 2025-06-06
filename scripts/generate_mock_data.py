#!/usr/bin/env python3
"""
Script de génération de données mock pour Agentic Communications
Génère 500 emails, 300 chats, 50 échantillons vocaux
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

EMAILS_COUNT = 500
CHATS_COUNT = 300
VOICE_SAMPLES_COUNT = 50

OUTPUT_DIR = Path("../data/mock")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Templates de données
# ═══════════════════════════════════════════════════════════════════════════════

EMAIL_SUBJECTS = [
    "Problème de connexion urgent",
    "Demande de remboursement",
    "Question sur l'abonnement premium", 
    "Modification de profil impossible",
    "Erreur de paiement",
    "Commande non reçue",
    "Bug dans l'application",
    "Demande d'assistance technique",
    "Facture incorrecte",
    "Résiliation de compte",
    "Mot de passe oublié",
    "Changement d'adresse email",
    "Support produit",
    "Réclamation service client",
    "Information sur les tarifs"
]

CHAT_MESSAGES = [
    "Bonjour, j'ai un problème avec mon compte",
    "Comment puis-je réinitialiser mon mot de passe ?",
    "Je n'arrive pas à me connecter depuis ce matin",
    "Y a-t-il des frais pour l'abonnement premium ?",
    "Ma commande #12345 n'est pas arrivée",
    "Comment puis-je modifier mes informations personnelles ?",
    "Le paiement a été refusé, que faire ?",
    "Où puis-je télécharger l'app mobile ?",
    "Je souhaite annuler ma commande",
    "Comment contacter le support technique ?",
    "Puis-je obtenir un remboursement ?",
    "L'application plante quand j'ouvre mes messages",
    "Ma facture semble incorrecte",
    "Je veux supprimer mon compte",
    "Comment changer mon email ?"
]

VOICE_PROMPTS = [
    "Comment réinitialiser mon mot de passe ?",
    "Quels sont vos horaires d'ouverture ?", 
    "Je souhaite connaître le statut de ma commande",
    "Comment contacter le support ?",
    "Y a-t-il des frais de livraison ?",
    "Où est mon colis ?",
    "Comment annuler mon abonnement ?",
    "Problème avec l'application mobile",
    "Ma carte a été refusée",
    "Je veux parler à un agent humain"
]

USER_NAMES = [
    "Marie Dubois", "Pierre Martin", "Sophie Laurent", "Jean Moreau",
    "Isabelle Roux", "Michel Bernard", "Nathalie Petit", "François Durand",
    "Catherine Thomas", "Philippe Robert", "Sylvie Richard", "Alain Lefebvre",
    "Valérie Morel", "Christophe Simon", "Martine Garcia", "Laurent Fournier"
]

# ═══════════════════════════════════════════════════════════════════════════════
# Générateurs
# ═══════════════════════════════════════════════════════════════════════════════

def generate_email_data():
    """Génère les données d'emails mock"""
    emails = []
    
    for i in range(EMAILS_COUNT):
        user_name = random.choice(USER_NAMES)
        email_domain = random.choice(["gmail.com", "outlook.com", "yahoo.fr", "orange.fr"])
        from_email = f"{user_name.lower().replace(' ', '.')}.{random.randint(1, 999)}@{email_domain}"
        
        subject = random.choice(EMAIL_SUBJECTS)
        
        # Contenu plus élaboré selon le sujet
        if "connexion" in subject.lower():
            content = f"Bonjour,\n\nJe rencontre des difficultés pour me connecter à mon compte depuis {random.randint(1, 7)} jours. L'erreur affichée est 'Identifiants incorrects' alors que je suis sûr(e) de mes informations.\n\nPouvez-vous m'aider rapidement ?\n\nCordialement,\n{user_name}"
        elif "remboursement" in subject.lower():
            order_id = f"CMD{random.randint(10000, 99999)}"
            content = f"Bonjour,\n\nJe souhaite demander le remboursement de ma commande {order_id} du {(datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%d/%m/%Y')}.\n\nLe produit ne correspond pas à mes attentes.\n\nMerci de votre compréhension.\n\n{user_name}"
        else:
            content = f"Bonjour,\n\n{random.choice(CHAT_MESSAGES)}\n\nMerci de votre aide.\n\nCordialement,\n{user_name}"
        
        email = {
            "id": str(uuid.uuid4()),
            "subject": subject,
            "content": content,
            "from_email": from_email,
            "to_email": "support@company.com",
            "user_name": user_name,
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat(),
            "status": random.choice(["pending", "processed", "resolved"]),
            "priority": random.choice(["low", "medium", "high"]),
            "category": random.choice(["technical", "billing", "general", "product"])
        }
        
        emails.append(email)
    
    return emails

def generate_chat_data():
    """Génère les données de chat mock"""
    chats = []
    
    for i in range(CHATS_COUNT):
        user_name = random.choice(USER_NAMES)
        message = random.choice(CHAT_MESSAGES)
        
        # Ajout de variantes
        if random.random() < 0.3:
            message += f" (urgent - client VIP)"
        
        chat = {
            "id": str(uuid.uuid4()),
            "content": message,
            "user_id": f"user_{random.randint(1000, 9999)}",
            "user_name": user_name,
            "channel": "chat",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat(),
            "session_id": str(uuid.uuid4()),
            "status": random.choice(["active", "resolved", "escalated"]),
            "response_time_ms": random.randint(800, 4500),
            "confidence_score": random.uniform(0.65, 0.95),
            "agent_id": f"agent_{random.randint(1, 50)}"
        }
        
        chats.append(chat)
    
    return chats

def generate_voice_data():
    """Génère les métadonnées des échantillons vocaux mock"""
    voice_samples = []
    
    for i in range(VOICE_SAMPLES_COUNT):
        user_name = random.choice(USER_NAMES)
        prompt = random.choice(VOICE_PROMPTS)
        
        voice = {
            "id": str(uuid.uuid4()),
            "transcript": prompt,
            "user_id": f"user_{random.randint(1000, 9999)}",
            "user_name": user_name,
            "channel": "voice",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat(),
            "duration_seconds": random.uniform(8, 45),
            "audio_format": "wav",
            "sample_rate": 16000,
            "language": "fr-FR",
            "status": random.choice(["processed", "processing", "transcribed"]),
            "stt_confidence": random.uniform(0.85, 0.98),
            "response_latency_ms": random.randint(600, 1200),
            "tts_generated": True,
            "agent_id": f"agent_{random.randint(1, 50)}"
        }
        
        voice_samples.append(voice)
    
    return voice_samples

def generate_agent_performance():
    """Génère les données de performance des agents"""
    agents = []
    
    for i in range(50):
        agent_id = f"agent_{i+1:03d}"
        
        agent = {
            "id": agent_id,
            "name": f"Agent {i+1}",
            "status": random.choice(["idle", "busy", "training", "offline"]),
            "specialization": random.choice(["general", "technical", "billing", "sales"]),
            "current_load": random.randint(0, 10),
            "max_load": 10,
            "total_processed": random.randint(500, 5000),
            "successful_resolutions": random.randint(400, 4500),
            "escalations": random.randint(10, 200),
            "errors": random.randint(0, 50),
            "uptime_hours": random.uniform(720, 744),  # ~30 jours
            "last_activity": (datetime.now() - timedelta(minutes=random.randint(0, 180))).isoformat(),
            "success_rate": random.uniform(0.82, 0.97),
            "average_response_time_ms": random.randint(1200, 3800),
            "average_confidence_score": random.uniform(0.75, 0.92),
            "languages": random.sample(["fr", "en", "es", "de", "it"], random.randint(1, 3)),
            "certifications": random.sample(["Azure AI", "Customer Service", "Technical Support"], random.randint(1, 3))
        }
        
        agents.append(agent)
    
    return agents

def generate_system_metrics():
    """Génère les métriques système"""
    return {
        "timestamp": datetime.now().isoformat(),
        "total_agents": 50,
        "active_agents": random.randint(35, 48),
        "total_conversations": EMAILS_COUNT + CHATS_COUNT + VOICE_SAMPLES_COUNT,
        "processed_today": random.randint(800, 1200),
        "average_response_time_ms": random.randint(1800, 2800),
        "resolution_rate": random.uniform(0.78, 0.87),
        "escalation_rate": random.uniform(0.08, 0.18),
        "system_uptime_seconds": random.randint(86400 * 25, 86400 * 30),
        "cpu_usage_percent": random.uniform(25, 75),
        "memory_usage_percent": random.uniform(40, 80),
        "redis_connections": random.randint(100, 300),
        "database_connections": random.randint(20, 50)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# Génération et sauvegarde
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Génère toutes les données mock"""
    print("🚀 Génération des données mock pour Agentic Communications...")
    
    # Génération des données
    print(f"📧 Génération de {EMAILS_COUNT} emails...")
    emails = generate_email_data()
    
    print(f"💬 Génération de {CHATS_COUNT} conversations chat...")
    chats = generate_chat_data()
    
    print(f"🎤 Génération de {VOICE_SAMPLES_COUNT} échantillons vocaux...")
    voice_samples = generate_voice_data()
    
    print("🤖 Génération des données d'agents...")
    agents = generate_agent_performance()
    
    print("📊 Génération des métriques système...")
    metrics = generate_system_metrics()
    
    # Sauvegarde
    print("💾 Sauvegarde des fichiers...")
    
    with open(OUTPUT_DIR / "emails.json", "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)
    
    with open(OUTPUT_DIR / "chats.json", "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)
    
    with open(OUTPUT_DIR / "voice_samples.json", "w", encoding="utf-8") as f:
        json.dump(voice_samples, f, indent=2, ensure_ascii=False)
    
    with open(OUTPUT_DIR / "agents.json", "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
    
    with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    # Fichier de données consolidées
    consolidated = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "emails": len(emails),
            "chats": len(chats), 
            "voice_samples": len(voice_samples),
            "agents": len(agents)
        },
        "emails": emails[:10],  # Échantillon
        "chats": chats[:10],    # Échantillon
        "voice_samples": voice_samples[:5],  # Échantillon
        "agents": agents[:5],   # Échantillon
        "metrics": metrics
    }
    
    with open(OUTPUT_DIR / "demo_data.json", "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    print("✅ Génération terminée !")
    print(f"📁 Fichiers sauvegardés dans : {OUTPUT_DIR.absolute()}")
    print(f"📊 Total: {len(emails)} emails, {len(chats)} chats, {len(voice_samples)} échantillons vocaux")
    print(f"🤖 {len(agents)} agents configurés")

if __name__ == "__main__":
    main() 