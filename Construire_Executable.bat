@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Construit l'exécutable Windows autonome (--onefile) de SARA Route
rem Manager avec PyInstaller, dans l'environnement virtuel partagé (voir
rem Installer.bat). Nécessite un poste Windows : ce script ne peut pas
rem être exécuté ni testé depuis l'environnement de préparation Linux.

call Installer.bat
if errorlevel 1 goto :error

echo Installation de PyInstaller (environnement de construction)...
"%SARA_VENV_PYTHON%" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :error

echo Construction de l'executable...
"%SARA_VENV_PYTHON%" -m PyInstaller sara_route_manager.spec
if errorlevel 1 goto :error

echo.
echo Construction terminee. Executable : dist\SARA_Route_Manager.exe
exit /b 0

:error
echo.
echo La construction a echoue. Consultez les messages ci-dessus.
pause
exit /b 1
