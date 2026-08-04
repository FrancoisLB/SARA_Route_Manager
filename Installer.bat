@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Emplacement partage et stable de l'environnement virtuel Python, en
rem dehors du dossier versionne du projet : chaque nouvelle version livree
rem reutilise ainsi le meme environnement sans avoir besoin de le recreer
rem ni de le recopier manuellement d'un dossier a l'autre (friction de
rem distribution signalee et corrigee).
set "VENV_DIR=%LOCALAPPDATA%\SARA Route Manager\venv"

rem Ce script recherche automatiquement une version de Python compatible.
rem Il accepte Python 3.10, 3.11, 3.12, 3.13 ou une version plus recente.

if exist "%VENV_DIR%\Scripts\python.exe" goto :install_dependencies

echo Recherche d'une installation Python compatible...

rem Le lanceur Python pour Windows peut gerer plusieurs versions.
where py >nul 2>&1
if not errorlevel 1 (
    py -3.13 -m venv "%VENV_DIR%" >nul 2>&1
    if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created

    py -3.12 -m venv "%VENV_DIR%" >nul 2>&1
    if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created

    py -3.11 -m venv "%VENV_DIR%" >nul 2>&1
    if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created

    py -3.10 -m venv "%VENV_DIR%" >nul 2>&1
    if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created

    rem Sans numero de version, le lanceur choisit son Python par defaut.
    py -3 -m venv "%VENV_DIR%" >nul 2>&1
    if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created
)

rem Recherche ensuite la commande python disponible dans le PATH.
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        python -m venv "%VENV_DIR%"
        if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created
    )
)

rem Certains environnements utilisent la commande python3.
where python3 >nul 2>&1
if not errorlevel 1 (
    python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 (
        python3 -m venv "%VENV_DIR%"
        if exist "%VENV_DIR%\Scripts\python.exe" goto :venv_created
    )
)

echo.
echo ERREUR : aucune installation Python compatible n'a ete trouvee.
echo.
echo Cette application accepte Python 3.10 ou une version plus recente.
echo Pour afficher les versions detectees par le lanceur Windows, tapez :
echo     py -0p
echo.
echo Vous pouvez aussi verifier ces commandes :
echo     python --version
echo     py --version
echo.
echo Installez Python depuis python.org en cochant l'option
 echo "Add python.exe to PATH", puis relancez ce fichier.
exit /b 1

:venv_created
echo Environnement Python cree avec succes.

:install_dependencies
echo Verification des dependances Python...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

rem Rendre le chemin du Python de l'environnement partage disponible au
rem script appelant (Lancer_*.bat), au-dela de la portee locale de ce
rem script (endlocal termine la portee, mais le "set" qui suit sur la
rem meme ligne s'execute deja dans la portee du script appelant).
endlocal & set "SARA_VENV_PYTHON=%LOCALAPPDATA%\SARA Route Manager\venv\Scripts\python.exe"
exit /b 0
