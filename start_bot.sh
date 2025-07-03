#!/bin/bash

# Переходим в директорию с ботом
cd /var/www/u3185898/data/doc161Bot

# Проверяем, не запущен ли уже бот
if pgrep -f "exampleBot.py" > /dev/null; then
    echo "Бот уже запущен!"
    echo "Текущие процессы:"
    ps aux | grep exampleBot.py | grep -v grep
    exit 1
fi

# Очищаем старый PID файл
rm -f bot.pid

# Запускаем бота в фоновом режиме
nohup /opt/python/python-3.9.0/bin/python exampleBot.py > bot.log 2>&1 &

# Получаем PID процесса
BOT_PID=$!
echo $BOT_PID > bot.pid

echo "Бот запущен с PID: $BOT_PID"
echo "Логи: tail -f /var/www/u3185898/data/doc161Bot/bot.log"

