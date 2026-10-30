import os
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "outreach.db"

DATA_DIR.mkdir(exist_ok=True, parents=True)
UPLOADS_DIR.mkdir(exist_ok=True, parents=True)

class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=False, arbitrary_types_allowed=True)
    name: str = "Mohammed HSINY"
    title_fr: str = "Élève-Ingénieur en Génie Électrique & Contrôle Industriel"
    title_en: str = "Electrical Engineering & Industrial Control Student"
    school: str = "FST Mohammedia"
    promotion: str = "2024–2027"
    degree_fr: str = "Diplôme d'Ingénieur d'État en Génie Électrique et Contrôle Industriel"
    degree_en: str = "State Engineering Degree in Electrical Engineering & Industrial Control"
    target_role_fr: str = "Stage PFE (6 mois) à partir de Janvier 2027"
    target_role_en: str = "6-Month Master Graduation Internship (PFE) starting January 2027"
    email: str = "mohammedhsiny2@gmail.com"
    phone: str = "+212 611 424 571"
    portfolio_url: str = "https://portfolio-mohammed-hsiny-ux7z.vercel.app"
    linkedin_url: str = "https://linkedin.com/in/mohammed-hsiny"
    mobility_fr: str = "Mobilité nationale (Maroc) & internationale (France, Belgique, Suisse, Canada, USA, Europe)"
    mobility_en: str = "National & International Mobility (France, Belgium, Switzerland, Germany, US, Canada, Europe)"
    cv_fr_path: Optional[str] = None
    cv_en_path: Optional[str] = None
    portfolio_pdf_path: Optional[str] = None
    
    specialties_fr: List[str] = [
        "Systèmes Embarqués (STM32, ESP32, FreeRTOS, C/C++)",
        "Robotique Autonome & Drones (ArduPilot, YOLO, OpenCV, ROS, Betaflight)",
        "Automatisme Industriel & SCADA (M580, TIA Portal, Ignition, Modbus TCP)",
        "R&D, Prototypage Rapide (SolidWorks, KiCad, Électronique, Impression 3D)"
    ]
    
    specialties_en: List[str] = [
        "Embedded Systems (STM32, ESP32, FreeRTOS, C/C++)",
        "Robotics & Autonomous Drones (ArduPilot, YOLO, Computer Vision, ROS, Betaflight)",
        "Industrial Automation & SCADA (Schneider M580, Siemens TIA, Ignition, Modbus TCP)",
        "R&D, Rapid Prototyping (SolidWorks, KiCad, PCB Design, 3D Printing)"
    ]
    
    key_projects: List[Dict[str, str]] = [
        {
            "name": "Drone Quadricoptère d'Inspection Lignes HT",
            "stack": "ArduPilot, Pixhawk, YOLOv8, Python, OpenCV, MAVLink, Châssis Carbone CNC",
            "desc": "Conception intégrale et vol autonome d'un drone quadricoptère dédié à l'inspection de lignes haute tension avec détection d'anomalies (isolateurs défectueux, points chauds) en temps réel par vision IA embarquée."
        },
        {
            "name": "Projet Tawfir – Distribution Intelligente d'Eau & Détection de Fuites Invisibles",
            "stack": "Embedded AI, ESP32, STM32, Capteurs Débit/Pression, IoT, LoRaWAN",
            "desc": "Système embarqué IoT pour la gestion hydrique intelligente et la détection acoustique prédictive des micro-fuites invisibles dans les réseaux de distribution sous pression."
        },
        {
            "name": "Flotte Multi-Robots Autonomes & Plateforme ADAS",
            "stack": "FreeRTOS, ESP-NOW, Asservissement PID, Capteurs Ultrasons/ToF, Évitement d'obstacles",
            "desc": "Flotte de robots mobiles coopératifs communiquant en réseau maillé ultra-rapide avec régulation de vitesse adaptative et évitement d'obstacles dynamique."
        },
        {
            "name": "SkyPharma – Robot Cartésien H-Bot de Stockage Pharmaceutique",
            "stack": "Cinématique H-Bot, Contrôle-Commande Temps Réel, Python, SQLite, IHM Web",
            "desc": "Robot cartésien automatisé pour la gestion, l'indexation et la dispensation ultra-précise de médicaments en milieu hospitalier et officine."
        },
        {
            "name": "Bras Manipulateur Robotisé 6-DOF",
            "stack": "SolidWorks 3D, Cinématique Inverse (IK), STM32 C++, Asservissement Multiaxe",
            "desc": "Conception mécanique complète, cinématique directe et inverse, et asservissement en boucle fermée temps réel de 6 servomoteurs pour tâches de pick-and-place industrielles."
        },
        {
            "name": "Robot Suiveur de Ligne Haute Vitesse",
            "stack": "Microcontrôleur STM32, Barrette Capteurs Optiques, Régulation PID Rapide, PWM",
            "desc": "Robot mobile de compétition avec algorithmes avancés d'asservissement PID et de prédiction de courbure pour navigation haute vitesse."
        },
        {
            "name": "Prototype de Robot Humanoïde Bipède",
            "stack": "Robotique Bipède, Équilibrage Dynamique, IMU, Filtrage Kalman, C++",
            "desc": "Étude et prototypage d'une structure bipède articulée avec algorithmes de stabilisation d'assiette et contrôle de marche dynamique."
        },
        {
            "name": "Banc d'Essai Logique Séquentielle Câblée & Automatisme",
            "stack": "Électrotechnique Industrielle, Relais, Contacteurs, Sécurités Machine, Schémas Électriques",
            "desc": "Plateforme didactique et industrielle pour le câblage, le test et la validation de circuits de commande et de puissance sécurisés pour moteurs industriels."
        },
        {
            "name": "Drone FPV Freestyle & Long-Range 7 pouces",
            "stack": "Betaflight, INAV, Filtrage PID Giroscopique, Électronique de Puissance ESC/BLDC",
            "desc": "Dimensionnement de propulsion haute puissance, électronique de vol embarquée et réglage fin des filtres logiciels pour vol longue distance."
        }
    ]
    
    key_experiences: List[Dict[str, str]] = [
        {
            "company": "Groupe OCP (Direction Maroc Chimie)",
            "role": "Stage Ingénieur - Supervision SCADA Poste MT",
            "desc": "Architecture d'automatisme et télégestion des 12 cellules MT, configuration relais Sepam 80, Modicon M580 et SCADA Ignition."
        },
        {
            "company": "PAYPER PROD",
            "role": "Stage Technique - Inspection Drones Lignes HT",
            "desc": "Télépilotage DJI, acquisition de données aériennes d'infrastructures électriques et maintenance de la flotte."
        },
        {
            "company": "Ciments du Maroc (Heidelberg Materials)",
            "role": "Stage Technique - Maintenance Électrique & Instrumentation",
            "desc": "Diagnostic instrumentation process, étude démarreur électrolytique moteur asynchrone et GMAO."
        },
        {
            "company": "Marsa Maroc",
            "role": "Stage Ingénieur - Fiabilisation Grue Portuaire & IoT",
            "desc": "Analyse AMDEC/MTBF/MTTR grue G40T, automatisation du graissage et passerelle IoT 4G avec IHM SCADA."
        }
    ]
    
    leadership_and_awards: List[str] = [
        "Team Leader Projets Robotiques & Systèmes Autonomes (FST Mohammedia) : Conduite de projets mécatroniques et développement embarqué.",
        "1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM).",
        "2e Prix Compétition Nationale Robotique (ENSA Khouribga / ENIM Rabat).",
        "3e Prix Compétition Nationale (EMI Rabat / ENSA El Jadida)."
    ]

