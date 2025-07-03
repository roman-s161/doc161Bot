#!/bin/bash

cd /var/www/u3185898/data/doc161Bot

BOT_PID=$(pgrep -f "exampleBot.py")

if [ ! -z "$BOT_PID" ]; then
    echo "Бот запущен с PID: $BOT_PID"
    echo "Время работы:"
    ps -o pid,etime,cmd -p $BOT_PID
    echo ""
    echo "Последние 10 строк лога:"
    tail -n 10 bot.log
else
    echo "Бот не запущен"
fi

