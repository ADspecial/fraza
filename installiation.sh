#!/bin/bash

REPO_URL="https://github.com/ADspecial/fraza.git"
APP_NAME="fraza"

# Проверяем наличие git
if ! command -v git &>/dev/null; then
  echo "Git не установлен. Установите git и повторите."
  exit 1
fi

# Проверяем наличие python3
if ! command -v python3 &>/dev/null; then
  echo "Python3 не установлен. Установите python3 и повторите."
  exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &>/dev/null; then
  echo "pip3 не установлен. Установите pip3 и повторите."
  exit 1
fi

# Проверяем наличие pyinstaller, если нет — ставим
if ! command -v pyinstaller &>/dev/null; then
  echo "PyInstaller не найден. Устанавливаю..."
  pip3 install --user pyinstaller || { echo "Ошибка установки PyInstaller"; exit 1; }
fi

# Клонируем репозиторий
if [ -d "$APP_NAME" ]; then
  echo "Папка $APP_NAME уже существует, обновляю..."
  cd "$APP_NAME" && git pull || exit 1
else
  git clone "$REPO_URL" || { echo "Ошибка клонирования репозитория"; exit 1; }
  cd "$APP_NAME" || exit 1
fi

# Устанавливаем зависимости, если есть requirements.txt
if [ -f "requirements.txt" ]; then
  pip3 install --user -r requirements.txt || { echo "Ошибка установки зависимостей"; exit 1; }
fi

# Собираем исполняемый файл
pyinstaller --onefile --name fraza --add-data "data/tagged_words_full.json;data" fraza/cli.py || { echo "Ошибка сборки PyInstaller"; exit 1; }

# Копируем в /usr/local/bin с правами
sudo cp ./dist/fraza /usr/local/bin/ || { echo "Ошибка копирования файла"; exit 1; }

echo "Установка завершена. Используйте команду 'fraza' для запуска."