class SMTPSettings(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=False, arbitrary_types_allowed=True)
    provider: str = "gmail"  # gmail, outlook, custom
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = Field(default_factory=lambda: os.getenv("GMAIL_SENDER_EMAIL", "mohammedhsiny2@gmail.com"))
    sender_name: str = "Mohammed HSINY"
    app_password: str = Field(default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD", "pcgq jfir ahpt miwg"))
    min_delay_seconds: int = 4
    max_delay_seconds: int = 8
    daily_limit: int = 500

class LLMSettings(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=False, arbitrary_types_allowed=True)
    provider: str = "gemini"  # gemini, openai, groq, deepseek, ollama, openrouter
    api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = "gemini-3.5-flash"
    temperature: float = 0.6
    api_base_url: Optional[str] = None

FRANCOPHONE_COUNTRIES = {
    "france", "fr", "belgique", "belgium", "suisse", "switzerland", 
    "maroc", "morocco", "tunisie", "tunisia", "algerie", "algeria",
    "canada", "quebec", "luxembourg", "monaco", "senegal", "cote d'ivoire"
}

def is_francophone(country_or_location: str) -> bool:
    if not country_or_location:
        return True  # default to French for user context if unspecified
    cleaned = country_or_location.strip().lower()
    for country in FRANCOPHONE_COUNTRIES:
        if country in cleaned:
            return True
    return False

MASTER_SECURITY_PIN: str = os.getenv("SECURITY_PIN", "")
