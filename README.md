# DBF Comparator Pro v2

В этом репозитории находится web-версия внутреннего инструмента для строгого сравнения двух DBF-файлов.

## Current Status

- `backend/`: upload, compare, preview, Excel report, cleanup, readiness, request-id logging и hourly cleanup scheduler.
- `frontend/`: одноэкранный workflow с upload, polling, preview, report download и improved error states.
- `docker-compose.yml`: pilot-окружение с `frontend`, `api`, `worker`, `postgres`, `redis`, `nginx`.
- `.github/workflows/ci.yml`: CI на backend и frontend.
- `qa/`: test strategy и pilot smoke checklist.

## Local pilot run

1. Скопируйте `backend/.env.example` в `backend/.env`, если нужны локальные изменения.
2. Скопируйте `frontend/.env.example` в `frontend/.env`, если нужен другой API URL.
3. Запустите `docker compose up --build`.
4. Откройте `http://localhost:8080`.

## Local Checks

- Backend tests: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -q`
- Frontend tests: `cd frontend && npm test`
- Frontend build: `cd frontend && npm run build`
