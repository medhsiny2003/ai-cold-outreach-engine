import os
from pathlib import Path
from pydantic import BaseModel, Field
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
            "name": "Drone Quadricoptère d'Inspection HT",
            "stack": "ArduPilot, YOLO, Python, OpenCV",
            "desc": "Conception d'un drone autonome pour l'inspection de lignes haute tension avec détection d'anomalies en temps réel par IA."
        },
        {
            "name": "SkyPharma - Robot Cartésien H-Bot",
            "stack": "H-Bot, GRBL, PySerial, SQLite, Python",
            "desc": "Robot cartésien de gestion automatisée de stock avec interface web de supervision."
        },
        {
            "name": "Bras Manipulateur Robotisé 6 DOF",
            "stack": "SolidWorks, STM32, C++, Tkinter, Cinématique inverse",
            "desc": "Conception mécanique 3D et contrôle-commande embarqué temps réel sur microcontrôleur STM32."
        },
        {
            "name": "Flotte Multi-Robots Mobiles ADAS",
            "stack": "ESP-NOW, PID, FreeRTOS, Ultrasons",
            "desc": "Robots autonomes communicants avec asservissement PID et évitement d'obstacles en réseau maillé."
        },
        {
            "name": "Drone FPV Freestyle 7 pouces",
            "stack": "Betaflight, INAV, FPV, Moteurs Brushless",
            "desc": "Dimensionnement de propulsion, électronique embarquée et réglage fin des filtres PID de vol."
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
        "Président & Team Leader du Club RoboThings (FST Mohammedia) : Leadership, gestion d'équipe et conduite de projets robotiques.",
        "1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM).",
        "2e Prix Compétition Nationale Robotique (ENSA Khouribga / ENIM Rabat).",
        "3e Prix Compétition Nationale (EMI Rabat / ENSA El Jadida)."
    ]

class SMTPSettings(BaseModel):
    provider: str = "gmail"  # gmail, outlook, custom
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = Field(default_factory=lambda: os.getenv("GMAIL_SENDER_EMAIL", "mohammedhsiny2@gmail.com"))
    sender_name: str = "Mohammed HSINY"
    app_password: str = Field(default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD", "qawi kviz qjqu hwgb"))
    min_delay_seconds: int = 4
    max_delay_seconds: int = 8
    daily_limit: int = 500

class LLMSettings(BaseModel):
    provider: str = "gemini"  # gemini, openai, groq, deepseek, ollama, openrouter
    api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = "gemini-2.0-flash"
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
