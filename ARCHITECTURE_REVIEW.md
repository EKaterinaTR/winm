# Архитектурный обзор проекта WinM

Отчёт по результатам проверки кода: лишние файлы, дублирование, God class/file, предложения по улучшению по блокам.

---

## 1. Лишние файлы

| Файл | Вердикт |
|------|--------|
| Все текущие файлы | **Лишних файлов нет.** Структура осмысленная: server (API + чтение графа + брокер), consumer (очередь + запись в граф + экспорт), shared (события). |

**Рекомендация:** Не удалять файлы. При рефакторинге дублирования (см. ниже) появятся новые общие модули — старые API-файлы можно будет упростить, но не удалять (маршруты останутся).

---

## 2. Дублирование кода

### 2.1 API: characters, concepts, locations (критично)

**Проблема:** Три файла `server/app/api/characters.py`, `concepts.py`, `locations.py` почти идентичны (~64 строки каждый). Отличаются только:
- префикс роутера и тег;
- метка узла в Cypher (`Character`, `Concept`, `Location`);
- имена схем (CharacterCreate/Update/Read и т.д.);
- тип события (EventType.CHARACTER_* и т.д.).

Один и тот же сценарий: create (проверка уникальности имени → publish), list, get by id, patch (проверка уникальности → publish).

**Предложение (на апрув):**
- Ввести общий модуль `server/app/api/_resource.py` (или `server/app/core/resource_handlers.py`) с фабрикой эндпоинтов: функция, принимающая конфиг (label, schema names, event types, prefix) и возвращающая router.
- В `characters.py`, `concepts.py`, `locations.py` оставить только создание роутера из этой фабрики и подключение к приложению (минимальный код).
- Альтернатива: один файл `entities.py` с тремя роутерами (characters, concepts, locations), если не нужна жёсткая изоляция по файлам.

### 2.2 Consumer: graph.py — create/update для Location, Character, Concept

**Проблема:** Пары `create_location`/`update_location`, `create_character`/`update_character`, `create_concept`/`update_concept` повторяют один и тот же шаблон: MERGE/SET по id, name, description. Отличается только метка узла (`Location`, `Character`, `Concept`).

**Предложение (на апрув):**
- Добавить в `consumer/app/graph.py` две общие функции:
  - `_create_node(label: str, payload: dict, props: list[str]) -> str`
  - `_update_node(label: str, payload: dict, props: list[str]) -> str`
- Реализации `create_location`, `update_location` (и аналоги для Character, Concept) вызывают эти функции с нужной меткой и списком полей. Scene оставить отдельно (есть связи и другая логика).

### 2.3 Нормализация имени: server vs consumer

**Проблема:**
- **Server** (`app/core/validation.py`): `normalize_name(name) = name.strip().lower()` — используется для проверки уникальности в Cypher.
- **Consumer** (`app/handlers.py`): `_normalize_name(name) = name.strip()` (без lower). В БД попадает строка в том регистре, в котором её прислал API.

Итог: уникальность на стороне сервера по `toLower(trim(...))`, в графе может храниться разный регистр. Логика не сломана, но два разных правила «нормализации» — источник путаницы и риска расхождений.

**Предложение (на апрув):**
- Вынести общую нормализацию в `shared/` (например `shared/normalize.py`): одна функция `normalize_name(name: str) -> str` (strip + lower для единообразия уникальности и хранения).
- Server: использовать эту функцию из shared (и при проверке уникальности, и при формировании payload можно передавать уже нормализованное имя или оставить как есть — но проверка только через общую функцию).
- Consumer: заменить `_normalize_name` на импорт из `shared.normalize` и использовать ту же функцию перед записью в граф, чтобы в БД всегда было единое представление (например, lowercase).

---

## 3. God class и God file

**God class:** Нет перегруженных классов. Классы по сути только в конфигах (Settings) и схемах (Pydantic) — это нормально.

**God file:**
- `server/app/models/schemas.py` — все Pydantic-модели в одном файле (~107 строк). Объём умеренный, темы единые (API-схемы). Для текущего размера проекта приемлемо.
- **Предложение (опционально):** При росте числа сущностей разбить на `schemas/locations.py`, `schemas/characters.py` и т.д. и собирать в `models/schemas/__init__.py`. Сейчас можно оставить как есть.

