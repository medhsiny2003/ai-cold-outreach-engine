# ⚡ AI Cold Outreach Engine & Email Automation
### Plateforme Intelligente de Candidature Spécialisée Ingénieur (Embedded / Robotics / Automation / R&D)

Développé pour **Mohammed HSINY** — Élève-Ingénieur en Génie Électrique & Contrôle Industriel (FST Mohammedia).

---

## 🌟 Fonctionnalités Principales

1. **Génération IA de Haut Niveau (Gemini, OpenAI, Groq, DeepSeek, Ollama)** :
   - Techniques de communication et de copywriting persuasif (AIDA, Hook technique, valorisation concrète des réalisations).
   - Adaptation du message selon le poste du destinataire (CTO / Lead Dev vs RH / Recruteur vs Fondateur / CEO).
   - Intégration dynamique de vos projets clés (*Drone d'inspection HT par IA*, *Robots ADAS ESP-NOW*, *Supervision SCADA OCP*, *Bras 6 axes*, etc.) et lien vers votre **[Portfolio en ligne](https://portfolio-mohammed-hsiny-ux7z.vercel.app)**.
2. **Détection & Adaptation Linguistique Automatique** :
   - **Français** : pour les destinataires en France, Belgique francophone, Suisse, Canada (Québec), Maroc, etc.
   - **Anglais** : pour les entreprises aux USA, Royaume-Uni, Allemagne, Pays-Bas, et hubs internationaux.
   - Possibilité de forcer la langue globalement ou par contact.
3. **Contrôle Total (Human-in-the-Loop)** :
   - Génération en masse en 1 clic.
   - Interface de prévisualisation et éditeur en direct pour chaque email (Objet + Corps).
   - Validation / Approbation individuelle ou groupée avant tout envoi.
4. **Moteur d'Envoi Gmail SMTP Sécurisé & Anti-Spam** :
   - Envoi direct via votre compte Gmail (`mohammedhsiny2@gmail.com`) avec **Mot de Passe d'Application Google**.
   - Pièce jointe automatique (CV PDF).
   - Temporisation aléatoire anti-spam (ex: 25s à 50s entre chaque email) pour préserver la réputation de votre adresse.
   - **Mode Test** pour vous envoyer un email de vérification avant le lancement de campagne.
   - Historique complet des envois avec statut et export CSV/Excel.

---

## 🚀 Démarrage Rapide

### 1. Lancement de l'Application
Double-cliquez sur `run_app.bat` ou exécutez dans votre terminal :
```bash
streamlit run app.py
```
L'interface web s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`.

---

## 📧 Configuration de Gmail (Étape Obligatoire)

Pour permettre à l'application d'envoyer des emails via votre compte Gmail sans bloquer la sécurité Google :

1. Activez la **Validation en 2 étapes** sur votre compte Google : [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Rendez-vous sur la page des **Mots de passe des applications** : [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Saisissez un nom (ex: `Outreach-App`) et cliquez sur **Créer**.
4. Google affiche un code de 16 caractères (ex: `abcd efgh ijkl mnop`).
5. Ouvrez l'onglet **"Paramètres & Gmail"** dans l'application, collez ce mot de passe de 16 caractères et cliquez sur **"Tester la connexion SMTP"**.

---

## 🤖 Configuration de la Clé IA (Google Gemini)

1. Obtenez votre clé API gratuite en 30 secondes sur [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Dans l'onglet **"Paramètres & Gmail"**, collez votre clé API Gemini.
3. Vous pouvez choisir entre `gemini-2.0-flash`, `gemini-2.5-flash` ou `gemini-1.5-pro`.

---

## 📁 Structure du Projet

```
automation -sensidng-email/
│
├── app.py                      # Interface principale Streamlit
├── config.py                   # Paramètres, profil candidat & constantes
├── requirements.txt            # Dépendances Python
├── run_app.bat                 # Lanceur Windows en 1 clic
├── README.md                   # Guide complet d'utilisation
│
├── services/
│   ├── prompt_builder.py       # Moteur de prompt engineering et copywriting
│   ├── llm_service.py          # Connecteur multi-fournisseurs IA (Gemini/OpenAI)
│   ├── email_sender.py         # Envoi SMTP sécurisé & gestion CV PDF
│   ├── contact_manager.py      # Import / export CSV/Excel & détection de langue
│   └── storage_service.py      # Base de données SQLite & suivi des statuts
│
├── data/
│   ├── sample_contacts.csv     # Modèle de contacts pré-rempli
│   ├── outreach.db             # Base SQLite (profil, contacts, historique)
│   └── uploads/                # Répertoire de votre CV PDF
│
└── scripts/
    └── test_system.py          # Suite de tests d'intégration automatisés
```

---

## 📋 Format du Fichier Contacts (CSV / Excel)

Le système détecte automatiquement les colonnes quel que soit leur nom (`Nom`, `Email`, `Entreprise`, `Poste`, `Pays`...). Exemple de structure recommandée :

| name | email | company | role | location | industry | notes |
|---|---|---|---|---|---|---|
| Julien Moreau | julien.moreau@parrot.com | Parrot | CTO / Head of Embedded | Paris, France | Drones & IA | Équipe R&D micro-drones |
| Sarah Jenkins | s.jenkins@skydio.com | Skydio | Technical Recruiter | San Mateo, CA, USA | Autonomous Drones | Looking for Embedded interns |
