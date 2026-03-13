## Архитектура WinM (UML-диаграмма для GitHub)

Ниже — диаграмма в формате Mermaid, который GitHub умеет рендерить напрямую.

```mermaid
flowchart LR
    subgraph Clients["Клиенты (Frontend / внешние сервисы)"]
        C[ ]
    end

    subgraph Repo["WinM монорепозиторий"]
        subgraph Server["server (FastAPI)"]
            API["REST API (/api/*)"]
            AUTH["Auth / JWT (/api/auth/token)"]
            LLMProxy["LLM Proxy (/api/llm/answer)"]
            METRICS["/metrics (Prometheus)"]
        end

        subgraph Consumer["consumer (worker)"]
            QCONS["Consumer очереди\n(events consumer)"]
            GWRITER["Запись в Neo4j\n(graph writer)"]
            EXPORT["Экспорт событий\nexports/events.jsonl"]
        end

        subgraph Shared["shared"]
            EVENTS["События домена\nEventType, build_event"]
        end

        subgraph LLM["llm-service\n(отдельный сервис)"]
            LLMHTTP["FastAPI сервис\n/ chat endpoint"]
        end
    end

    subgraph Infra["Инфраструктура"]
        DC["Docker Compose"]
        HELM["Helm-чарт\n(helm/winm)"]
        ARGO["ArgoCD\n(argocd/)"]
        CHAOS["Chaos Mesh\n(chaos/)"]
    end

    NEO4J[("Neo4j\n(graph DB)")]
    RABBIT[("RabbitMQ\n(message broker)")]
    PROM[("Prometheus\n(metrics storage)")]

    C --> API
    C --> AUTH

    API --> NEO4J
    API --> RABBIT
    API --> LLMProxy
    API --> METRICS

    LLMProxy --> LLMHTTP

    QCONS --> RABBIT
    QCONS --> GWRITER
    QCONS --> EXPORT
    GWRITER --> NEO4J

    METRICS --> PROM

    Server --- Shared
    Consumer --- Shared

    DC --> Server
    DC --> Consumer
    DC --> NEO4J
    DC --> RABBIT
    DC --> PROM
    DC --> LLM

    HELM --> Server
    HELM --> Consumer
    HELM --> LLM
    HELM --> PROM

    ARGO --> HELM

    CHAOS --> Server
    CHAOS --> Consumer
```

Описание:

- **Server**: читает из Neo4j, публикует события в RabbitMQ, отдаёт REST API и метрики для Prometheus, проксирует запросы к `llm-service`.
- **Consumer**: подписывается на очередь RabbitMQ, пишет изменения в Neo4j и экспортирует события в `exports/events.jsonl`.
- **Shared**: общие типы событий (`EventType`) и фабрика `build_event`, которые используют и server, и consumer.
- **Инфраструктура**: Docker Compose для локального запуска, Helm-чарт и ArgoCD для Kubernetes, Chaos Mesh для экспериментов с отказоустойчивостью.

