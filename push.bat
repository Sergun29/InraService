@echo off
chcp 65001 >nul
setlocal

REM Автоматическая выгрузка изменений в GitHub (Windows)
cd /d "%~dp0"

echo Проверяем актуальность перед пушем...
git pull origin main

echo.
set /p msg=Введите сообщение коммита: 

git add .
git commit -m "%msg%"
git push origin main

echo.
echo Готово. Изменения отправлены в репозиторий.
pause