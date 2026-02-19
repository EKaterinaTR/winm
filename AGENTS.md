# Инструкции для агента (WinM)

Краткий контекст проекта для AI-агента (Cursor, Claude Code, Windsurf и др.).

## Что это за проект

WinM — бэкенд для графовой базы знаний визуальной новеллы. REST API (FastAPI) читает из Neo4j и публикует события в RabbitMQ; отдельный consumer обрабатывает очередь, пишет в Neo4j и экспортирует события в JSONL.

## Структура репозитория

| Часть | Назначение |
|-------|------------|
| **server/** | FastAPI: чтение Neo4j, публикация в RabbitMQ, метрики Prometheus. Запись в граф только через consumer. |
| **consumer/** | Подписка на RabbitMQ, запись в Neo4j, экспорт в `exports/events.jsonl`. |
| **shared/** | Общие типы событий (`EventType`, `build_event`). |
| **.cursor/rules/** | Правила Cursor: архитектура, тесты. |
| **docs/** | Описание метрик (например `METRICS.md`). |

## Ключевые соглашения

- **API ресурсов с уникальным именем** (characters, locations, concepts): общий базовый класс `NameResourceRouter` в `server/app/api/base_resource.py`. В тестах мокать `app.api.base_resource.run_read_query` и `app.api.base_resource.publish_event`.
- **Consumer: узлы id/name/description** (Location, Character, Concept) — базовый класс `NameNodeWriter` в `consumer/app/graph.py`. Scene — отдельная логика со связями.
- **Схемы** — в `server/app/models/schemas/` по доменам (location, character, concept, scene, search, llm). Импорт: `from app.models.schemas import ...`.
- **Конфиг**: у server нет `export_dir`; у consumer есть. Примеры: `.env.server.example`, `.env.consumer.example`.

## Запуск тестов

Активировать `.venv` в корне, установить зависимости из `server` и `consumer`.  
Server: `PYTHONPATH="<корень>/server;<корень>"`, из каталога `server` запустить `pytest tests/`.  
Consumer: `PYTHONPATH="<корень>/consumer;<корень>"`, из каталога `consumer` запустить `pytest tests/`.

Подробнее — в `.cursor/rules/winm-testing.mdc`.

## Для человека

Обычный запуск, API, деплой — в **README.md**. Метрики — в **docs/METRICS.md**. Архитектурный обзор и апрувы — в **ARCHITECTURE_REVIEW.md**.
