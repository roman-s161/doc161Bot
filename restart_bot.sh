#!/bin/bash

echo "Перезапуск бота..."
cd /var/www/u3185898/data/doc161Bot

# Останавливаем бота
./stop_bot.sh

# Ждем немного
sleep 2

# Запускаем бота
./start_bot.sh

