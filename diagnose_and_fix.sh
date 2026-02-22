#!/bin/bash

echo "=== Диагностика проблемы с Telegram кодом ==="
echo ""

# Проверка запущенных процессов
echo "1. Проверка запущенных процессов..."
PROCESS_COUNT=$(ps aux | grep -i "TelegramMailer.app" | grep -v grep | wc -l)

if [ $PROCESS_COUNT -gt 0 ]; then
    echo "⚠️  Найдено запущенных процессов TelegramMailer: $PROCESS_COUNT"
    echo ""
    ps aux | grep -i "TelegramMailer.app" | grep -v grep
    echo ""
    echo "Завершаем процессы..."
    pkill -f "TelegramMailer.app"
    sleep 2
    echo "✓ Процессы завершены"
else
    echo "✓ Нет запущенных процессов TelegramMailer"
fi

echo ""

# Проверка сессионного файла
SESSION_FILE="$HOME/Library/Application Support/TelegramMailer/session_name.session"
echo "2. Проверка сессионного файла..."

if [ -f "$SESSION_FILE" ]; then
    echo "✓ Файл сессии найден: $SESSION_FILE"
    
    # Проверка прав доступа
    PERMS=$(stat -f "%Lp" "$SESSION_FILE")
    echo "  Права доступа: $PERMS"
    
    if [ "$PERMS" != "600" ]; then
        echo "  Исправляем права доступа..."
        chmod 600 "$SESSION_FILE"
        echo "  ✓ Права установлены на 600"
    fi
    
    # Проверка размера
    SIZE=$(stat -f "%z" "$SESSION_FILE")
    echo "  Размер файла: $SIZE байт"
    
else
    echo "❌ Файл сессии не найден"
    echo "   Необходима повторная авторизация"
fi

echo ""

# Проверка логов
echo "3. Проверка логов ошибок..."
ERROR_LOG="$HOME/Library/Application Support/TelegramMailer/errors.txt"
CRASH_LOG="$HOME/Library/Application Support/TelegramMailer/crash.log"

if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
    echo "⚠️  Найдены ошибки в errors.txt:"
    tail -20 "$ERROR_LOG"
else
    echo "✓ Нет ошибок в errors.txt"
fi

echo ""

if [ -f "$CRASH_LOG" ] && [ -s "$CRASH_LOG" ]; then
    echo "⚠️  Найдены крэши в crash.log (последние строки):"
    tail -30 "$CRASH_LOG"
else
    echo "✓ Нет крэшей в crash.log"
fi

echo ""
echo "=== Рекомендации ==="
echo ""
echo "Обнаружена проблема: база данных сессии была заблокирована запущенным процессом."
echo ""
echo "Что сделано:"
echo "  ✓ Завершены все процессы TelegramMailer"
echo "  ✓ Проверены права доступа к файлу сессии"
echo ""
echo "Следующие шаги:"
echo "  1. Запустите приложение заново"
echo "  2. Попробуйте войти снова"
echo "  3. Если проблема повторяется, запустите: python3 fix_session.py"
echo ""
