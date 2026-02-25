# Helm-чарт WinM

Деплой server, consumer, а также Neo4j и RabbitMQ из образов с персистентными томами.

## Установка

### Вариант A: Neo4j и RabbitMQ из чарта (по умолчанию)

Чарт разворачивает Neo4j и RabbitMQ из официальных образов с PVC. Секрет можно создавать из values:

```bash
helm upgrade --install winm . -n winm --create-namespace \
  --set secrets.create=true \
  --set secrets.neo4jPassword=YOUR_NEO4J_PASSWORD \
  --set rabbitmq.auth.password=YOUR_RABBITMQ_PASSWORD
```

Либо передать через `-f values-secret.yaml` (файл в `.gitignore`).

### Вариант B: Внешние Neo4j/RabbitMQ

Выключите встроенные и создайте секрет вручную:

```bash
helm upgrade --install winm . -n winm --create-namespace \
  --set neo4j.enabled=false \
  --set rabbitmq.enabled=false

kubectl create secret generic winm-secrets -n winm \
  --from-literal=neo4j-password=YOUR_PASSWORD \
  --from-literal=rabbitmq-url="amqp://user:pass@external-rabbitmq:5672/" \
  --from-literal=gigachat-credentials=""
```

Если Neo4j/RabbitMQ включены, но `secrets.create=false`, в секрете должны быть ключи: `neo4j-password`, `neo4j-auth` (формат `neo4j/<password>`), `rabbitmq-url`, `rabbitmq-default-user`, `rabbitmq-default-pass`.

## Образы из registry

После сборки в CI (GHCR) укажите registry и теги:

```bash
helm upgrade --install winm . -n winm --create-namespace \
  --set global.imageRegistry=ghcr.io/YOUR_ORG \
  --set server.image.tag=abc1234 \
  --set consumer.image.tag=abc1234
```

Либо создайте свой `values-production.yaml` и подключайте его через `-f values-production.yaml`.

## Параметры (values.yaml)

| Параметр | Описание |
|----------|----------|
| `server.enabled` / `consumer.enabled` | Включить/выключить компонент |
| `neo4j.enabled` | Развернуть Neo4j из образа (персистентный том) |
| `rabbitmq.enabled` | Развернуть RabbitMQ из образа (персистентный том) |
| `neo4j.persistence.enabled`, `neo4j.persistence.size` | PVC для Neo4j (по умолчанию 10Gi) |
| `rabbitmq.persistence.enabled`, `rabbitmq.persistence.size` | PVC для RabbitMQ (по умолчанию 5Gi) |
| `rabbitmq.auth.user`, `rabbitmq.auth.password` | Учётные данные RabbitMQ (при secrets.create подставляются в секрет) |
| `server.replicaCount` | Число реплик server |
| `server.image.repository`, `server.image.tag` | Образ server |
| `global.imageRegistry` | Префикс registry (например, `ghcr.io/owner`) |
| `secrets.name` | Имя Secret с neo4j-password, rabbitmq-url, gigachat-credentials (и при встроенных neo4j/rabbitmq: neo4j-auth, rabbitmq-default-user, rabbitmq-default-pass) |
| `secrets.create` | Создавать Secret из values (для dev; по умолчанию false) |
