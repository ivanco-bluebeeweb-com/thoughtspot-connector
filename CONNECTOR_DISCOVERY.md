# ThoughtSpot Connector — Discovery

**Статус:** discovery завершён, готов к PREPARATION.md
**Источники:** developers.thoughtspot.com/docs/rest-apiv2-reference
(REST API v2), developers.thoughtspot.com/docs/api-authv2 (trusted auth /
V2 token auth).

## 1. Что за продукт

ThoughtSpot — Search & AI-driven аналитика (естественный язык → запрос,
"Google для данных"). Ключевые объекты: **Liveboards** (аналог Dashboard,
набор визуализаций), **Answers** (единичный результат поиска/запроса,
аналог Look/сохранённого запроса), **Worksheets/Models** (семантический
слой, объединяет таблицы), **Search** (сам естественно-языковой запрос,
можно вызывать программно через Search API). Существует ThoughtSpot Cloud
(SaaS, `<org>.thoughtspot.cloud`) и Software (self-hosted) — API
идентичен, отличается только базовый URL.

## 2. API-поверхность

REST API v2: `https://<instance>/api/rest/2.0/*`.

- **Auth** (`/auth/token/full`) — обмен `username`+`password` (или
  secret_key для service account) на Bearer `token` с TTL (по умолчанию
  проект-специфичный, обычно несколько часов) — самая близкая модель к
  Looker (login → короткоживущий токен, без refresh, прозрачный re-login).
- **Liveboards** (`/metadata/liveboard/search`, `/report/liveboard/{id}`) —
  список и экспорт (PDF/PNG/CSV) дашбордов.
- **Answers** (`/metadata/answer/search`, `/report/answer/{id}`) — список
  сохранённых Answers, экспорт результата.
- **Worksheets** (`/metadata/worksheet/search`) — метаданные семантического
  слоя (аналог LookML Model / Explore).
- **Search** (`/searchdata`) — программный запуск natural-language запроса
  против Worksheet с сохранением/без сохранения результата — уникальная
  для ThoughtSpot возможность среди всех BI-коннекторов портфеля.
- **Users/Groups** (`/user/search`, `/group/search`) — управление доступом.
- **Tags** (`/tag/search`) — теги для организации Liveboards/Answers
  (аналог Folders у других BI-платформ, но применяется как метка, не
  контейнер — важное структурное отличие).
- **Metadata TML export/import** (`/metadata/tml/export`) — экспорт
  объекта как YAML (ThoughtSpot Modeling Language) — для миграции/
  version control, кандидат Ярус 2/3 (сложный, риск конфликтов).

## 3. Авторизация

Bearer token, обменивается через `POST /api/rest/2.0/auth/token/full` с
`username`+`password` (или секретным ключом сервисного аккаунта). TTL
токена конфигурируется на инстансе (администратором) — коннектор должен
транспарентно перелогиниваться по 401, аналогично Looker/Tableau.

## 4. Отличия от Power BI / Tableau / Qlik / Looker

- Поисковый (natural-language) слой (`/searchdata`) — уникальная фича,
  ничего похожего у остальных 4 BI-коннекторов портфеля нет.
- Организация контента через Tags (метки), а не строгую иерархию папок —
  UI должен фильтровать по тегам, а не строить дерево.
- Нет отдельного понятия "Space"/"Workspace" в v2 API на уровне
  контейнера — весь контент организации плоский, доступ регулируется ролями
  и группами.

## 5. Вне scope v1

- TML export/import (сложный YAML-формат, риск конфликтов при записи).
- Embed SDK / SSO trusted authentication (для встраивания в чужие сайты).
- ThoughtSpot Sage (расширенный AI-слой) — отдельный продукт/лицензия.
