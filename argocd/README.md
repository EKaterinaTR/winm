# GitOps с ArgoCD

Деплой WinM через ArgoCD из Git-репозитория.

## Требования

- Кластер Kubernetes с установленным [ArgoCD](https://argo-cd.readthedocs.io/en/stable/getting_started/).
- Репозиторий с чартом в `helm/winm` (доступен для ArgoCD по HTTPS или SSH).

## Подключение репозитория

1. В UI ArgoCD: **Settings → Repositories → Connect Repo**.
2. Либо через CLI:
   ```bash
   argocd repo add https://github.com/YOUR_ORG/winm.git \
     --username YOUR_GITHUB_USER \
     --password YOUR_PAT_OR_TOKEN
   ```
   Для публичного репо можно не указывать username/password.

## Создание Application

1. Замените в `application.yaml` `repoURL` на URL вашего репозитория (и при необходимости `targetRevision`).
2. Примените манифест:
   ```bash
   kubectl apply -f argocd/application.yaml
   ```
3. В UI ArgoCD появится приложение **winm**. Синхронизация выполнится автоматически (auto-sync включён).

## Обновление образов (связка с CI)

После того как CI собирает образы и пушит их в registry (с тегом по коммиту или тегу Git), нужно обновить версию образа в кластере. Варианты:

### Вариант A: Отдельный values-файл для окружения

Создайте в репозитории `helm/winm/values-production.yaml` (добавьте в `.gitignore` если храните секреты) и в нём задайте:

```yaml
global:
  imageRegistry: "ghcr.io/YOUR_ORG"
server:
  image:
    tag: "abc1234"   # тег образа после сборки в CI
consumer:
  image:
    tag: "abc1234"
```

В `argocd/application.yaml` в `source.helm.valueFiles` добавьте `values-production.yaml`. Тогда CI после пуша образа может коммитить обновление тега в этом файле — ArgoCD подхватит изменение при следующем sync.

### Вариант B: ArgoCD Image Updater

Установите [Argo CD Image Updater](https://argocd-image-updater.readthedocs.io/) и аннотируйте Application для автоматического обновления образов по тегам из registry.

### Вариант C: Ручное обновление

В UI ArgoCD: **App Details → Parameters** — изменить `server.image.tag` и `consumer.image.tag`, затем **Sync**.

## Секреты

ArgoCD не создаёт секрет `winm-secrets` из чарта по умолчанию (`secrets.create: false`). Создайте секрет в namespace `winm` вручную или через Sealed Secrets / External Secrets перед первым sync:

```bash
kubectl create secret generic winm-secrets -n winm \
  --from-literal=neo4j-password=YOUR_PASSWORD \
  --from-literal=rabbitmq-url="amqp://user:pass@rabbitmq:5672/" \
  --from-literal=gigachat-credentials=""
```

## Проверка

- Статус приложения: `argocd app get winm`
- Синхронизация: `argocd app sync winm`
- Логи: в UI или `kubectl logs -n winm -l app=winm-server -f`
