@echo off
cd /d C:\Users\Gilberto\Desktop\Projetos\Zenitus\contaazul_api

echo =============================
echo 🚀 INICIANDO DEPLOY GIT
echo =============================

git status

echo.
echo 📦 Adicionando arquivos...
git add .

echo.
echo 💾 Criando commit...
git commit -m "update automatico %date% %time%"

echo.
echo ⬆️ Enviando para GitHub...
git push origin main

echo.
echo =============================
echo ✅ DEPLOY FINALIZADO
echo =============================
pause