Итог: явных God class/God file нет; при расширении схем — рассмотреть разбиение схем по файлам.

---

## 4. Несогласованности (по файлам)

### 4.1 Метрики Neo4j

**Проблема:** В `locations.py` в list и get вызывается `neo4j_queries_total.labels(operation="...").inc()`. В `characters.py` и `concepts.py` такой метрики нет.

**Предложение (на апрув):** Либо добавить такие же вызовы `neo4j_queries_total` в list/get в `characters.py` и `concepts.py`, либо убрать из `locations.py` — чтобы метрика была единообразной по всем ресурсам.

### 4.2 Синхронный эндпоинт в story

**Проблема:** В `server/app/api/story.py` эндпоинт `update_scene` объявлен как `def update_scene(...)`, остальные эндпоинты в приложении — `async def`. FastAPI отработает, но стиль разный.

**Предложение (на апрув):** Сделать `async def update_scene(...)` и внутри вызывать `await` ни к чему не обязывает (можно оставить тело как есть). Это только единообразие с остальными роутами.

### 4.3 Конфигурация server

**Проблема:** В `server/app/core/config.py` в Settings есть `export_dir`. Экспорт в файл делает только consumer; server эту переменную не использует.

**Предложение (на апрув):** Удалить `export_dir` из server config, чтобы в каждом приложении были только нужные ему настройки. Либо оставить, если планируется общий .env для обоих сервисов и вы хотите один набор переменных — тогда пометить в комментарии, что используется только consumer.

---

## 5. Предложения по блокам (кратко)

### Server

| Что | Предложение |
|-----|-------------|
| API characters/concepts/locations | Вынести общую логику в фабрику роутеров или общий модуль (см. п. 2.1). |
| API story | Сделать `update_scene` async для единообразия. |
| API locations/characters/concepts | Унифицировать использование `neo4j_queries_total`. |
| core/validation | При переносе нормализации в shared — оставить тонкую обёртку или удалить и импортировать из shared. |
| core/config | Убрать `export_dir` или явно задокументировать, что для consumer. |
| core/graph | `run_write_query` не используется в коде — оставить для будущего или удалить, чтобы не раздувать API. |
| models/schemas | Оставить один файл; при росте — разбить по доменам. |

### Consumer

| Что | Предложение |
|-----|-------------|
| graph.py | Ввести общие `_create_node` / `_update_node` для Location, Character, Concept (см. п. 2.2). |
| handlers.py | Использовать единую нормализацию из shared (см. п. 2.3), убрать дублирующую `_normalize_name`. |

### Shared

| Что | Предложение |
|-----|-------------|
| events.py | Оставить как есть. |
| Новый модуль | Добавить `shared/normalize.py` с одной функцией нормализации имени и использовать в server и consumer. |

### Тесты

| Что | Предложение |
|-----|-------------|
| Server | После введения фабрики ресурсов — добавить тесты на фабрику и сократить дубли в test_api_characters/concepts/locations за счёт параметризации или общих хелперов. |
| Consumer | После переноса нормализации в shared — тесты на normalize оставить в shared или в одном месте (server уже тестирует normalize); в consumer проверять только вызов общей функции. |

---

## 6. Сводка рекомендаций для апрува

1. **Дублирование API (characters/concepts/locations):** ввести общую фабрику/хелперы для CRUD ресурса с уникальным именем — апрувить? (да/нет)
2. **Дублирование в consumer graph.py:** ввести `_create_node` / `_update_node` для Location, Character, Concept — апрувить? (да/нет)
3. **Нормализация имени:** вынести в `shared/normalize.py`, использовать в server и consumer (strip+lower везде) — апрувить? (да/нет)
4. **Метрики:** добавить `neo4j_queries_total` в characters и concepts (или убрать из locations) — апрувить? (да/нет)
5. **story.update_scene:** сделать `async def` — апрувить? (да/нет)
6. **Server config:** убрать `export_dir` (или задокументировать) — апрувить? (да/нет)
7. **run_write_query в server/core/graph:** оставить как есть / удалить неиспользуемое — апрувить? (оставить/удалить)

После вашего апрува по пунктам можно переходить к конкретным патчам по каждому пункту.
