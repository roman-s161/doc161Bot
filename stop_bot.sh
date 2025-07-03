#!/bin/bash

cd /var/www/u3185898/data/doc161Bot

# Проверяем файл с PID
if [ -f bot.pid ]; then
    BOT_PID=$(cat bot.pid)
    if kill -0 $BOT_PID 2>/dev/null; then
        echo "Останавливаем бота с PID: $BOT_PID"
        kill $BOT_PID
        rm bot.pid
        echo "Бот остановлен"
    else
        echo "Процесс с PID $BOT_PID не найден"
        rm bot.pid
    fi
else
    # Пытаемся найти процесс по имени
    BOT_PID=$(pgrep -f "exampleBot.py")
    if [ ! -z "$BOT_PID" ]; then
        echo "Найден процесс бота с PID: $BOT_PID"
        kill $BOT_PID
        echo "Бот остановлен"
    else
        echo "Бот не запущен"
    fi
fi

