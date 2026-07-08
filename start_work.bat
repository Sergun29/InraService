@echo off
chcp 65001 >nul
REM Синхронизация перед началом работы
cd /d "%~dp0"

echo Получаем последние изменения с GitHub...
git pull origin main

echo.
echo Активируем виртуальное окружение...
call venv\Scripts\activate.bat

echo.
echo Готово. Можно приступать к работе.
cmd /k