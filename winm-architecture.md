## Архитектура WinM (UML-диаграмма для GitHub)

Ниже — диаграмма в формате Mermaid, который GitHub умеет рендерить напрямую. Показаны только основные сервисы и их связи.

```mermaid
flowchart LR
    %% Основные сервисы
    subgraph Server["server (FastAPI)"]
        API["REST API\n(/api/*, /api/auth/token,\n/api/llm/answer)"]
        METRICS["/metrics\n(Prometheus)"]
    end

    subgraph Consumer["consumer (worker)"]
        QCONS["Consumer очереди"]
        GWRITER["Graph writer"]
        EXPORT["Экспорт\nexports/events.jsonl"]
    end

    subgraph Shared["shared"]
        EVENTS["EventType,\nbuild_event"]
    end

    subgraph LLM["llm-service"]
        LLMHTTP["/chat endpoint"]
    end

    NEO4J[("Neo4j\n(graph DB)")]
    RABBIT[("RabbitMQ\n(message broker)")]
    PROM[("Prometheus")]

    %% Связи server
    API --> NEO4J:::read
    API --> RABBIT:::write
    API --> LLMHTTP
    METRICS --> PROM

    %% Связи consumer
    QCONS --> RABBIT
    QCONS --> GWRITER
    QCONS --> EXPORT
    GWRITER --> NEO4J:::write

    %% Общий доменный слой
    Server --- EVENTS
    Consumer --- EVENTS

    classDef read stroke:#1f78b4,stroke-width:2px;
    classDef write stroke:#33a02c,stroke-width:2px;
```

Описание:

- **Server**: читает из Neo4j, публикует события в RabbitMQ, отдаёт REST API и метрики для Prometheus, проксирует запросы к `llm-service`.
- **Consumer**: подписывается на очередь RabbitMQ, пишет изменения в Neo4j и экспортирует события в `exports/events.jsonl`.
- **Shared**: общие типы событий (`EventType`) и фабрика `build_event`, которые используют и server, и consumer.
- **llm-service**: отдельный сервис, который обрабатывает запросы от server по HTTP.

