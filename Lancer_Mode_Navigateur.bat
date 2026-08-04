@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call Installer.bat
if errorlevel 1 goto :error

rem Mode de diagnostic uniquement : ouverture dans le navigateur par défaut.
"%SARA_VENV_PYTHON%" -m sara_route_manager --browser
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Une erreur est survenue. Consultez les messages ci-dessus et le journal.
pause
exit /b 1
