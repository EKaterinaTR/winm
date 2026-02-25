# Chaos Engineering — эксперименты для WinM

Проверка отказоустойчивости с помощью [Chaos Mesh](https://chaos-mesh.org/).

## Требования

- Kubernetes-кластер с установленным Chaos Mesh (например, `helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace`).
- Развёрнутое приложение WinM в namespace `winm` (server, consumer, llm-service).

## Эксперимент 1: Pod Kill (consumer)

**Файл:** `pod-kill-consumer.yaml`

**Цель:** Убить один под winm-consumer и убедиться, что Deployment перезапускает под, очередь RabbitMQ не теряет сообщения (при наличии ack), система восстанавливается.

**Запуск:**

```bash
kubectl apply -f chaos/pod-kill-consumer.yaml
```

**Ожидаемое поведение:**

1. Chaos Mesh выбирает один под с меткой `app: winm-consumer` и завершает его (SIGKILL или удаление).
2. Deployment обнаруживает отсутствие пода и создаёт новый (ReplicaSet).
3. Новый под поднимается, подключается к RabbitMQ и продолжает обрабатывать сообщения.
4. Liveness/readiness probes у consumer (exec: pgrep) позволяют Kubelet корректно считать под готовым после старта процесса.

**Наблюдение:**

- До эксперимента: `kubectl get pods -n winm -l app=winm-consumer`
- После применения: один из подов перейдёт в `Terminating`, затем появится новый под.
- Логи: `kubectl logs -n winm -l app=winm-consumer -f`

**Остановка эксперимента:**

```bash
kubectl delete -f chaos/pod-kill-consumer.yaml
```

Эксперимент одноразовый (mode: one, без scheduler), поэтому после срабатывания его можно удалить.

## Дополнительно: Network Delay (опционально)

Для проверки задержки между server и llm-service можно использовать NetworkChaos (задержка трафика до winm-llm). Примеры см. в [документации Chaos Mesh](https://chaos-mesh.org/docs/simulate-network-chaos-on-kubernetes/).

## Итог

- **Гипотеза:** При убийстве пода consumer система остаётся работоспособной за счёт перезапуска пода Deployment и сохранения очереди в RabbitMQ.
- **Метрики:** До/после можно смотреть количество подов, время восстановления, наличие ошибок в логах server/consumer.
