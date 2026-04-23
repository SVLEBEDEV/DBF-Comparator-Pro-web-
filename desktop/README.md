# Desktop Runtime

Этот каталог содержит оболочку `Electron` для полностью оффлайн desktop-версии под Windows и macOS.

## Что уже заложено

- приложение поднимает локальный backend на `127.0.0.1:18400`
- фронтенд читает runtime API URL из `preload`
- desktop backend рассчитан на `sqlite` и локальный потоковый runner без `Redis`
- runtime данные desktop backend сохраняются в пользовательскую директорию приложения, а не в app bundle
- веб-версия остаётся отдельной и не меняет свой production flow

## Dev-режим

1. Скопируйте `backend/.env.desktop.example` в `backend/.env.desktop`
2. Соберите фронтенд для веба или поднимите dev-сервер на `127.0.0.1:18401`
3. Запустите backend:
   `cd /Users/thelebedevs/DBF Comparator PRO v2/backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 18400`
4. Запустите desktop shell:
   `cd /Users/thelebedevs/DBF Comparator PRO v2/desktop && npm install && npm run dev`

## Packaging

Для production-сборки нужен отдельно упакованный backend executable. В качестве entrypoint используется [backend/run_desktop.py](/Users/thelebedevs/DBF Comparator PRO v2/backend/run_desktop.py).

`cd /Users/thelebedevs/DBF Comparator PRO v2/desktop && npm install && npm run dist:win`

Команды для локальной сборки:

- Windows: `npm run dist:win`
- macOS Intel: `npm run dist:mac:x64`
- macOS Apple Silicon: `npm run dist:mac:arm64`

Ожидаемые backend binaries:

- Windows: `backend/dist/dbf-comparator-backend.exe`
- macOS: `backend/dist/dbf-comparator-backend`

Для CI в репозиторий добавлены отдельные workflow для Windows и macOS desktop-сборок.

Если локальный backend не стартует, desktop shell показывает путь к лог-файлу backend. На macOS он будет лежать внутри `~/Library/Application Support/<app name>/runtime/logs/backend.log`.
