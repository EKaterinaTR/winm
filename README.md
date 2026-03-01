# WinM — графовая база знаний для визуальной новеллы

Сервис для заполнения и использования графовой БД связей между понятиями мира визуальной новеллы: локации, персонажи, сцены, понятия. 

REST API для поиска. Хранение в Neo4j и экспорт в файлы (для Git).

## Технологии

- **Сервер**: Python, FastAPI, Neo4j (чтение), RabbitMQ (публикация событий), Prometheus (метрики)
- **Consumer**: Python, RabbitMQ (обработка очереди), Neo4j (запись), экспорт в JSONL
- **LLM-сервис (GigaChat)**: отдельный микросервис `llm-service` — FastAPI, один эндпоинт `/chat`; сервер вызывает его по HTTP при запросах к `/api/llm/answer`
- **Инфраструктура**: Docker Compose (Neo4j, RabbitMQ, Prometheus)
- **Kubernetes**: Helm-чарт в `helm/winm` (server, consumer, llm-service, HPA, RBAC), GitOps через ArgoCD (`argocd/`), CI собирает образы (в т.ч. winm-llm) и пушит в GHCR. Chaos Engineering: эксперименты в `chaos/` (Chaos Mesh).

## Локальный запуск

### Вариант 1: Всё в Docker 

Нужны: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (или Docker + Docker Compose).

```bash
# В корне проекта (winm)
cd c:\Users\User\Desktop\hw\winm

# Опционально: скопировать .env (логин/пароль Neo4j и RabbitMQ)
# Windows: copy .env.example .env
# Linux/macOS: cp .env.example .env

# Поднять всю систему одной командой
docker compose up -d

# Дождаться запуска (10–20 сек), проверить
curl http://localhost:8000/health
```

После этого доступны:
- **API**: http://localhost:8000  
- **Neo4j Browser**: http://localhost:7474 (логин `neo4j`, пароль из `.env` или `password`)  
- **RabbitMQ**: http://localhost:15672 (логин/пароль из `.env` или `guest`/`guest`)  
- **Prometheus**: http://localhost:9090  

Остановить всё:
```bash
docker compose down
```

### Вариант 2: Инфраструктура в Docker, сервер и consumer на хосте

Удобно для разработки (перезапуск кода без пересборки образов).

**Шаг 1.** Поднять только Neo4j, RabbitMQ и Prometheus:
```bash
docker compose up -d neo4j rabbitmq prometheus
```

**Шаг 2.** Установить зависимости и запустить сервер (в одном терминале):
```bash
cd server
pip install -r requirements.txt
set PYTHONPATH=%CD%;..
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
В PowerShell: `$env:PYTHONPATH="$PWD;.."; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**Шаг 3.** В другом терминале — consumer:
```bash
cd consumer
pip install -r requirements.txt
set PYTHONPATH=%CD%;..
python -m app.main
```
В PowerShell: `$env:PYTHONPATH="$PWD;.."; python -m app.main`

По умолчанию сервер и consumer подключаются к `localhost:7687` (Neo4j) и `localhost:5672` (RabbitMQ). Если порты другие — задать переменные окружения (см. `server/app/core/config.py` и `consumer/app/config.py`).  

## Сценарий: ручка → брокер → consumer

1. Клиент: `POST /api/locations` с телом `{"name": "Таверна", "description": "..."}`.
2. Сервер возвращает `202 Accepted` и публикует событие в RabbitMQ (очередь `graph.tasks`).
3. Consumer получает сообщение, создаёт узел в Neo4j и дописывает строку в `exports/events.jsonl`.
4. Чтение: `GET /api/locations` — сервер читает из Neo4j.

## Доступ к API (JWT и Ingress)

### Аутентификация

Все эндпоинты под префиксом `/api/`, кроме `/api/auth/token`, требуют JWT. Эндпоинты `/health` и `/metrics` доступны без токена.

1. Получить токен: `POST /api/auth/token` с телом `{"username": "api", "password": "api"}` (учётные данные задаются переменными `API_USERNAME`, `API_PASSWORD` или по умолчанию `api`/`api`).
2. В запросах к API передавать заголовок: `Authorization: Bearer <access_token>`.

