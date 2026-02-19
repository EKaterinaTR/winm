# Метрики (Prometheus)

## neo4j_queries_total

**Тип:** Counter  
**Лейблы:** `operation` (строка)

**Назначение:** Считает количество выполненных read-запросов к Neo4j на стороне API (server). Нужна для мониторинга нагрузки на граф и поиска «тяжёлых» операций.

**Где инкрементируется:**
- `list_locations` — GET /api/locations (список локаций)
- `get_location` — GET /api/locations/{id}
- `list_characters` — GET /api/characters
- `get_character` — GET /api/characters/{id}
- `list_concepts` — GET /api/concepts
- `get_concept` — GET /api/concepts/{id}
- `search` — GET /api/search?q=...

**Как использовать:** В Prometheus/графанах можно строить rate по `operation`, сравнивать нагрузку по эндпоинтам и находить аномалии (резкий рост запросов к одному типу операций).

**Примечание:** Create/Update в API не пишут в граф напрямую (события уходят в RabbitMQ), поэтому для них эта метрика не увеличивается; запрос на проверку уникальности имени внутри create/update тоже идёт в Neo4j, но отдельно не метрикуется (при желании можно добавить лейбл `check_unique`).
