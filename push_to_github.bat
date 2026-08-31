@echo off
chcp 65001 > nul
echo ======================================================================
echo    🚀 PUSH DU PROJET SUR GITHUB (POUR DÉPLOIEMENT RENDER)
echo ======================================================================
echo.

git branch -M main

set /p REPO_URL="Entrez l'URL de votre dépôt GitHub (ex: https://github.com/username/outreach-engine.git) : "

if "%REPO_URL%"=="" (
    echo [ERREUR] Aucune URL fournie. Veuillez relancer et coller l'URL de votre dépôt.
    pause
    exit /b
)

echo.
echo [*] Configuration de la branche distante origin...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo [*] Envoi du code sur GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo  🎉 SUCCÈS : Projet synchronisé sur GitHub !
    echo  👉 Rendez-vous maintenant sur https://dashboard.render.com/
    echo     et sélectionnez ce dépôt pour le déployer en 1 clic !
    echo ======================================================================
) else (
    echo.
    echo [!] Une erreur est survenue lors du push. Vérifiez vos identifiants GitHub.
)

pause
