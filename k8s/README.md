# Kubernetes (ветка k8s)

Манифесты для деплоя WinM в кластер. **Neo4j и RabbitMQ по умолчанию разворачиваются из образов внутри кластера с персистентными томами** (см. Helm-чарт).

**Рекомендуемый способ деплоя:** Helm-чарт и GitOps (ArgoCD).

| Способ | Описание |
|--------|----------|
| **Helm** | `helm/winm` — чарт с server, consumer, Neo4j и RabbitMQ (опционально). См. раздел «Деплой через Helm» ниже. |
| **ArgoCD** | Деплой из Git: `argocd/application.yaml` и [argocd/README.md](../argocd/README.md). |
| **Сырые YAML** | Файлы в этом каталоге — для ручного `kubectl apply` (без встроенных Neo4j/RabbitMQ). |

## Деплой через Helm

По умолчанию чарт включает Neo4j и RabbitMQ из образов с PVC. Секрет создаётся из values (dev) или вручную.

```bash
# С секретом из values (пароли не коммитить):
helm upgrade --install winm ./helm/winm -n winm --create-namespace \
  --set secrets.create=true \
  --set secrets.neo4jPassword=YOUR_NEO4J_PASSWORD \
  --set rabbitmq.auth.password=YOUR_RABBITMQ_PASSWORD

# С образами приложения из registry (после CI):
helm upgrade --install winm ./helm/winm -n winm --create-namespace \
  --set secrets.create=true \
  --set secrets.neo4jPassword=YOUR_NEO4J_PASSWORD \
  --set rabbitmq.auth.password=YOUR_RABBITMQ_PASSWORD \
  --set global.imageRegistry=ghcr.io/YOUR_ORG \
  --set server.image.tag=latest \
  --set consumer.image.tag=latest
```

## Секреты

При использовании встроенных Neo4j и RabbitMQ (`neo4j.enabled=true`, `rabbitmq.enabled=true`) и `secrets.create=true` чарт создаёт секрет с ключами: `neo4j-password`, `neo4j-auth`, `rabbitmq-url`, `rabbitmq-default-user`, `rabbitmq-default-pass`, `gigachat-credentials`. Задайте пароли через `--set` или `-f values-secret.yaml`.

Если секрет создаётся вручную (например, Sealed Secrets), создайте его с теми же ключами:

```bash
kubectl create namespace winm
kubectl create secret generic winm-secrets -n winm \
  --from-literal=neo4j-password=YOUR_NEO4J_PASSWORD \
  --from-literal=neo4j-auth="neo4j/YOUR_NEO4J_PASSWORD" \
  --from-literal=rabbitmq-url="amqp://guest:YOUR_RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --from-literal=rabbitmq-default-user=guest \
  --from-literal=rabbitmq-default-pass=YOUR_RABBITMQ_PASSWORD \
  --from-literal=gigachat-credentials=YOUR_BASE64_GIGACHAT_KEY
```

Либо скопировать `secret.example.yaml` в `secret.yaml`, подставить значения и:  
`kubectl apply -f secret.yaml`  
(файл `secret.yaml` добавьте в `.gitignore`.)

## Образы

**CI (GitHub Actions)** при пуше в `main`/`master` собирает образы и пушит в GitHub Container Registry:  
`ghcr.io/<owner>/winm-server` и `ghcr.io/<owner>/winm-consumer` (теги: short SHA и `latest`).

Локальная сборка:

```bash
docker build -f server/Dockerfile -t winm-server:latest .
docker build -f consumer/Dockerfile -t winm-consumer:latest .
```

В Helm задайте `global.imageRegistry` и теги в `values.yaml` или через `--set`.

## Применение

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secret.example.yaml   # или свой secret.yaml
kubectl apply -f server-deployment.yaml
kubectl apply -f server-service.yaml
kubectl apply -f consumer-deployment.yaml
```

## Доступ к API

- Внутри кластера: `http://winm-server.winm.svc.cluster.local:8000`
- Проброс порта: `kubectl port-forward -n winm svc/winm-server 8000:8000`
