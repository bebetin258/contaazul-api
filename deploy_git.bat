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
git commit -m "update automatico %date% %time%" || echo ⚠️ Nada para commit

echo.
echo ⬆️ Enviando para GitHub...
git push origin main || echo ❌ ERRO NO PUSH

echo.
echo =============================
echo ✅ PROCESSO FINALIZADO
echo =============================

pause