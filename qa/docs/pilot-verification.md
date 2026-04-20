# Pilot Verification

## Smoke Checklist

- `docker compose up --build` поднимает `proxy`, `frontend`, `api`, `worker`, `postgres`, `redis`.
- `GET /api/v1/health` возвращает `200`.
- `GET /api/v1/ready` возвращает `200`.
- Загрузка двух валидных DBF завершается успешно.
- Пользователь может выбрать `Ключ 1`, `Ключ 2` и флаги сравнения.
- Статус задачи доходит до `completed`.
- Preview доступен минимум для `STRUCTURE`, `RECONCILIATION`, `DETAILS`.
- Excel-отчёт скачивается.
- `DELETE /api/v1/comparisons/{jobId}` очищает артефакты.

## Regression Focus

- `cp866` и `cp1251` по-прежнему читаются без искажений.
- Пробел, таб, CRLF и пустое значение различаются как отдельные кейсы.
- `Только структура` не создаёт data-level preview.
- Preview-пагинация не ломает UI на пустой и непустой секции.
