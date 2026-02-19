# Изображения BASALT Casino

Изображения лежат в подкаталогах **`bot/templates/images/en/`** и **`bot/templates/images/ru/`**.

В каждой папке файлы именуются **без** суффикса языка:

**`basalt_{screen}.png`**

- `screen` — идентификатор экрана (см. таблицу ниже).
- Язык задаётся только каталогом: `en` или `ru`.

Путь в коде: `get_image_path(screen, lang)` → `IMAGES_DIR / lang / f"basalt_{screen}.png"`  
Примеры: `images/en/basalt_welcome.png`, `images/ru/basalt_welcome.png`.

---

## Список экранов

| Screen         | Файл в en/ и в ru/        | Назначение                                           |
|----------------|---------------------------|------------------------------------------------------|
| welcome        | basalt_welcome.png        | Первый запуск /start                                 |
| home           | basalt_home.png           | Главное меню                                         |
| account        | basalt_account.png        | Меню «Аккаунт»                                       |
| stats          | basalt_stats.png          | Статистика                                           |
| topup          | basalt_topup.png          | Пополнение баланса                                   |
| withdraw       | basalt_withdraw.png       | Вывод                                                |
| settings       | basalt_settings.png       | Настройки (уведомления, FAST MODE)                   |
| gamemode       | basalt_gamemode.png       | Режим Демо/Реал                                      |
| language       | basalt_language.png       | Выбор языка                                          |
| deposit        | basalt_deposit.png        | Депозит                                              |
| topup          | basalt_topup.png          | Выбор суммы пополнения                               |
| gamelist       | basalt_gamelist.png       | Список игр (8 кнопок)                                |
| 2dice          | basalt_2dice.png          | Игра 1: описание, исход, сумма                       |
| moreless       | basalt_moreless.png       | Игра 2                                               |
| evenodd        | basalt_evenodd.png        | Игра 3                                               |
| dart           | basalt_dart.png           | Игра 4                                               |
| basketball     | basalt_basketball.png     | Игра 5                                               |
| football       | basalt_football.png       | Игра 6                                               |
| bowling        | basalt_bowling.png        | Игра 7                                               |
| slots          | basalt_slots.png          | Игра 8                                               |
| confirm        | basalt_confirm.png        | Подтверждение ставки, Повторить                      |
| win            | basalt_win.png            | Результат: выигрыш                                   |
| loss           | basalt_lost.png           | Результат: проигрыш                                  |
| contact        | basalt_contact.png        | Экран «Отправить контакт» (зачем нужен, один раз)    |
| newapplication | basalt_newapplication.png | Уведомление админу о новой заявке (пополнение/вывод) |
| adminpanel     | basalt_adminpanel.png     | Все экраны админ-панели                              |

**Структура:** в `bot/templates/images/en/` и `bot/templates/images/ru/` по одному файлу на экран. Поддерживаются расширения **.png** и **.jpg** (сначала ищется .png, при отсутствии — .jpg). Суффиксы _en и _ru в именах файлов **не используются** — язык определяется папкой.
