# DBF Comparator Pro v2

В этом репозитории находится web-версия внутреннего инструмента для строгого сравнения двух DBF-файлов.

## Current Status

- `backend/`: upload, compare, preview, Excel report, cleanup, readiness, request-id logging и hourly cleanup scheduler.
- `frontend/`: одноэкранный workflow с upload, polling, preview, report download и improved error states.
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
2. Заполните пароль БД и IP/домен
3. Выполните `docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build`
4. Откройте `http://<server-ip>`

## Local Checks

- Backend tests: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q`
- Frontend tests: `cd frontend && npm test`
- Frontend build: `cd frontend && npm run build`
