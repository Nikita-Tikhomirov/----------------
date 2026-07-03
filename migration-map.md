# Карта переноса на Beget

Дата последнего обновления: 2026-07-03.

## Выполнено 2026-07-03

- `apreal.spb.ru`: сайт создан на Beget, архив `apreal.spb.ru.zip` загружен и распакован в `/home/n/nousroc9/apreal.spb.ru/public_html`. БД `nousroc9_aprlspb` создана и импортирована из `a278429_aprlspb.sql`, после импорта найдено `35` таблиц. Старый парковочный `index.html` от Макхоста убран в резервный файл, временные debug-define из `wp-config.php` удалены, кеш WordPress очищен. Публичная проверка: `apreal.spb.ru` и `www.apreal.spb.ru` дают `200`, `charset=UTF-8`, видимых `Notice/Warning/Fatal error` нет.
- `fstek.spb.ru`: сайт создан на Beget, архив `fstek.spb.ru.zip` загружен и распакован в `/home/n/nousroc9/fstek.spb.ru/public_html`. БД `nousroc9_fstek` создана и импортирована из `a278429_fstek.sql`, после импорта найдено `24` таблицы. Временные debug-define из `wp-config.php` удалены, кеш WordPress очищен. Публичная проверка: `fstek.spb.ru` и `www.fstek.spb.ru` дают `200`, `charset=UTF-8`, видимых `Notice/Warning/Fatal error` нет.
- `medlic.spb.ru`: сайт создан на Beget, архив `medlic.spb.ru.zip` загружен и распакован в `/home/n/nousroc9/medlic.spb.ru/public_html`. БД `nousroc9_medspb` создана и импортирована из `a278429_medspb.sql`, после импорта найдено `30` таблиц. Публичная проверка: `medlic.spb.ru` и `www.medlic.spb.ru` дают `200`, видимых `Notice/Warning/Fatal error` нет.
- `fste.ru`: после смены PHP на стороне панели добавлен HTTP-заголовок `charset=windows-1251` в `.htaccess`, потому что файлы сайта в Windows-1251 и браузер показывал кракозябры. Публичная проверка: `fste.ru` редиректит на `www.fste.ru`, финальный ответ `200`, `charset=windows-1251`, русский текст читается.
- Версии PHP для `apreal.spb.ru`, `fstek.spb.ru`, `medlic.spb.ru` и `fste.ru` выставлены пользователем в панели Beget.

## Выполнено 2026-07-01

- `lfsb.ru`: сайт создан на Beget, архив распакован в `/home/n/nousroc9/lfsb.ru/public_html`, домены `lfsb.ru` и `www.lfsb.ru` привязаны к сайту. БД не подключалась: в архиве нет DB-конфига, в SQL-файлах текущей папки совпадений по содержимому не найдено. Проверка по Host header: `lfsb.ru` — `200`, `www.lfsb.ru` — `200`.
- `fste.ru`: сайт создан на Beget, архив распакован в `/home/n/nousroc9/fste.ru/public_html`, домены `fste.ru` и `www.fste.ru` привязаны к сайту. БД не подключалась: в архиве нет DB-конфига, в SQL-файлах текущей папки совпадений по содержимому не найдено. Проверка по Host header: `fste.ru` — `301` на `www.fste.ru`, `www.fste.ru` — `200`.
- Версии PHP для этих сайтов не менялись.

## Состояние Beget на 2026-07-01 перед расширением работ

- Вход в панель Beget прошел успешно.
- Тариф: `Blog`.
- Диск: занято `9,3 из 12 ГБ`.
- Сайты: занято `7 из 7`.
- Уже занятые сайты в разделе Beget `Сайты`:
  - `dpomuc.ru`
  - `ed-kgd.ru`
  - `muc-vrn.ru`
  - `nousro-nn.ru`
  - `nousro-spb.ru`
  - `nousro.ru`
  - `test.nousro.ru`
- MySQL: 8 существующих баз, сервер для сайтов `localhost`, версия MySQL `8.0`.
- Beget API по паролю от панели вернул `AUTH_ERROR`; вероятно, нужен отдельный API-пароль или включение доступа в настройках.

