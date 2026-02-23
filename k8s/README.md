# Kubernetes (ветка k8s)

Манифесты для деплоя WinM в кластер. Neo4j и RabbitMQ предполагаются развёрнутыми отдельно (в кластере или снаружи).

## Секреты

Создать секрет (реальные значения не коммитить):

```bash
kubectl create namespace winm
kubectl create secret generic winm-secrets -n winm \
  --from-literal=neo4j-password=YOUR_NEO4J_PASSWORD \
  --from-literal=rabbitmq-url="amqp://guest:YOUR_RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --from-literal=gigachat-credentials=YOUR_BASE64_GIGACHAT_KEY
```

Либо скопировать `secret.example.yaml` в `secret.yaml`, подставить значения и:  
`kubectl apply -f secret.yaml`  
(файл `secret.yaml` добавьте в `.gitignore`.)

## Образы

Собрать и при необходимости запушить образы:

```bash
docker build -f server/Dockerfile -t winm-server:latest .
docker build -f consumer/Dockerfile -t winm-consumer:latest .
# Для кластера с registry:
# docker tag winm-server:latest YOUR_REGISTRY/winm-server:latest
# docker push YOUR_REGISTRY/winm-server:latest
```

В манифестах замените `winm-server:latest` на полный образ из registry, если нужно.

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
