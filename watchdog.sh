#!/bin/bash

cd /var/www/u3185898/data/doc161Bot

# Проверяем, запущен ли бот
if ! pgrep -f "exampleBot.py" > /dev/null; then
    echo "$(date): Бот не запущен, запускаем..." >> watchdog.log
    ./start_bot.sh
else
    echo "$(date): Бот работает нормально" >> watchdog.log
fi

