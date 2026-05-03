@echo off

git init
git add .
git commit -m "Primeiro commit - Conta Azul API"

git branch -M main

git remote remove origin 2>nul
git remote add origin https://github.com/bebetin258/contaazul-api.git

git push -u origin main

pause