# Что сделать, чтобы ArgoCD заработал (после пуша в репозиторий)

Без правок в репо — только действия в кластере и в ArgoCD.

---

## 1. Установить ArgoCD в кластере (если ещё нет)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Дождаться готовности подов. При необходимости открыть UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Логин: `admin`. Пароль взять так:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

---

## 2. Подключить репозиторий в ArgoCD

**Вариант A — публичный репо**  
В UI: **Settings → Repositories → Connect Repo** — укажите URL репозитория (как в `argocd/application.yaml`: `https://github.com/EKaterinaTR/winm.git`). Для публичного репо логин/пароль не нужны.

**Вариант B — приватный репо**  
Тогда нужны учётные данные (PAT с правами `repo` или логин/пароль). В том же экране укажите URL, username и password (или token).

Через CLI:

```bash
argocd repo add https://github.com/EKaterinaTR/winm.git
# для приватного:
# argocd repo add https://github.com/EKaterinaTR/winm.git --username YOUR_USER --password YOUR_PAT
```

---

## 3. Создать секрет приложения в namespace `winm`

ArgoCD из чарта секрет не создаёт. Создать один раз вручную:

```bash
kubectl create namespace winm
kubectl create secret generic winm-secrets -n winm \
  --from-literal=neo4j-password=YOUR_NEO4J_PASSWORD \
  --from-literal=neo4j-auth="neo4j/YOUR_NEO4J_PASSWORD" \
  --from-literal=rabbitmq-url="amqp://guest:YOUR_RABBITMQ_PASSWORD@rabbitmq:5672/" \
  --from-literal=rabbitmq-default-user=guest \
  --from-literal=rabbitmq-default-pass=YOUR_RABBITMQ_PASSWORD \
  --from-literal=jwt-secret-key=YOUR_JWT_SECRET \
  --from-literal=api-username=api \
  --from-literal=api-password=YOUR_API_PASSWORD
```

Подставьте свои пароли. Если GigaChat не используете, можно не добавлять `gigachat-credentials` или передать пустую строку.

---

## 4. Создать Application в ArgoCD

В `argocd/application.yaml` уже указаны `repoURL` и `targetRevision: k8s`. Применить манифест из своего клона репо (с уже запушенным кодом):

```bash
kubectl apply -f argocd/application.yaml
```

Если файл правили локально и не пушили — применить тот файл, который лежит в репо на GitHub (например, склонировать репо и из корня выполнить `kubectl apply -f argocd/application.yaml`).

Убедиться, что в манифесте:
- `source.repoURL` — ваш репо (например `https://github.com/EKaterinaTR/winm.git`);
- `source.targetRevision` — ветка, куда вы пушите (например `k8s` или `main`);
- `source.path` — `helm/winm`.

---

## 5. Дождаться синхронизации

В UI ArgoCD появится приложение **winm**. При включённом auto-sync оно само синхронизируется. Если нет — нажать **Sync**. Проверить статус:

```bash
argocd app get winm
```

При успехе в namespace `winm` появятся поды (server, consumer, neo4j, rabbitmq, llm и т.д.).

---

## 6. (Опционально) Указать образы из GHCR

В чарте по умолчанию образы могут быть без registry (типа `winm-server:latest`). Если образы лежат в GHCR, в ArgoCD нужно задать параметры (чтобы не менять файлы в репо — через UI или отдельный values):

В UI: открыть приложение **winm** → **App Details** → **Parameters** (или **Edit**), добавить/задать:

- `global.imageRegistry` = `ghcr.io/EKaterinaTR` (или ваш owner)
- `server.image.repository` = `winm-server`
- `server.image.tag` = `latest` (или нужный тег)
- Аналогично для `consumer` и `llm`.

Сохранить и снова нажать **Sync**. Тогда поды подтянут образы из GHCR.

---

**Кратко:** установить ArgoCD → добавить репо в ArgoCD → создать `winm-secrets` в `winm` → применить `argocd/application.yaml` → при необходимости в UI выставить registry и теги образов и сделать Sync. Файлы в репозитории менять не обязательно, если URL репо и ветка в `application.yaml` уже совпадают с тем, что вы запушили.
