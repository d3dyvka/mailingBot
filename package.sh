#!/bin/bash
# Package script for distributing Telegram Mailer
# Creates a ready-to-distribute ZIP archive

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_NAME="TelegramMailer"
APP_BUNDLE="dist/${APP_NAME}.app"
OUTPUT_ZIP="dist/${APP_NAME}.zip"
README_FILE="dist/README_RU.txt"

echo -e "${GREEN}Упаковка приложения для распространения...${NC}"
echo ""

# Check if app exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Ошибка: Приложение не найдено. Сначала запустите ./build.sh"
    exit 1
fi

# Remove quarantine attributes
echo -e "${YELLOW}Шаг 1: Удаление атрибутов карантина...${NC}"
xattr -cr "$APP_BUNDLE"
echo -e "${GREEN}✓ Готово${NC}"
echo ""

# Ad-hoc signing
echo -e "${YELLOW}Шаг 2: Подпись приложения...${NC}"
codesign --force --deep --sign - "$APP_BUNDLE" 2>/dev/null || true
echo -e "${GREEN}✓ Готово${NC}"
echo ""

# Create README for user
echo -e "${YELLOW}Шаг 3: Создание инструкции...${NC}"
cat > "$README_FILE" << 'EOF'
TELEGRAM MAILER - ИНСТРУКЦИЯ ПО УСТАНОВКЕ
==========================================

1. Распакуйте архив (двойной клик по ZIP файлу)

2. Перетащите TelegramMailer.app в папку "Программы" (Applications)

3. ПЕРВЫЙ ЗАПУСК:
   
   Если при запуске появляется ошибка "Невозможно открыть программу":
   
   СПОСОБ 1 (Рекомендуется):
   - Нажмите правой кнопкой мыши на TelegramMailer.app
   - Выберите "Открыть"
   - В диалоге нажмите "Открыть" еще раз
   
   СПОСОБ 2 (Через терминал):
   - Откройте Терминал
   - Выполните: xattr -cr /Applications/TelegramMailer.app
   - Запустите приложение обычным способом
   
   СПОСОБ 3 (Через настройки):
   - Попробуйте открыть приложение (получите ошибку)
   - Откройте: Системные настройки → Конфиденциальность и безопасность
   - Внизу нажмите "Открыть в любом случае"

4. После первого успешного запуска приложение будет открываться обычным двойным кликом

ВАЖНО: Это безопасное приложение. Предупреждение появляется потому что оно не подписано 
сертификатом Apple Developer (стоимость $99/год).

Приятного использования!
EOF
echo -e "${GREEN}✓ Инструкция создана${NC}"
echo ""

# Remove old ZIP if exists
if [ -f "$OUTPUT_ZIP" ]; then
    rm "$OUTPUT_ZIP"
fi

# Create ZIP archive
echo -e "${YELLOW}Шаг 4: Создание ZIP архива...${NC}"
cd dist
zip -r -q "${APP_NAME}.zip" "${APP_NAME}.app" "README_RU.txt"
cd ..

if [ -f "$OUTPUT_ZIP" ]; then
    ZIP_SIZE=$(du -sh "$OUTPUT_ZIP" | cut -f1)
    echo -e "${GREEN}✓ Архив создан: ${OUTPUT_ZIP}${NC}"
    echo -e "${GREEN}  Размер: ${ZIP_SIZE}${NC}"
else
    echo "Ошибка при создании архива"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Готово к распространению!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Отправьте файл: ${GREEN}${OUTPUT_ZIP}${NC}"
echo ""
echo -e "${YELLOW}Пользователь должен:${NC}"
echo "1. Распаковать ZIP"
echo "2. При первом запуске: ПКМ → Открыть → Открыть"
echo "3. Дальше приложение будет работать обычным двойным кликом"
echo ""
