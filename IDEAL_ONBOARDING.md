# ThoughtSpot Connector — идеальный первый запуск

Источник: `ONBOARDING_FIRST_LAUNCH_STANDARD.md`. Целевой пользователь:
BI/Data аналитик или ThoughtSpot админ.

## 1. Credential type
Bearer token, обменивается через `/auth/token/full` с username+password
(или secret_key сервисного аккаунта) + instance hostname — TTL
конфигурируется на инстансе, без refresh token, прозрачный re-login при
истечении.

## 2. Идеальный флоу

1. **Первое открытие** — `Empty` со ссылкой на использование существующего
   пользователя ThoughtSpot (или service account) и явным пояснением, что
   инстанс — это `<org>.thoughtspot.cloud` для Cloud или собственный домен
   для Software.
2. **Форма** — instance_hostname (placeholder: `myorg.thoughtspot.cloud`) +
   username + password, все с лейблами и контекстными placeholder-ами.
3. **После успешного подключения** — сразу список тегов (не папок — у
   ThoughtSpot плоская организация через теги) с числом Liveboards/Answers
   под каждым; если тегов нет — точное объяснение "подключение работает,
   но контент организации не размечен тегами" с предложением посмотреть
   весь список без фильтра.
4. **Health snapshot сразу после connect** — сколько Liveboards, сколько
   Answers, сколько Worksheets, сколько пользователей —
   POST_CONNECT_EXPERIENCE принцип, применённый с первого взгляда.
5. **Истечение токена (401 mid-session)** — прозрачный silent re-login на
   тех же username/password, а не общая ошибка 401.
6. **Ошибка username/password invalid** — конкретное сообщение "Логин или
   пароль неверны — проверьте учётные данные ThoughtSpot", не общий
   "Unauthorized".
7. **Search запрос без результатов** — явное объяснение "запрос не вернул
   данных — попробуйте переформулировать или указать другой Worksheet", а
   не пустая таблица без контекста.

## 3. Разница с реализацией сейчас
См. UI_COMPONENT_PLAN.md §0 — реализация ниже строго из существующего
словаря `imperal_sdk.ui`, без компромиссов относительно этого идеального
флоу (ThoughtSpot REST API v2 уже даёт всё необходимое для шагов 1-7).
