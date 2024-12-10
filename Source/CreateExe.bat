@echo off
REM Obtenir le chemin du répertoire contenant ce script
set SCRIPT_DIR=%~dp0

REM Changer le répertoire de travail pour celui du script
cd /d "%SCRIPT_DIR%"

REM Lancer PyInstaller avec les chemins relatifs
pyinstaller --onefile --noconsole --icon=images.ico ^
--add-data "Python/config.json;Python" ^
--add-data "Python/style.css;Python" ^
--add-data "Python/sidebar.js;Python" ^
--add-data "Python/Template_CRF.html;Python" ^
--add-data "images.ico;Python" ^
"%SCRIPT_DIR%/Python/interface.py"

REM Attendre avant de fermer la fenêtre (facultatif)
pause