Для локальной разработки можно отключить проверку: `AUTH_DISABLED=true`.

### Ingress (Kubernetes)

В Helm-чарте включён Ingress для доступа к API снаружи кластера. В `helm/winm/values.yaml` задаётся `ingress.enabled: true`, `ingress.className: nginx` и список `ingress.hosts` (по умолчанию `winm-api.local`). Для HTTPS нужно задать `ingress.tls` (имя Secret с сертификатом) и при использовании cert-manager — аннотации, например `cert-manager.io/cluster-issuer: letsencrypt-prod`. Подробнее — комментарии в `values.yaml` в секции `ingress`.

## API (кратко)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/auth/token | Получить JWT (username, password в теле) |
| POST | /api/locations | Создать локацию (202, событие в брокер) |
| GET | /api/locations | Список локаций из графа |
| GET | /api/locations/{id} | Локация по id |
| PATCH | /api/locations/{id} | Обновить локацию (202, событие) |
| POST | /api/characters | Создать персонажа |
| GET | /api/characters | Список персонажей |
| POST | /api/story/scenes | Создать сцену (location_id, character_ids) |
| GET | /api/story/scenes | Список сцен |
| POST | /api/concepts | Создать понятие |
| GET | /api/search?q=... | Поиск по графу |
| POST | /api/llm/answer | Заглушка под LLM (question, role) |

## Метрики

- `GET /metrics` — Prometheus scrape.
- Метрики: `http_server_requests_total`, `http_server_request_duration_seconds`, `events_published_total`, `neo4j_queries_total`.

## Хранение в Git

Consumer пишет события в volume `exports/` в файл `events.jsonl` (каждая строка — JSON события). Чтобы хранить в Git:

1. Примонтировать этот volume в директорию репозитория на хосте (или скопировать `exports/` в репо).
2. Настроить cron/скрипт на хосте: `git add exports/ && git commit -m "Export" && git push`.

Либо использовать отдельный сервис, который периодически дергает API и сохраняет дамп в файлы в репо.

## Тесты и CI

- **Сервер**: из каталога `server` с `PYTHONPATH=.:..` (или из корня с `PYTHONPATH=server:shared`).
- **Consumer**: из каталога `consumer` с `PYTHONPATH=.:..`.

```bash
# Сервер
cd server && pip install -r requirements.txt -r requirements-dev.txt
PYTHONPATH=.:.. pytest tests -v --cov=app --cov-report=term-missing --cov-fail-under=50

# Consumer
cd consumer && pip install -r requirements.txt pytest pytest-cov
PYTHONPATH=.:.. pytest tests -v --cov=app --cov-report=term-missing --cov-fail-under=50
```

CI (GitHub Actions) запускает тесты для server и consumer; в логе job выводится отчёт покрытия (`--cov-report=term-missing`), порог 50% (`--cov-fail-under=50`).

## Для агентов и Cursor

- **AGENTS.md** — краткие инструкции для AI-агента (структура, соглашения, тесты).
- **.cursor/rules/** — правила Cursor: архитектура (always apply), тесты (при работе с `tests/`).
- **CONTRIBUTORS.md** — список участников команды (курс «Проектирование и разработка распределенных программных систем»).
- **docs/COURSE_READINESS.md** — соответствие проекта требованиям курса и чек-лист на защиту.

## Структура проекта

```
winm/
├── docker-compose.yml   # server, consumer, neo4j, rabbitmq, prometheus
├── .github/workflows/ci.yml   # тесты + сборка образов и пуш в GHCR
├── helm/winm/           # Helm-чарт (Chart.yaml, values.yaml, templates/)
├── argocd/              # GitOps: Application для ArgoCD
├── chaos/               # Chaos Mesh: эксперименты (pod-kill и др.)
├── k8s/                 # сырые манифесты (альтернатива Helm)
├── CONTRIBUTORS.md      # участники команды
├── AGENTS.md
├── .cursor/rules/
├── docs/                # METRICS.md, COURSE_READINESS.md
├── shared/
├── prometheus/
├── server/
├── consumer/
├── llm-service/
└── README.md
```
