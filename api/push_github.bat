@echo off

echo Limpando locks antigos...
del /f /q .git\*.lock 2>nul

echo Commitando...
git add .
git commit -m "update automatico %date% %time%"

git branch -M main

git remote remove origin 2>nul
git remote add origin https://github.com/bebetin258/contaazul-api.git

echo Enviando...
git push -u origin main --force

echo FINALIZADO 🚀
pause