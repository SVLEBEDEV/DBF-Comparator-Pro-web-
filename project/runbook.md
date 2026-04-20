# Runbook

## Назначение

Этот runbook описывает первый production-like деплой `DBF Comparator Pro v2` на VPS и базовые действия по эксплуатации.

Основной сценарий для первого запуска на Beget описан отдельно в:

- [project/beget-deploy.md](/Users/thelebedevs/DBF Comparator PRO v2/project/beget-deploy.md)

## Что используется на сервере

- `docker-compose.prod.yml`
- `.env.production`
- `infra/nginx/Dockerfile`
- `infra/nginx/default.prod.conf.template`

## Первый запуск

1. Подключиться к VPS.
2. Склонировать репозиторий в `/opt/dbf-comparator-pro`.
3. Скопировать `.env.production.example` в `.env.production`.
4. Заполнить пароль БД и IP/домен в `CORS_ORIGINS`.
5. Выполнить:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## Проверка после запуска

1. Открыть `http://<server-ip>`.
2. Проверить `http://<server-ip>/api/v1/health`.
3. Проверить `http://<server-ip>/api/v1/ready`.
4. Выполнить ручной smoke:
   - загрузить два DBF;
   - дождаться завершения проверки;
   - открыть детали;
   - скачать Excel-отчёт.

## Обновление версии

```bash
cd /opt/dbf-comparator-pro
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## Перезапуск

```bash
cd /opt/dbf-comparator-pro
docker compose --env-file .env.production -f docker-compose.prod.yml restart
```

## Остановка

```bash
cd /opt/dbf-comparator-pro
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

## Логи

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs proxy --tail=100
docker compose --env-file .env.production -f docker-compose.prod.yml logs api --tail=100
docker compose --env-file .env.production -f docker-compose.prod.yml logs worker --tail=100
```

## Rollback

1. Перейти в каталог проекта.
2. Вернуться на предыдущий коммит или тег.
3. Выполнить повторную сборку:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

4. Повторить `health`, `ready` и ручной smoke.

## Что важно не забыть

- `.env.production` не коммитится в git;
- пароль PostgreSQL должен быть заменён перед первым запуском;
- первый этап может работать по IP и HTTP;
- HTTPS и домен лучше делать вторым отдельным этапом, когда базовый деплой уже стабильно работает.
