@echo off
cd /d "%~dp0"
call opencode run "Lade Skill graphify. Führe graphify, wenn graphify-out besteht, update ausführen, ansonsten graphify komplett ausführen. Gebe nach der Verarbeitung eine meldung aus 'ALLES ERLEDIGT!'. opencode nicht schließen das macht der Anwender" --model opencode/big-pickle
pause

