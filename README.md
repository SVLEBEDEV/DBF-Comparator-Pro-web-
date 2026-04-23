# DBF Comparator Pro v2

В этом репозитории находится web-версия внутреннего инструмента для строгого сравнения двух DBF-файлов.

## Current Status

- `backend/`: upload, compare, preview, Excel report, cleanup, readiness, request-id logging и hourly cleanup scheduler.
- `frontend/`: одноэкранный workflow с upload, polling, preview, report download и improved error states.
- `desktop/`: Windows desktop shell для оффлайн-режима поверх существующих frontend/backend.
- `docker-compose.yml`: pilot-окружение с `frontend`, `api`, `worker`, `postgres`, `redis`, `nginx`.
- `docker-compose.prod.yml`: production-окружение для VPS с раздачей frontend через `nginx`.
- `.github/workflows/ci.yml`: CI на backend и frontend.
- `qa/`: test strategy и pilot smoke checklist.

## Local pilot run

1. Скопируйте `backend/.env.example` в `backend/.env`, если нужны локальные изменения.
2. Скопируйте `frontend/.env.example` в `frontend/.env`, если нужен другой API URL.
3. Запустите `docker compose up --build`.
4. Откройте `http://localhost:8080`.

## Production deploy on Beget VPS

Для первого серверного развёртывания используйте:

1. [`.env.production.example`](/Users/thelebedevs/DBF Comparator PRO v2/.env.production.example)
2. [`docker-compose.prod.yml`](/Users/thelebedevs/DBF Comparator PRO v2/docker-compose.prod.yml)
3. [`project/beget-deploy.md`](/Users/thelebedevs/DBF Comparator PRO v2/project/beget-deploy.md)

Коротко:

1. Скопируйте `.env.production.example` в `.env.production`
2. Заполните пароль БД, домен и параметры `https`
3. Выполните `docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build`
4. Для production с доменом и сертификатом откройте `https://<your-domain>`

## Local Checks

- Backend tests: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q`
- Frontend tests: `cd frontend && npm test`
- Frontend build: `cd frontend && npm run build`

## Desktop Offline

Desktop-версия идёт как дополнение к web-версии и использует тот же UI, но локальный backend:

- web production остаётся на `PostgreSQL + Redis + Celery`
- desktop использует `sqlite` и `JOB_RUNNER=thread`
- runtime-конфиг frontend получает из `Electron preload`, поэтому web и desktop могут жить параллельно
- поддерживаются сборки под `Windows` и `macOS`

Файлы для desktop-режима:

- [backend/.env.desktop.example](/Users/thelebedevs/DBF Comparator PRO v2/backend/.env.desktop.example)
- [desktop/main.cjs](/Users/thelebedevs/DBF Comparator PRO v2/desktop/main.cjs)
- [desktop/preload.cjs](/Users/thelebedevs/DBF Comparator PRO v2/desktop/preload.cjs)
- [desktop/README.md](/Users/thelebedevs/DBF Comparator PRO v2/desktop/README.md)
- [windows-desktop.yml](/Users/thelebedevs/DBF Comparator PRO v2/.github/workflows/windows-desktop.yml)
- [macos-desktop.yml](/Users/thelebedevs/DBF Comparator PRO v2/.github/workflows/macos-desktop.yml)
