import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Configuration MQTT
BROKER = "localhost"
PORT = 1883
TOPIC_BASE = "salle_classe/"

# Simulation de capteurs
def generer_donnees_capteurs():
    """Génère des données réalistes pour une salle de classe"""
    
    # Capteur de présence (0 = vide, 1-30 = nombre d'étudiants)
    presence = random.randint(0, 30)
    
    # Température (18-26°C, plus élevée si salle occupée)
    temp_base = 22
    temp_variation = (presence / 30) * 2  # +2°C max si salle pleine
    temperature = round(temp_base + temp_variation + random.uniform(-1, 1), 1)
    
    # Luminosité (0-1000 lux)
    luminosite = random.randint(200, 800)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "presence": presence,
        "temperature": temperature,
        "luminosite": luminosite,
        "salle_occupee": presence > 0
    }

# Fonction de connexion au broker
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connecté au broker MQTT")
    else:
        print(f"❌ Échec de connexion. Code: {reason_code}")

# Création du client MQTT avec la nouvelle API v2
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
    print("   (Appuyez sur Ctrl+C pour arrêter)\n")
    
    while True:
        # Générer les données
        donnees = generer_donnees_capteurs()
        
        # Publier sur différents topics
        client.publish(f"{TOPIC_BASE}presence", donnees["presence"])
        client.publish(f"{TOPIC_BASE}temperature", donnees["temperature"])
        client.publish(f"{TOPIC_BASE}luminosite", donnees["luminosite"])
        client.publish(f"{TOPIC_BASE}donnees_completes", json.dumps(donnees))
        
        # Affichage console
        print(f"⏰ {donnees['timestamp']}")
        print(f"   👥 Présence: {donnees['presence']} personnes")
        print(f"   🌡️  Température: {donnees['temperature']}°C")
        print(f"   💡 Luminosité: {donnees['luminosite']} lux")
        print(f"   📊 État: {'🟢 Occupée' if donnees['salle_occupee'] else '🔴 Vide'}\n")
        
        time.sleep(5)  # Envoie toutes les 5 secondes
        
except KeyboardInterrupt:
    print("\n🛑 Arrêt des capteurs...")
    client.loop_stop()
    client.disconnect()
    print("✅ Déconnecté proprement")
except Exception as e:
    print(f"❌ Erreur: {e}")
    client.loop_stop()
    client.disconnect()