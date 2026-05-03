@echo off

echo ================================
echo Inicializando repositório...
echo ================================

git init

echo ================================
echo Adicionando arquivos...
echo ================================

git add .

echo ================================
echo Commitando...
echo ================================

git commit -m "Primeiro commit - Conta Azul API"

echo ================================
echo Conectando ao GitHub...
echo ================================

git branch -M main

git remote add origin https://github.com/bebetin258/contaazul-api.git

echo ================================
echo Enviando para o GitHub...
echo ================================

git push -u origin main

echo ================================
echo FINALIZADO 🚀
echo ================================

pause