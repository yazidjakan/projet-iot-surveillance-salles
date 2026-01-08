import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime

# Configuration MQTT
BROKER = "localhost"
PORT = 1883

# Liste des salles à simuler
SALLES = ["A101", "A102", "B201", "B202", "C301"]

# Caractéristiques de chaque salle
CARACTERISTIQUES_SALLES = {
    "A101": {"capacite": 30, "etage": 1, "type": "cours"},
    "A102": {"capacite": 25, "etage": 1, "type": "cours"},
    "B201": {"capacite": 40, "etage": 2, "type": "amphitheatre"},
    "B202": {"capacite": 20, "etage": 2, "type": "tp"},
    "C301": {"capacite": 15, "etage": 3, "type": "reunion"}
}

def generer_donnees_salle(nom_salle):
    """Génère des données pour une salle spécifique"""
    carac = CARACTERISTIQUES_SALLES[nom_salle]
    
    # Présence selon le type de salle
    if carac["type"] == "amphitheatre":
        presence = random.randint(0, carac["capacite"])
    elif carac["type"] == "tp":
        presence = random.randint(0, min(20, carac["capacite"]))
    elif carac["type"] == "reunion":
        presence = random.randint(0, min(10, carac["capacite"]))
    else:
        presence = random.randint(0, carac["capacite"])
    
    # Température (varie selon l'étage - plus chaud en haut)
    temp_base = 21 + (carac["etage"] * 0.5)
    temp_variation = (presence / carac["capacite"]) * 2
    temperature = round(temp_base + temp_variation + random.uniform(-1, 1), 1)
    
    # Luminosité
    if presence > 0:
        luminosite = random.randint(400, 800)
    else:
        luminosite = random.randint(100, 400)
    
    # Taux d'occupation
    taux_occupation = round((presence / carac["capacite"]) * 100, 1)
    
    return {
        "salle": nom_salle,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "presence": presence,
        "capacite": carac["capacite"],
        "taux_occupation": taux_occupation,
        "temperature": temperature,
        "luminosite": luminosite,
        "etage": carac["etage"],
        "type": carac["type"],
        "salle_occupee": presence > 0
    }

def simuler_salle(client, nom_salle, stop_event, salles_data_list):
    """Simule les capteurs pour une salle spécifique"""
    topic_base = f"salles/{nom_salle}/"
    
    print(f"🏫 Démarrage simulation salle {nom_salle}")
    
    try:
        while not stop_event.is_set():
            donnees = generer_donnees_salle(nom_salle)
            
            # Publier sur différents topics
            client.publish(f"{topic_base}presence", donnees["presence"])
            client.publish(f"{topic_base}temperature", donnees["temperature"])
            client.publish(f"{topic_base}luminosite", donnees["luminosite"])
            client.publish(f"{topic_base}taux_occupation", donnees["taux_occupation"])
            client.publish(f"{topic_base}donnees_completes", json.dumps(donnees))
            
            # Topic global pour toutes les salles
            client.publish("salles/toutes", json.dumps(donnees))
            
            # Mettre à jour la liste partagée
            # Trouver l'index de cette salle ou l'ajouter
            salle_index = next((i for i, d in enumerate(salles_data_list) if d.get('salle') == nom_salle), None)
            if salle_index is not None:
                salles_data_list[salle_index] = donnees
            else:
                salles_data_list.append(donnees)
            
            # Affichage console
            statut = "🟢" if donnees['salle_occupee'] else "🔴"
            print(f"{statut} {nom_salle}: {donnees['presence']}/{donnees['capacite']} pers. | "
                  f"{donnees['temperature']}°C | {donnees['luminosite']} lux | "
                  f"Occupation: {donnees['taux_occupation']}%")
            
            time.sleep(7)  # Envoie toutes les 7 secondes
            
    except Exception as e:
        print(f"❌ Erreur salle {nom_salle}: {e}")

def calculer_stats_globales(client, salles_data_list, stop_event):
    """Calcule et publie les statistiques globales"""
    print("📊 Démarrage calcul statistiques globales")
    
    try:
        while not stop_event.is_set():
            time.sleep(7)  # Calcul toutes les 7 secondes (synchronisé avec l'envoi)
            
            if len(salles_data_list) > 0:
                # Calculer les stats à partir des dernières données de chaque salle
                total_presence = sum(d.get('presence', 0) for d in salles_data_list)
                total_capacite = sum(CARACTERISTIQUES_SALLES[s]['capacite'] for s in SALLES)
                taux_global = round((total_presence / total_capacite) * 100, 1)
                
                salles_occupees = sum(1 for d in salles_data_list if d.get('presence', 0) > 0)
                
                temp_moy = round(sum(d.get('temperature', 0) for d in salles_data_list) / len(salles_data_list), 1)
                lum_moy = round(sum(d.get('luminosite', 0) for d in salles_data_list) / len(salles_data_list), 0)
                
                stats = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_presence": total_presence,
                    "total_capacite": total_capacite,
                    "taux_occupation_global": taux_global,
                    "salles_occupees": salles_occupees,
                    "total_salles": len(SALLES),
                    "temperature_moyenne": temp_moy,
                    "luminosite_moyenne": lum_moy
                }
                
                client.publish("salles/statistiques_globales", json.dumps(stats))
                
                print(f"\n📊 STATS GLOBALES: {total_presence}/{total_capacite} pers. | "
                      f"{salles_occupees}/{len(SALLES)} salles occupées | "
                      f"Taux: {taux_global}% | Temp moy: {temp_moy}°C\n")
    
    except Exception as e:
        print(f"❌ Erreur stats globales: {e}")

# Fonction de connexion
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connecté au broker MQTT")
    else:
        print(f"❌ Échec de connexion. Code: {reason_code}")

# Création du client MQTT
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="Capteurs_Multi_Salles"
)
client.on_connect = on_connect

print("🔌 Connexion au broker Mosquitto...")
client.connect(BROKER, PORT, 60)
client.loop_start()

print(f"\n🏫 Simulation de {len(SALLES)} salles de classe")
print("=" * 80)
for salle, carac in CARACTERISTIQUES_SALLES.items():
    print(f"   {salle}: {carac['type']} - Capacité {carac['capacite']} pers. - Étage {carac['etage']}")
print("=" * 80)
print("   (Appuyez sur Ctrl+C pour arrêter)\n")

# Dictionnaire partagé pour stocker les dernières données de chaque salle
salles_data_list = []

# Event pour arrêter tous les threads
stop_event = threading.Event()

# Créer un thread pour chaque salle
threads = []
for salle in SALLES:
    thread = threading.Thread(target=simuler_salle, args=(client, salle, stop_event, salles_data_list))
    thread.daemon = True
    thread.start()
    threads.append(thread)
    time.sleep(0.5)  # Décalage pour éviter la surcharge

# Thread pour les statistiques globales
stats_thread = threading.Thread(target=calculer_stats_globales, args=(client, salles_data_list, stop_event))
stats_thread.daemon = True
stats_thread.start()

try:
    # Boucle principale pour mettre à jour salles_data
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n🛑 Arrêt de toutes les simulations...")
    stop_event.set()
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join(timeout=2)
    stats_thread.join(timeout=2)
    
    client.loop_stop()
    client.disconnect()
    print("✅ Tous les capteurs déconnectés proprement")