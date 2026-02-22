#!/bin/bash
# Debug script to see why app crashes

echo "Запуск приложения с выводом ошибок..."
echo "========================================"
echo ""

# Run the app executable directly to see errors
./dist/TelegramMailer.app/Contents/MacOS/TelegramMailer

echo ""
echo "========================================"
echo "Приложение завершилось"
