@echo off
chcp>nul 2>nul 65001
:path
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat
rem pyinstaller --noconfirm --onefile --windowed --icon "./web/favicon.ico" --add-data "./module/*.exe;./module/" --add-data "./web;web/"  "./main.py" --name "NsEmuTools"
rem pyinstaller --noconfirm --onefile --console --icon "./web/favicon.ico" --add-data "./module/*.exe;./module/" --add-data "./web;web/"  "./main.py" --name "NsEmuTools"
pyinstaller --noconfirm --onefile --console --icon "./web/favicon.ico" --add-data "./module/*.exe;./module/" --add-data "./web;web/"  "./ui_webview.py" --additional-hooks-dir=".\\hooks" --name "NsEmuTools-webview"
pause
