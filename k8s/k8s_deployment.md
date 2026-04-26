# Развертывание
## Docker Image.
У нас есть образ, который автоматически установит зависимости, создаст и изолирует рабочую директорию проекта. На выходе получаем контейнер, который а) можно разворачивать почти на любой ОС ) б) работает изолированно от процессов системы
# Масштабирование
## K8s.
Используем для оркестрации контейнеров:
1. Балансировка нагрузки
2. Автоматическое масштабирование (HPA. Растет нагрузка => увеличиваем количество реплик и обратно)
3. Автоматическое восстановление при сбоях (контейнер упал => перезапускаем, пока реплики работают)

---

## Запуск и деплой

### Предварительные требования
- Установлены `docker` и `kubectl`
- Запущен Kubernetes-кластер (Docker Desktop / minikube / kind)
- В корне проекта лежит файл `.env` с переменной подключения к БД

### Сборка Docker-образа
```bash
docker build -t notify-service-app:latest .
```
> **Для minikube**: выполните `eval $(minikube docker-env)` перед сборкой, либо загрузите готовый образ:  
> `minikube image load notify-service-app:latest`

### Создание секрета
```bash
kubectl create secret generic notify-db-secret --from-env-file=.env
```
> **Важно**: ключ в `.env` должен называться `DB__DATABASE_URL` (совпадать с `secretKeyRef.key` в манифесте).  
> Проверить содержимое секрета:  
> `kubectl get secret notify-db-secret -o jsonpath='{.data}' | jq`

### Применение манифестов
```bash
kubectl apply -f k8s/notify-deployment.yaml
kubectl apply -f k8s/notify-service.yaml
# Если есть HPA, ConfigMap или Postgres-манифесты — примените их аналогично
```

### Проверка и доступ к приложению
```bash
# Дождитесь статуса Running
kubectl get pods -l app=notify-service

# Пробросьте порт на локальную машину (универсально для любой среды)
kubectl port-forward svc/notify-service 8000:80

# Приложение доступно по адресу: http://localhost:8000
```

### Обновление после изменений в коде
Поскольку используется `image: notify-service-app:latest` + `imagePullPolicy: IfNotPresent`, Kubernetes может не подтянуть новую сборку автоматически. После `docker build` выполните:
```bash
kubectl rollout restart deployment notify-service-deployment
kubectl rollout status deployment notify-service-deployment
```

---

## Подробнее про масштабирование
Внедряем HPA для автоматического масштабирования при росте нагрузки.
Можно использовать различные метрики (не ограничиваясь cpu, как в примере)
Пример:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: notify-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: notify-service-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```
