# Runbook

## Назначение

Этот runbook описывает пилотное on-premise развёртывание `DBF Comparator Pro v2`, базовую диагностику и сценарий rollback.

## Подготовка

1. Установить Docker и Docker Compose plugin на сервере.
2. Подготовить каталог проекта и volume для временного storage.
3. Скопировать `backend/.env.example` в `backend/.env`.
4. Скопировать `frontend/.env.example` в `frontend/.env` при необходимости смены API URL.

## Первый запуск

1. Выполнить `docker compose up --build -d`.
2. Проверить `http://<host>:8080`.
3. Проверить `http://<host>:8080/api/v1/health`.
4. Проверить `http://<host>:8080/api/v1/ready`.

## Smoke-проверка

1. Загрузить два тестовых DBF.
2. Дождаться статуса `completed`.
3. Открыть preview по секциям.
4. Скачать Excel-отчёт.
5. Выполнить ручную очистку задания.

## Обновление

1. Получить новую версию проекта.
2. Выполнить `docker compose up --build -d`.
3. Повторить smoke-проверку.

## Rollback

1. Вернуть предыдущую ревизию проекта.
2. Выполнить `docker compose up --build -d`.
3. Проверить health/readiness.

## Диагностика

- Проверить логи API: `docker compose logs api`.
- Проверить логи worker: `docker compose logs worker`.
- Проверить readiness: `curl http://localhost:8080/api/v1/ready`.
- Проверить storage-каталог и свободное место.
