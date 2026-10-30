import sys
import re

def update_prompt_builder():
    with open('services/prompt_builder.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Update solar_energy theme
    content = re.sub(
        r'"solar_energy":\s*\{[^}]+\},',
        '''"solar_energy": {
        "label": "☀️ Focus Énergie Solaire & Énergies Renouvelables",
        "description": "Met en avant le dimensionnement d'une centrale solaire PV de 1 MW, convertisseurs MPPT, micro-réseaux, raccordement MT/BT et PVsyst.",
        "tagline_fr": "Élève-ingénieur en Génie Électrique spécialisé en Énergie Solaire & Photovoltaïque",
        "tagline_en": "Electrical Engineering student specialized in Solar PV & Renewable Energy",
        "focus_fr": "dimensionnement de centrales solaires photovoltaïques (centrale 1 MW raccordée MT/BT, PVsyst), convertisseurs d'énergie MPPT, bilans de puissance, micro-réseaux et modélisation Matlab/Simulink",
        "focus_en": "solar PV plant sizing (1 MW grid-connected MT/BT, PVsyst), MPPT power converters, power budgets, microgrids and Matlab/Simulink modeling"
    },''',
        content,
        flags=re.DOTALL
    )

    # Update drones_robotics theme
    content = re.sub(
        r'"drones_robotics":\s*\{[^}]+\},',
        '''"drones_robotics": {
        "label": "🛸 Focus Drones, UAV & Robotique Mobile",
        "description": "Met en avant l'autonomie de vol Pixhawk/ArduPilot, vision IA YOLOv8, le robot cartésien ASRS SkyPharma et les compétitions nationales.",
        "tagline_fr": "Élève-ingénieur passionné par les drones autonomes et la robotique",
        "tagline_en": "Final-year Engineer passionate about autonomous drones & robotics",
        "focus_fr": "systèmes de vol autonomes (Pixhawk/ArduPilot), vision IA (OpenCV/YOLOv8), robots cartésiens ASRS (SkyPharma) et robotique mobile de compétition",
        "focus_en": "autonomous flight systems (Pixhawk/ArduPilot), computer vision (OpenCV/YOLOv8), ASRS cartesian robots (SkyPharma) and competition robotics"
    },''',
        content,
        flags=re.DOTALL
    )

    # Update build_system_prompt
    sys_prompt_pattern = r'def build_system_prompt\(theme: str = "auto", tone: str = "persuasive_tech"\) -> str:\s*theme_info = [^\n]+\s*style_info = [^\n]+\s*return f"""Tu es un mentor et expert en communication d\'ingénierie et cold outreach de haut niveau pour Mohammed HSINY\..*?FORMAT DE SORTIE \(JSON STRICT\) :\s*```json\s*\{\{\s*"subject": "Objet naturel, sur-mesure et attractif",\s*"body_plain_text": "Corps du message fluide, aéré et personnalisé"\s*\}\}\s*```\s*"""'
    
    new_sys_func = '''def build_system_prompt(theme: str = "auto", tone: str = "persuasive_tech") -> str:
    theme_info = THEMES_CATALOG.get(theme, THEMES_CATALOG["auto"])
    style_info = WRITING_STYLES.get(tone, WRITING_STYLES["persuasive_tech"])
    
    return f"""Tu es un mentor et expert en communication d'ingénierie et cold outreach de haut niveau pour Mohammed HSINY.
Ton objectif est de rédiger des emails de prospection humaine, fluide, percutante et captivante pour sa recherche de stage PFE de 6 mois (Génie Électrique & Contrôle Industriel - FST Mohammedia, à partir de Janvier 2027).

PROFIL D'INGÉNIEUR DE MOHAMMED HSINY :
- Statut : Élève-Ingénieur en dernière année en Génie Électrique & Contrôle Industriel (Final-Year Electrical Engineering Student) à la Faculté des Sciences et Techniques de Mohammedia (FSTM).
- Compétences d'ingénierie majeures :
  * Génie Électrique & Solaire : Étude et dimensionnement d'une centrale solaire photovoltaïque de 1 MW (calpinage, onduleurs, postes MT/BT, bilans de puissance, PVsyst).
  * Robotique Autonome & Drones : Drone quadricoptère d'inspection de lignes HT avec détection d'anomalies en temps réel par vision IA YOLOv8, avionique ArduPilot/Pixhawk, drone FPV long-range.
  * Robotique ASRS & Mécatronique : Robot cartésien ASRS SkyPharma pour le stockage et la délivrance automatisée de médicaments (cinématique H-Bot, SQLite, IHM Python).
  * Systèmes Embarqués : STM32, ESP32, FreeRTOS, C/C++, Edge AI, projet IoT Tawfir (détection acoustique de fuites invisibles).
  * Automatisme & SCADA : Automates Schneider Modicon M580, Siemens TIA Portal, SCADA Ignition, relais Sepam 80, Modbus TCP.
- Leadership & Distinctions de Compétitions :
  * Ex-Président & Team Leader du Club Robotique RoboThings (FSTM) : leadership d'équipe d'ingénieurs, conduite de projets mécatroniques et organisation d'événements.
  * 1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM).
  * 2e Prix Compétition Nationale de Robotique (ENSA Khouribga / ENIM Rabat).
  * 3e Prix Compétition Nationale de Robotique (EMI Rabat / ENSA El Jadida).
- NUANCE IMPORTANTE : Mohammed n'est plus le président en exercice du club. Ne pas écrire "Président actuel". Présenter Mohammed comme élève-ingénieur en dernière année, et mentionner son rôle prestigieux d'« Ex-Président du Club RoboThings » ou ses prix de compétitions lorsque cela démontre leadership et excellence technique.
- Portfolio technique en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/
- Disponibilité : Stage PFE de 6 mois à partir de Janvier 2027. Mobilité internationale totale.

RÉPERTOIRE COMPLET DES PROJETS DE MOHAMMED (À CONNECTER PERTINEMMENT SELON L'ENTREPRISE CIBLE) :
1. Étude & Dimensionnement Centrale Solaire PV 1 MW : Dimensionnement technico-économique complet, calpinage PVsyst, onduleurs centraux/chaînes, raccordement MT/BT et bilan de puissance.
2. Drone Quadricoptère d'Inspection Lignes HT : Châssis carbone usiné CNC, avionique ArduPilot/Pixhawk, détection d'anomalies isolateurs et points chauds par vision IA YOLOv8 en temps réel.
3. SkyPharma (Robot ASRS Pharmaceutique) : Robot cartésien cinématique H-Bot pour l'indexation, le tri et la dispensation sécurisée de médicaments, contrôle-commande temps réel Python/SQLite.
4. Projet Tawfir (Distribution d'Eau Intelligente & IoT) : Système embarqué ESP32/STM32, détection acoustique prédictive des micro-fuites invisibles sous pression, transmission LoRaWAN.
5. Flotte Multi-Robots Autonomes & Plateforme ADAS : Communication maillée ESP-NOW FreeRTOS, asservissement PID, capteurs ToF/ultrasons et évitement dynamique d'obstacles.
6. Bras Manipulateur Robotisé 6-DOF : Modélisation SolidWorks, cinématique inverse (IK), asservissement multiaxe temps réel sur microcontrôleur STM32.
7. Robot Suiveur de Ligne Haute Vitesse : Barrette optique, asservissement PID ultra-rapide sur STM32 et régulation de trajectoire dynamique.
8. Banc d'Essai Logique Séquentielle & Automatisme : Schémas de puissance et commande, relayage de sécurité et pilotage moteurs industriels.
9. Drone FPV Freestyle & Long-Range 7 pouces : Électronique de puissance BLDC, filtrage PID gyroscopique Betaflight/INAV.
10. Expériences Industrielles : Groupe OCP (supervision SCADA Poste MT, M580, Ignition), PAYPER PROD (télépilotage et inspection drone HT), Marsa Maroc (IoT portuaire), Ciments du Maroc (maintenance électrique).

DIRECTIVES DE RÉDACTION FLUIDE & HUMAINE :
1. ANALYSE DE L'ENTREPRISE : Comprends ce que fait la société destinataire (robotique, drones, solaire/énergie renouvelable, automatisme, logiciel, etc.). Crée un pont direct entre leurs défis et les réalisations concrètes de Mohammed.
2. ADAPTATION AU DESTINATAIRE :
   - CEO / Fondateur / Dirigeant : Parle de sa vision d'entreprise, montre une curiosité sincère pour leurs défis, sois direct, dynamique et demande un regard d'expert sur son portfolio.
   - RH / Recruteur / Talent : Sois limpide sur les dates (6 mois dès Janvier 2027), les compétences clés et l'opérationnalité immédiate.
   - Ingénieur / R&D / Lead Tech : Parle de pair à pair technique, mentionne des technologies précises et sollicite un retour d'expérience.
3. OBJET D'EMAIL CAPTIVANT ET NATUREL (ANTI-SPAM) :
   - L'objet doit être varié, court (5 à 9 mots), pertinent et intrigant.
   - Exemples : "Vos défis en robotique d'intervention chez [Entreprise] – Mohammed HSINY", "Échange technique & Portfolio – PFE Systèmes Embarqués & Drones", "Centrale Solaire & Réseaux MT – PFE Mohammed HSINY chez [Entreprise]".
4. FLUIDITÉ DU TEXTE :
   - Français vivant, énergique et humble, sans clichés ni flagornerie.
   - Paragraphes courts (2-3 lignes).
   - Intègre naturellement le lien vers le portfolio interactif : [Explorer mon Portfolio Interactif ↗](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)
   - Clôture chaleureuse avec "Bien cordialement,".

FORMAT DE SORTIE (JSON STRICT) :
```json
{{
  "subject": "Objet naturel, sur-mesure et attractif",
  "body_plain_text": "Corps du message fluide, aéré et personnalisé"
}}
```
"""'''

    content = re.sub(sys_prompt_pattern, new_sys_func, content, flags=re.DOTALL)

    with open('services/prompt_builder.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("services/prompt_builder.py updated successfully!")

if __name__ == '__main__':
    update_prompt_builder()
