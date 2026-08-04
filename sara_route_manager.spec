# -*- mode: python ; coding: utf-8 -*-
"""
Fichier : sara_route_manager.spec
Description : Configuration PyInstaller pour construire l'exécutable
Windows autonome (--onefile) de SARA Route Manager.

Utilisation (depuis l'environnement virtuel partage, sur un poste
Windows -- ce fichier ne peut pas etre construit ni teste depuis
l'environnement de developpement Linux) :

    "%LOCALAPPDATA%\\SARA Route Manager\\venv\\Scripts\\python.exe" -m pip install pyinstaller
    "%LOCALAPPDATA%\\SARA Route Manager\\venv\\Scripts\\pyinstaller.exe" sara_route_manager.spec

Le resultat est ecrit dans dist\\SARA_Route_Manager.exe (dossier deja
exclu du depot par .gitignore, comme build\\ et *.spec -- ce fichier-ci
est une exception explicite, necessaire au depot pour que la construction
soit reproductible).

Construction et test confirmes en conditions reelles sur Windows (4 aout
2026) : les imports caches ci-dessous (backends pywebview et keyring) se
sont averes corrects -- connexion au compte SARA, recherche/ajout de
marques SHOM et fenetre de visualisation cartographique tous verifies
fonctionnels dans l'executable construit.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("sara_route_manager/templates", "sara_route_manager/templates"),
    ("sara_route_manager/static", "sara_route_manager/static"),
]

# Modules charges dynamiquement par leurs bibliotheques respectives,
# qu'une analyse statique de PyInstaller peut manquer.
hidden_imports = [
    # Backends pywebview pertinents sous Windows (Edge WebView2 et,
    # a defaut, WinForms) -- pywebview les selectionne dynamiquement
    # selon l'environnement, PyInstaller ne peut pas le deduire seul.
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    # Backend keyring pour le Gestionnaire d'identifiants Windows,
    # decouvert par points d'entree (mecanisme que PyInstaller ne
    # suit pas automatiquement).
    "keyring.backends.Windows",
]

a = Analysis(
    ["run_sara_route_manager.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SARA_Route_Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Application graphique : pas de console visible. Repasser
    # temporairement a True en cas d'echec au demarrage, pour voir les
    # messages d'erreur habituellement invisibles sans console.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icone de l'executable : aucune fournie a ce jour. Ajouter
    # icon="chemin/vers/icone.ico" ici le cas echeant.
)
