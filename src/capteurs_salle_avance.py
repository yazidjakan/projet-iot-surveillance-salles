import paho.mqtt.client as mqtt
import json
import time
import random
import csv
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuration MQTT
BROKER = "localhost"
PORT = 1883
TOPIC_BASE = "salle_classe/"

# Configuration Email (à personnaliser)
EMAIL_ENABLED = False  # Mettez True pour activer les emails
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "votre_email@gmail.com"
EMAIL_PASSWORD = "votre_mot_de_passe_app"
EMAIL_TO = "destinataire@gmail.com"

# Fichier CSV pour l'historique
CSV_FILE = "historique_salle.csv"

# Statistiques quotidiennes
stats_journalieres = {
    "temperature": [],
    "luminosite": [],
    "presence": []
}

def initialiser_csv():
    """Crée le fichier CSV s'il n'existe pas"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Presence', 'Temperature', 'Luminosite', 'Salle_Occupee'])
        print(f"✅ Fichier CSV créé : {CSV_FILE}")

def enregistrer_donnees_csv(donnees):
    """Enregistre les données dans le fichier CSV"""
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                donnees['timestamp'],
                donnees['presence'],
                donnees['temperature'],
                donnees['luminosite'],
                donnees['salle_occupee']
            ])
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement CSV: {e}")

def calculer_statistiques():
    """Calcule les statistiques quotidiennes"""
    if len(stats_journalieres['temperature']) == 0:
        return None
    
    stats = {
        "temperature": {
            "moyenne": round(sum(stats_journalieres['temperature']) / len(stats_journalieres['temperature']), 1),
            "min": min(stats_journalieres['temperature']),
            "max": max(stats_journalieres['temperature'])
        },
        "luminosite": {
            "moyenne": round(sum(stats_journalieres['luminosite']) / len(stats_journalieres['luminosite']), 0),
            "min": min(stats_journalieres['luminosite']),
            "max": max(stats_journalieres['luminosite'])
        },
        "presence": {
            "moyenne": round(sum(stats_journalieres['presence']) / len(stats_journalieres['presence']), 1),
            "max": max(stats_journalieres['presence'])
        }
    }
    return stats

def envoyer_email_alerte(sujet, message):
    """Envoie un email d'alerte"""
    if not EMAIL_ENABLED:
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = sujet
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        
        print(f"📧 Email envoyé : {sujet}")
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")

def generer_donnees_capteurs():
    """Génère des données réalistes pour une salle de classe"""
    
    # Capteur de présence (0 = vide, 1-30 = nombre d'étudiants)
    # Simulation selon l'heure de la journée
    heure = datetime.now().hour
    if 8 <= heure <= 18:  # Heures de cours
        presence = random.randint(5, 30)
    else:  # Hors cours
        presence = random.randint(0, 3)
    
    # Température (18-26°C, plus élevée si salle occupée)
    temp_base = 22
    temp_variation = (presence / 30) * 2  # +2°C max si salle pleine
    temperature = round(temp_base + temp_variation + random.uniform(-1, 1), 1)
    
    # Luminosité (0-1000 lux)
    # Plus élevée si salle occupée (lumières allumées)
    if presence > 0:
        luminosite = random.randint(400, 800)
    else:
        luminosite = random.randint(100, 400)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "presence": presence,
        "temperature": temperature,
        "luminosite": luminosite,
        "salle_occupee": presence > 0
    }

def verifier_alertes(donnees):
    """Vérifie les conditions d'alerte et envoie des notifications"""
    alertes = []
    
    # Alerte température trop élevée
    if donnees['temperature'] > 25:
        msg = f"⚠️ Température élevée: {donnees['temperature']}°C"
        alertes.append(msg)
        envoyer_email_alerte("Alerte Température Élevée", msg)
    
    # Alerte température trop basse
    if donnees['temperature'] < 19:
        msg = f"❄️ Température basse: {donnees['temperature']}°C"
        alertes.append(msg)
        envoyer_email_alerte("Alerte Température Basse", msg)
    
    # Alerte luminosité insuffisante si salle occupée
    if donnees['salle_occupee'] and donnees['luminosite'] < 300:
        msg = f"🔦 Luminosité insuffisante: {donnees['luminosite']} lux"
        alertes.append(msg)
        envoyer_email_alerte("Alerte Luminosité Faible", msg)
    
    # Alerte salle presque pleine
    if donnees['presence'] > 25:
        msg = f"👥 Salle presque pleine: {donnees['presence']} personnes"
        alertes.append(msg)
    
    return alertes

