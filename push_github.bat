@echo off

echo ================================
echo Sincronizando repositorio...
echo ================================

git init

git add .
git commit -m "update automatico %date% %time%"

echo ================================
echo Ajustando branch...
echo ================================

git branch -M main

echo ================================
echo Configurando remoto...
echo ================================

git remote remove origin 2>nul
git remote add origin https://github.com/bebetin258/contaazul-api.git

echo ================================
echo Tentando push normal...
echo ================================

git pull origin main --allow-unrelated-histories

git push -u origin main

IF %ERRORLEVEL% NEQ 0 (
    echo ================================
    echo ERRO detectado, forçando envio...
    echo ================================
    git push -u origin main --force
)

echo ================================
echo FINALIZADO 🚀
echo ================================

pause