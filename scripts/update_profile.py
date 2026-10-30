import sys
import re

def update_config():
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update specialties
    old_spec_pattern = r'    specialties_fr: List\[str\] = \[\s*"Systèmes Embarqués[^\]]+\]\s*specialties_en: List\[str\] = \[\s*"Embedded Systems[^\]]+\]'
    new_spec = '''    specialties_fr: List[str] = [
        "Génie Électrique & Énergies Renouvelables (Dimensionnement Solaire 1 MW, Réseaux MT/BT, Postes HTA, PVsyst)",
        "Systèmes Embarqués (STM32, ESP32, FreeRTOS, C/C++)",
        "Robotique Autonome & Drones (ArduPilot, Pixhawk, YOLOv8, OpenCV, ROS, Betaflight)",
        "Automatisme Industriel & SCADA (Schneider M580, Siemens TIA Portal, Ignition, Modbus TCP)",
        "R&D Mécatronique & Prototypage (SolidWorks, KiCad, Châssis Carbone CNC, Impression 3D)"
    ]
    
    specialties_en: List[str] = [
        "Electrical Engineering & Renewable Energy (1 MW Solar PV Sizing, MV/LV Substation, PVsyst, Power Distribution)",
        "Embedded Systems (STM32, ESP32, FreeRTOS, C/C++)",
        "Autonomous Robotics & Drones (ArduPilot, Pixhawk, YOLOv8, Computer Vision, ROS, Betaflight)",
        "Industrial Automation & SCADA (Schneider M580, Siemens TIA, Ignition, Modbus TCP)",
        "Mechatronics R&D & Prototyping (SolidWorks, KiCad, CNC Carbon Frames, 3D Printing)"
    ]'''
    content = re.sub(old_spec_pattern, new_spec, content, flags=re.DOTALL)

    # 2. Add 1 MW Solar Plant to key_projects if not already there
    if "Centrale Solaire Photovoltaïque de 1 MW" not in content:
        solar_block = '''        {
            "name": "Étude & Dimensionnement d'une Centrale Solaire Photovoltaïque de 1 MW",
            "stack": "Génie Électrique, PVsyst, Calpinage Solaire, Onduleurs de Branche/Centraux, Raccordement MT/BT, Schémas Unifilaires",
            "desc": "Étude technico-économique et dimensionnement complet d'une centrale solaire PV de 1 MW raccordée au réseau moyenne tension : calpinage, bilan de puissance, choix des onduleurs et transformateurs, optimisation du productible et modélisation des pertes."
        },
'''
        content = content.replace('key_projects: List[Dict[str, str]] = [\n', 'key_projects: List[Dict[str, str]] = [\n' + solar_block)

    # 3. Update SkyPharma description
    content = re.sub(
        r'\{\s*"name":\s*"SkyPharma[^}]+H-Bot[^}]+milieu hospitalier[^}]+\},',
        '''{
            "name": "SkyPharma – Robot ASRS (Automated Storage & Retrieval System) Pharmaceutique",
            "stack": "Robot Cartésien Cinématique H-Bot, Contrôle-Commande Temps Réel, Python, SQLite, IHM Web, Motorisation Pas-à-Pas",
            "desc": "Robot ASRS automatisé à cinématique H-Bot pour la dispensation, l'inventaire dynamique et la délivrance ultra-sécurisée de médicaments en milieu hospitalier et officines."
        },''',
        content,
        flags=re.DOTALL
    )

    # 4. Update leadership & awards
    content = re.sub(
        r'leadership_and_awards: List\[str\] = \[[^\]]+\]',
        '''leadership_and_awards: List[str] = [
        "Ex-Président & Team Leader du Club RoboThings (FST Mohammedia) : Leadership d'équipe d'ingénierie, gestion de projets mécatroniques et organisation d'événements technologiques.",
        "1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM) – Projet d'innovation et technologies émergentes.",
        "2e Prix Compétition Nationale de Robotique (ENSA Khouribga / ENIM Rabat) – Performance robotique autonome.",
        "3e Prix Compétition Nationale de Robotique (EMI Rabat / ENSA El Jadida) – Défis robotiques et ingénierie de pointe."
    ]''',
        content,
        flags=re.DOTALL
    )

    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("config.py successfully updated!")

if __name__ == '__main__':
    update_config()