## Блокеры, зафиксированные на 2026-07-01

- Нельзя создать новые сайты: лимит `7/7` уже исчерпан.
- Свободного диска недостаточно: для имеющихся не исключенных архивов нужно примерно `4,54 ГБ` после распаковки, без учета MySQL и временных файлов; свободно примерно `2,7 ГБ`.
- Нельзя удалять или заменять существующие сайты без отдельного подтверждения.
- Для части доменов в папке нет ZIP и/или SQL, поэтому их нельзя перенести из текущего набора файлов.

## Исключены по задаче

| Домен | Причина |
| --- | --- |
| `apkonsalt.ru` | Не нужно переносить |
| `apreal-samara.ru` | Не нужно переносить |
| `attox.ru` | Не нужно переносить |
| `feo.taxi` | Не нужно переносить |
| `dpomuc.ru` | Уже перенесен |
| `ed-crimea.ru` | Уже перенесен |
| `nousro-spb.ru` | Уже перенесен |

## Сопоставление сайтов и БД

Сопоставление сделано по содержимому: конфиги сайта, `siteurl/home` в SQL, тип таблиц и структура CMS. Имена файлов SQL используются только как идентификаторы найденных файлов.

| Домен | ZIP | CMS / признаки | SQL для импорта | Подтверждение внутри SQL | PHP со скрина |
| --- | --- | --- | --- | --- | --- |
| `apreal-nn.ru` | `apreal-nn.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_aprealnn.sql` | `siteurl/home=https://apreal-nn.ru` | 7.3 |
| `apreal-volgograd.ru` | `apreal-volgograd.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_vlg.sql` | `siteurl/home=https://apreal-volgograd.ru` | 5.6 |
| `apreal.ru` | `apreal.ru.zip` | WordPress, корневой `wp-config.php`, prefix `wp_`; `trash/wp-config.php` не основной | `a66165_docpastr.sql` | `siteurl/home=https://www.apreal.ru` | 7.4 |
| `apreal.spb.ru` | `apreal.spb.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a278429_aprlspb.sql` | `siteurl/home=https://apreal.spb.ru`; старый DB config указывал на `a278429_aprlspb` | Выставлена пользователем |
| `apreal36.ru` | `apreal36.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_apreal36.sql` | `siteurl/home=http://apreal36.ru` | 7.3 |
| `apreal72.ru` | `apreal72.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_apreal72.sql` | `siteurl/home=http://apreal72.ru`; файл `a66165_apreal72 (1).sql` полный дубль по SHA256 | 5.6 |
| `docp.ru` | `docp.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_docp.sql` | `siteurl/home=https://docp.ru`; `a66165_docp2.sql` тоже основной `docp.ru`, см. риски ниже | 7.3 |
| `elecktro.ru` | `elecktro.ru.zip` | WordPress-конфиг найден в `backup/_old/wp-config.php`; архив требует ручной проверки корня | `a66165_elecktro.sql` | `siteurl/home=https://elecktro.ru` | 7.1 |
| `fste.ru` | `fste.ru.zip` | Файловый/PHP-сайт, явного DB-конфига не найдено; файлы в Windows-1251 | БД не найдена | В ZIP нет типового MySQL-конфига; совпадений по SQL текущей папки нет; на Beget добавлен `charset=windows-1251` | Выставлена пользователем |
| `fstek.spb.ru` | `fstek.spb.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a278429_fstek.sql` | `siteurl/home=https://fstek.spb.ru` | Выставлена пользователем |
| `fsa-lab.ru` | `fsa-lab.ru.zip` | Файловый/PHP-сайт, явного DB-конфига не найдено | БД не найдена | В ZIP нет типового MySQL-конфига | 7.1 |
| `lfsb.ru` | `lfsb.ru.zip` | Файловый/PHP-сайт, явного DB-конфига не найдено | БД не найдена | В ZIP нет типового MySQL-конфига; совпадений по SQL текущей папки нет | Не менялась |
| `mca24.ru` | `mca24.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_mca24.sql` | `siteurl/home=http://mca24.ru` | 7.1 |
| `mchs-vrn.ru` | `mchs-vrn.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_mchsvrn.sql` | `siteurl/home=http://mchs-vrn.ru` | 7.1 |
| `med-license.ru` | `med-license.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_licm.sql` | `siteurl/home=http://med-license.ru` | 5.6 |
| `medlic.spb.ru` | `medlic.spb.ru.zip` | WordPress, `wp-config.php`, prefix `lm_` | `a278429_medspb.sql` | `siteurl/home=http://medlic.spb.ru` | Выставлена пользователем |
| `mhsl.ru` | `mhsl.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_mhsl2.sql` | `siteurl/home=https://mhsl.ru`; свежее, чем `a66165_mhsl.sql`, по датам данных | 5.4 |
| `moopb.ru` | `moopb.ru.zip` | Файловый/PHP-сайт, явного DB-конфига не найдено | БД не найдена | В ZIP нет типового MySQL-конфига | 5.4 |
| `otxodi.ru` | `otxodi.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_otxodi.sql` | `siteurl/home=http://otxodi.ru` | 7.1 |
| `rectavr.ru` | `rectavr.ru.zip` | WordPress, `wp-config.php`, prefix `wp_` | `a66165_rectavrd.sql` | `siteurl/home=https://rectavr.ru` | 5.4 |
| `shopap.ru` | `shopap.ru.zip` | OpenCart, `config.php` и `admin/config.php`, prefix `oc_` | `a66165_newshop.sql` | Таблицы `oc_*`, ссылки `shopap.ru`; `a66165_newshop2.sql` относится к `test.shopap.ru` WordPress | 5.4 |

