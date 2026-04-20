# Деплой на Beget VPS

## Для чего этот документ

Этот документ помогает впервые развернуть `DBF Comparator Pro v2` на обычном VPS от Beget без опыта в DevOps.

Ниже описан самый простой и безопасный стартовый вариант:

- сервер на Beget VPS;
- Ubuntu или готовый образ Docker;
- запуск через `docker compose`;
- доступ к приложению по IP-адресу сервера;
- без HTTPS на первом шаге.

HTTPS, домен и дополнительное усиление безопасности можно подключить вторым этапом, когда первое развёртывание уже заработает.

## Что нужно заранее

Подготовьте:

1. Аккаунт на Beget.
2. Созданный VPS-сервер.
3. Публичный IP сервера.
4. Логин `root` и пароль от сервера, либо SSH-ключ.
5. Установленный на вашем компьютере терминал.
6. Этот репозиторий на GitHub.

## Какой сервер выбрать на Beget

Для первого запуска подойдёт:

- Ubuntu 24.04
или
- готовый образ `Docker` в каталоге приложений Beget.

Если есть выбор и вы хотите проще, берите готовый образ `Docker`.

Минимально разумная конфигурация для старта:

- 2 vCPU
- 4 GB RAM
- 40+ GB SSD/NVMe

Если пользователей мало и это pilot, этого обычно хватает.

## Шаг 1. Подключиться к серверу

На вашем компьютере откройте Terminal и выполните:

```bash
ssh root@IP_ВАШЕГО_СЕРВЕРА
```

Пример:

```bash
ssh root@123.123.123.123
```

Если система спросит `Are you sure you want to continue connecting`, ответьте:

```bash
yes
```

После этого введите пароль от VPS.

## Шаг 2. Установить Docker, если вы выбрали обычную Ubuntu

Если на Beget вы выбрали готовый образ `Docker`, этот шаг можно пропустить.

Проверьте:

```bash
docker --version
docker compose version
```

Если команды не работают, установите Docker:

```bash
apt update
apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
docker --version
docker compose version
```

## Шаг 3. Забрать проект на сервер

На сервере выполните:

```bash
cd /opt
git clone https://github.com/SVLEBEDEV/DBF-Comparator-Pro-web-.git dbf-comparator-pro
cd /opt/dbf-comparator-pro
```

Проверьте, что вы видите файлы проекта:

```bash
ls
```

## Шаг 4. Подготовить production env-файл

В проекте уже есть шаблон:

```bash
cp .env.production.example .env.production
```

Откройте файл редактором `nano`:

```bash
nano .env.production
```

### Что нужно изменить в `.env.production`

Найдите и замените значения:

```env
POSTGRES_PASSWORD=change_me_please
DATABASE_URL=postgresql+psycopg://dbf_comparator:change_me_please@postgres:5432/dbf_comparator
CORS_ORIGINS=["http://SERVER_IP_OR_DOMAIN"]
```

#### Как заполнять правильно

`POSTGRES_PASSWORD`

- придумайте длинный пароль;
- например 20+ символов;
- используйте буквы и цифры.

Пример:

```env
POSTGRES_PASSWORD=DbfComparator2026SecurePass
```

`DATABASE_URL`

- пароль внутри строки должен быть тем же самым, что и в `POSTGRES_PASSWORD`.

Пример:

```env
DATABASE_URL=postgresql+psycopg://dbf_comparator:DbfComparator2026SecurePass@postgres:5432/dbf_comparator
```

`CORS_ORIGINS`

- если будете открывать сайт по IP сервера, укажите IP;
- если позже подключите домен, замените IP на домен.

Пример для IP:

```env
CORS_ORIGINS=["http://123.123.123.123"]
```

Пример для домена:

```env
CORS_ORIGINS=["https://dbf.example.ru"]
```

### Как сохранить файл в nano

1. Нажмите `Ctrl + O`
2. Нажмите `Enter`
3. Нажмите `Ctrl + X`

## Шаг 5. Первый запуск контейнеров

Выполните:

```bash
cd /opt/dbf-comparator-pro
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Первая сборка может занять несколько минут. Это нормально.

## Шаг 6. Проверить, что всё запустилось

Посмотрите список контейнеров:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Вы должны увидеть сервисы:

- `proxy`
- `api`
- `worker`
- `postgres`
- `redis`

## Шаг 7. Проверить сайт и API

Откройте в браузере:

```text
http://IP_ВАШЕГО_СЕРВЕРА
```

Если интерфейс открылся, это уже хороший знак.

Дополнительно проверьте API:

```text
http://IP_ВАШЕГО_СЕРВЕРА/api/v1/health
```

и

```text
http://IP_ВАШЕГО_СЕРВЕРА/api/v1/ready
```

Если всё хорошо, вы увидите JSON-ответ.

## Шаг 8. Если сайт не открылся

Сначала посмотрите логи:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs proxy
docker compose --env-file .env.production -f docker-compose.prod.yml logs api
docker compose --env-file .env.production -f docker-compose.prod.yml logs worker
```

Если логов слишком много, добавьте `--tail=100`:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml logs api --tail=100
```

## Шаг 9. Проверить firewall на Beget/VPS

Если контейнеры запущены, но сайт не открывается по IP, проверьте:

1. открыт ли порт `80`;
2. не закрыт ли доступ firewall;
3. назначен ли серверу публичный IPv4.

Для проверки на самом сервере:

```bash
ss -tulpn | grep :80
```

Если всё хорошо, вы увидите процесс, слушающий `0.0.0.0:80`.

## Как обновлять проект позже

Когда в GitHub появятся новые коммиты:

```bash
cd /opt/dbf-comparator-pro
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## Как перезапустить проект

```bash
cd /opt/dbf-comparator-pro
docker compose --env-file .env.production -f docker-compose.prod.yml restart
```

## Как остановить проект

```bash
cd /opt/dbf-comparator-pro
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

## Где лежат данные

В production compose используются Docker volumes:

- `postgres-data` — база данных PostgreSQL;
- `redis-data` — данные Redis;
- `storage-data` — временные файлы, uploads и артефакты сравнения.

Это значит, что данные не пропадут просто от перезапуска контейнера.

## Что я рекомендую сделать сразу после первого успешного запуска

1. Проверить загрузку двух тестовых DBF-файлов.
2. Выполнить реальное сравнение.
3. Скачать Excel-отчёт.
4. Убедиться, что `ready` открывается без ошибок.
5. Сохранить `.env.production` отдельно в безопасное место.

## Что лучше сделать вторым этапом

После первого успешного запуска я рекомендую отдельно доделать:

1. домен;
2. HTTPS;
3. резервное копирование БД;
4. ограничение доступа по IP, если это внутренний сервис;
5. мониторинг и алерты.

## Самая короткая версия команд

Если нужен совсем короткий сценарий, то он такой:

```bash
ssh root@IP_ВАШЕГО_СЕРВЕРА
cd /opt
git clone https://github.com/SVLEBEDEV/DBF-Comparator-Pro-web-.git dbf-comparator-pro
cd /opt/dbf-comparator-pro
cp .env.production.example .env.production
nano .env.production
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```
