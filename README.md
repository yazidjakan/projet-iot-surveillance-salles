# Système IoT de Surveillance Intelligente des Salles de Classe

[![Python](https://img.shields.io/badge/Python-3.14.2-blue.svg)](https://www.python.org/)
[![MQTT](https://img.shields.io/badge/MQTT-3.1.1-green.svg)](https://mqtt.org/)
[![Node-RED](https://img.shields.io/badge/Node--RED-v4.1.2-red.svg)](https://nodered.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Système IoT complet basé sur MQTT pour surveiller en temps réel l'occupation et le confort des salles de classe, avec optimisation énergétique.

## Fonctionnalités

- **Surveillance temps réel** : Présence, température, luminosité
- **Dashboard interactif** : Jauges, graphiques, alertes
- **Multi-salles** : Gestion simultanée de 5+ salles
- **Alertes intelligentes** : Seuils configurables
- **Enregistrement CSV** : Historisation des données
- **Statistiques automatiques** : Moyenne, min, max
- **Configuration dynamique** : Modification en temps réel

## Architecture

```
Capteurs (Python) → MQTT (Mosquitto) → Node-RED → Dashboard Web
```

## Installation Rapide

### Prérequis

- Python 3.14+
- Node.js (pour Node-RED)
- Mosquitto MQTT Broker


## Utilisation

### Démarrage du Système Mono-Salle

```bash
# Terminal 1 : Vérifier Mosquitto
Get-Service -Name mosquitto  # Windows
# ou
systemctl status mosquitto    # Linux

# Terminal 2 : Lancer Node-RED
node-red

# Terminal 3 : Lancer les capteurs
cd src
python capteurs_salle_avance.py

# Ouvrir le dashboard
http://localhost:1880/ui
```

### Démarrage du Système Multi-Salles

```bash
# Lancer le script multi-salles à la place
python src/capteurs_multi_salles.py
```

## Technologies Utilisées

| Technologie | Version | Utilisation |
|------------|---------|-------------|
| Python | 3.14.2 | Simulation capteurs |
| Mosquitto | 2.0.22 | Broker MQTT |
| Node-RED | v4.1.2 | Traitement & visualisation |
| paho-mqtt | 2.0+ | Client MQTT Python |

##  Structure du Projet

```
projet-iot-surveillance-salles/
├── src/                          
│   ├── capteurs_salle.py
│   ├── capteurs_salle_avance.py
│   ├── capteurs_multi_salles.py
├── nodered/                      
│   └── flows_complete.json
├── data/                         
│   └── historique_salle.csv

## Contexte Académique

**Projet réalisé dans le cadre de :**
- Module : Internet des Objets (IoT)
- Master : Ingénierie de Développement Logiciel et Décisionnel
- Université Mohammed V - Faculté des Sciences de Rabat
- Année : 2025/2026

**Auteur :** JAKAN EL Yazid  
**Superviseur :** Mme. Hafssa BENABOUD
