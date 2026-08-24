# ThoughtSpot Connector — Preparation

## 1. Паспорт приложения

- **Название:** ThoughtSpot Connector
- **Короткое описание:** Управление Liveboards, Answers, Worksheets и
  natural-language поиском ThoughtSpot прямо из Imperal — программные
  запросы, экспорт отчётов и мониторинг контента.
- **Владелец продукта:** vlad@bluebeeweb.com
- **Дата подготовки:** 2026-08-24
- **Почему сейчас:** BI/Аналитика — новая категория портфеля (см.
  `Docs/session-notes/NEXT_12_CATEGORIES_RESEARCH.md` §5); ThoughtSpot —
  Search & AI-driven BI, завершает портфель альтернативой
  Power BI/Tableau/Qlik/Looker с уникальным natural-language слоем.
- **Scope:** максимальный функционал в рамках ThoughtSpot REST API v2 (TML
  export/import и Embed SDK явно вне scope v1, см.
  CONNECTOR_DISCOVERY.md §5).

## 2. Проблема в человеческих словах

Когда **BI/Data аналитик или ThoughtSpot админ** сталкивается с
**необходимостью быстро получить ответ на вопрос о данных, не открывая
отдельный интерфейс ThoughtSpot, или проверить какие Liveboards/Answers
помечены нужным тегом**, ей приходится **переключаться в отдельное
веб-приложение, вручную вводить поисковый запрос там и искать нужный
контент по тегам вручную**, из-за чего возникает **разрыв контекста между
рабочим чатом и BI-инструментом, а natural-language поиск ThoughtSpot
остаётся недоступен как часть автоматизированных сценариев компании**.

## 3. Пользователи и роли

- **BI/Data аналитик** — строит Worksheets/Answers, использует
  natural-language поиск для быстрых вопросов к данным.
- **ThoughtSpot админ** — управляет пользователями/группами/тегами.
- **Руководитель/консьюмер дашбордов** — не имеет прямого доступа к
  приложению, выигрывает от быстрых ответов на вопросы о данных.

## 4. Credential type и авторизация

Bearer token, обменивается через `/auth/token/full` с username+password
(или secret_key сервисного аккаунта) — TTL конфигурируется на инстансе,
без refresh token, прозрачный re-login при истечении (модель ближе всего
к Looker).

## 5. Ярус функционала (максимум в рамках API)

**Ярус 1 (v1, всё что даёт REST API v2):**
connect/disconnect/list_connections, list_liveboards, get_liveboard,
export_liveboard (PDF/PNG/CSV), list_answers, get_answer, export_answer,
list_worksheets, get_worksheet, search_data (natural-language запрос
против Worksheet), list_tags, list_users, list_groups,
audit_instance_health.

**Ярус 2/3 (за пределами v1, см. CONNECTOR_DISCOVERY.md §5):** TML
export/import, Embed SDK/trusted auth, ThoughtSpot Sage.

## 6. Максимальный функционал — обоснование

13 tool-функций покрывают весь read+search+export функционал API v2,
доступный без риска нарушения целостности данных организации (запись в
Worksheets/Liveboards через API v2 крайне ограничена и обычно делается
через UI/TML — вне scope v1 по этой же причине).
