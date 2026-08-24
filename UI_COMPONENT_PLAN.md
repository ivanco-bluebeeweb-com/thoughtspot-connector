# ThoughtSpot Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `thoughtspot-connector`.

## 0. Разница с IDEAL_ONBOARDING.md

Реализация ниже строго из существующего словаря `imperal_sdk.ui`. Единственный
компромисс — health snapshot после connect считается синхронно в первом
рендере sidebar (без фонового job), поэтому первый рендер может занять на
1-2 секунды больше при большом количестве Liveboards/Answers.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |\n|---|---|---|
| Sidebar (left) | `ui.Stack`(v, align="stretch") + connect `ui.Form`(instance_hostname/username/password, все с лейблами и контекстными placeholder) + `ui.Divider` + Tags список (`ui.Stack` v, без карточек, без иерархии — плоский список) + `ui.Button`("App settings") | Без карточек по стандарту; теги — плоский список, не дерево (ThoughtSpot не имеет папок). |
| Tag content (center, `center_overlay=True`) | `ui.Tabs`(Liveboards/Answers) + `ui.DataTable`(name, updated_at) в каждой вкладке | Табы — тот же паттерн, что у Looker Folder content, для двух типов контента одного тега. |
| Liveboard Detail | Back-button + `ui.KeyValue`(created_by/updated_at) + `ui.Button`("Export as PDF"/"Export as PNG"/"Export as CSV") | Экспорт — основная операция над готовым Liveboard. |
| Answer Detail | Back-button + `ui.KeyValue`(worksheet/created_by) + `ui.Button`("Export") → `ui.DataTable`(результат как таблица) | Результат Answer естественно табличный. |
| Search (natural language) | `ui.Form`(worksheet_id select + query text input, оба с лейблами) → `ui.DataTable`(результат) | Уникальная фича ThoughtSpot — отдельный экран, не переиспользует форму подключения. |
| Worksheets | `ui.DataTable`(name, description) | Простой список семантических моделей — read-only метаданные в v1. |
| Users / Groups | `ui.DataTable`(name, email/display_name) | Табличный список — стандартный паттерн admin-списков в портфеле. |
| App settings (center, `center_overlay=True`) | Connections список + Disconnect-кнопки + Health snapshot (`ui.Stats`) | Единственное место с disconnect — не дублируется в sidebar. |
| Connect help (overlay) | `ui.Stack`(v) с шагами получения credentials | slot="overlay", НЕ "modal" (это невалидный слот — подтверждено на Google Looker Connector). |

## 2. Проверенные корректные kwargs (накопленный опыт портфеля)

`ui.Badge(label=, color=)` — НЕ `variant`. `ui.Stack(direction="v", align=,
gap=, children=)` — нет `ui.Column`. `ui.Input(param_name=, placeholder=)` —
нет `input_type`. `ui.DataTable(columns=, rows=, on_row_click=,
on_cell_edit=)` — нет `row_action`/`empty_message`. `@ext.panel(slot=)` —
только `bottom|center|chat-sidebar|left|overlay|right`, НЕ `modal`/`main`.