## Найдены SQL без подходящего ZIP

| SQL | Что внутри |
| --- | --- |
| `a66165_feoed.sql` | WordPress `feo-edem.ru`, prefix `lm_`, `siteurl/home=https://feo-edem.ru`; ZIP для `feo-edem.ru` в папке не найден |
| `a66165_pitdocp.sql` | WordPress `piter.docp.ru`, не основной `docp.ru` |
| `a66165_samara.sql` | WordPress `apreal-samara.ru`, но домен исключен из переноса |
| `a66165_newshop2.sql` | WordPress `test.shopap.ru`, не основной OpenCart `shopap.ru` |
| `a66165_mhsl.sql` | WordPress `mhsl.ru`, но выбран `a66165_mhsl2.sql` как более актуальный и совпадающий с конфигом сайта |

## Нет исходников в текущей папке

Для этих доменов из исходного списка не найден полный комплект файлов в текущей папке:

- `91web.ru`
- `dpocenter.ru`
- `feo-edem.ru` — есть только SQL, нет ZIP сайта
- `linkedin.com.moopb.ru`

## Риски и ручные проверки

- `docp.ru`: `a66165_docp.sql` и `a66165_docp2.sql` оба содержат `siteurl/home=https://docp.ru`. Для импорта выбран `a66165_docp.sql`, потому что он соответствует конфигу сайта и содержит больше INSERT-блоков; перед DNS-переключением нужно визуально сравнить с текущим сайтом.
- `elecktro.ru`: `wp-config.php` найден только в `backup/_old/`. Нужно проверить структуру архива перед заливкой: возможно, рабочий сайт лежит в backup-папке или архив снят не из корня.
- `fsa-lab.ru` и `moopb.ru`: БД не найдена; выглядят как файловые/PHP-сайты, но после загрузки нужно проверить формы и отправку почты.
- На Beget MySQL 8.0; старые WordPress/OpenCart на PHP 5.4-5.6 могут потребовать совместимую версию PHP и отключение старых несовместимых плагинов.

## Что было нужно перед продолжением переноса на 2026-07-01

1. Освободить или увеличить лимит сайтов на Beget: сейчас `7/7`.
2. Освободить или увеличить диск минимум на `5 ГБ`, лучше с запасом `7-8 ГБ` под распаковку, кеши и БД.
3. Подтвердить, можно ли удалять/заменять какие-то из текущих сайтов Beget, если апгрейд тарифа не планируется.
4. Дослать отсутствующие ZIP/SQL для доменов из раздела `Нет исходников`, если их тоже нужно переносить.
