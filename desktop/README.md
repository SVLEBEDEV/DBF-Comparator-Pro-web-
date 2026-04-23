# Desktop Runtime

Этот каталог содержит оболочку `Electron` для полностью оффлайн Windows-версии.

## Что уже заложено

- приложение поднимает локальный backend на `127.0.0.1:18400`
- фронтенд читает runtime API URL из `preload`
- desktop backend рассчитан на `sqlite` и локальный потоковый runner без `Redis`
- веб-версия остаётся отдельной и не меняет свой production flow

## Dev-режим

1. Скопируйте `backend/.env.desktop.example` в `backend/.env.desktop`
2. Соберите фронтенд для веба или поднимите dev-сервер на `127.0.0.1:18401`
3. Запустите backend:
   `cd /Users/thelebedevs/DBF Comparator PRO v2/backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 18400`
4. Запустите desktop shell:
   `cd /Users/thelebedevs/DBF Comparator PRO v2/desktop && npm install && npm run dev`

## Packaging

Для production-сборки нужен отдельно упакованный Windows backend executable. В качестве entrypoint используется [backend/run_desktop.py](/Users/thelebedevs/DBF Comparator PRO v2/backend/run_desktop.py), а готовый файл должен лежать в `backend/dist/dbf-comparator-backend.exe`. После этого можно собрать desktop shell командой:

`cd /Users/thelebedevs/DBF Comparator PRO v2/desktop && npm install && npm run dist:win`

На macOS можно подготовить проект и прогнать часть пайплайна, но полноценный Windows `.exe` backend корректно собирается в Windows-окружении. Для этого в репозиторий добавлен GitHub Actions workflow сборки desktop-версии.
