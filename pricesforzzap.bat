@echo off
title Запуск проекта PricesForZZap (WSL)
echo Запуск main.py в WSL...

:: Переходим в папку проекта внутри WSL, активируем окружение и запускаем скрипт
wsl -d Ubuntu -e bash -c "cd ~/PricesForZZap && source .venv/bin/activate && python main.py"

echo Готово.
pause