def controle_automatique(donnees):
    """Simule le contrôle automatique des équipements"""
    actions = []
    
    # Climatisation
    if donnees['temperature'] > 24:
        actions.append("❄️ Climatisation activée")
    elif donnees['temperature'] < 20:
        actions.append("🔥 Chauffage activé")
    else:
        actions.append("✅ Température optimale")
    
    # Éclairage
    if donnees['salle_occupee'] and donnees['luminosite'] < 400:
        actions.append("💡 Lumières allumées")
    elif not donnees['salle_occupee']:
        actions.append("🌙 Lumières éteintes (économie d'énergie)")
    else:
        actions.append("☀️ Lumière naturelle suffisante")
    
    return actions

# Fonction de connexion au broker
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connecté au broker MQTT")
    else:
        print(f"❌ Échec de connexion. Code: {reason_code}")

# Initialisation
initialiser_csv()

# Création du client MQTT
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="Capteur_Salle_A101"
)
client.on_connect = on_connect

print("🔌 Connexion au broker Mosquitto...")
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    print("📡 Début de l'envoi des données...")
    print(f"💾 Enregistrement dans : {CSV_FILE}")
    print(f"📧 Emails : {'Activés' if EMAIL_ENABLED else 'Désactivés'}")
    print("   (Appuyez sur Ctrl+C pour arrêter)\n")
    
    compteur = 0
    
    while True:
        # Générer les données
        donnees = generer_donnees_capteurs()
        
        # Enregistrer dans le CSV
        enregistrer_donnees_csv(donnees)
        
        # Ajouter aux statistiques
        stats_journalieres['temperature'].append(donnees['temperature'])
        stats_journalieres['luminosite'].append(donnees['luminosite'])
        stats_journalieres['presence'].append(donnees['presence'])
        
        # Publier sur MQTT
        client.publish(f"{TOPIC_BASE}presence", donnees["presence"])
        client.publish(f"{TOPIC_BASE}temperature", donnees["temperature"])
        client.publish(f"{TOPIC_BASE}luminosite", donnees["luminosite"])
        client.publish(f"{TOPIC_BASE}donnees_completes", json.dumps(donnees))
        
        # Vérifier les alertes
        alertes = verifier_alertes(donnees)
        
        # Contrôle automatique
        actions = controle_automatique(donnees)
        
        # Publier les actions de contrôle
        client.publish(f"{TOPIC_BASE}controle", json.dumps({"actions": actions}))
        
        # Affichage console
        print(f"⏰ {donnees['timestamp']}")
        print(f"   👥 Présence: {donnees['presence']} personnes")
        print(f"   🌡️  Température: {donnees['temperature']}°C")
        print(f"   💡 Luminosité: {donnees['luminosite']} lux")
        print(f"   📊 État: {'🟢 Occupée' if donnees['salle_occupee'] else '🔴 Vide'}")
        
        if alertes:
            print(f"   🚨 Alertes: {', '.join(alertes)}")
        
        print(f"   ⚙️  Actions: {', '.join(actions)}")
        
        # Afficher les statistiques toutes les 10 mesures
        compteur += 1
        if compteur % 10 == 0:
            stats = calculer_statistiques()
            if stats:
                print(f"\n📊 STATISTIQUES (dernières {len(stats_journalieres['temperature'])} mesures):")
                print(f"   Température: {stats['temperature']['min']}°C - {stats['temperature']['max']}°C (moy: {stats['temperature']['moyenne']}°C)")
                print(f"   Luminosité: {stats['luminosite']['min']}-{stats['luminosite']['max']} lux (moy: {stats['luminosite']['moyenne']} lux)")
                print(f"   Présence max: {stats['presence']['max']} personnes (moy: {stats['presence']['moyenne']})")
                
                # Publier les statistiques
                client.publish(f"{TOPIC_BASE}statistiques", json.dumps(stats))
        
        print()
        time.sleep(2)  # Envoie toutes les 5 secondes
        
except KeyboardInterrupt:
    print("\n🛑 Arrêt des capteurs...")
    
    # Afficher les statistiques finales
    stats = calculer_statistiques()
    if stats:
        print("\n📊 STATISTIQUES FINALES:")
        print(f"   Température: {stats['temperature']['min']}°C - {stats['temperature']['max']}°C (moy: {stats['temperature']['moyenne']}°C)")
        print(f"   Luminosité: {stats['luminosite']['min']}-{stats['luminosite']['max']} lux (moy: {stats['luminosite']['moyenne']} lux)")
        print(f"   Présence max: {stats['presence']['max']} personnes (moy: {stats['presence']['moyenne']})")
    
    print(f"💾 Données enregistrées dans : {CSV_FILE}")
    
    client.loop_stop()
    client.disconnect()
    print("✅ Déconnecté proprement")
except Exception as e:
    print(f"❌ Erreur: {e}")
    client.loop_stop()
    client.disconnect()