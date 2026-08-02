from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from tools import build_apreal_client_report as source
except ModuleNotFoundError:
    import build_apreal_client_report as source  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path("C:/Windows/Fonts")
FONT_REGULAR = FONT_DIR / "arial.ttf"
FONT_BOLD = FONT_DIR / "arialbd.ttf"

PAGE_WIDTH, PAGE_HEIGHT = LETTER
LEFT_MARGIN = 0.65 * inch
RIGHT_MARGIN = 0.65 * inch
TOP_MARGIN = 0.65 * inch
BOTTOM_MARGIN = 0.62 * inch
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

BLUE = colors.HexColor("#2E74B5")
DARK_BLUE = colors.HexColor("#1F4D78")
PALE_BLUE = colors.HexColor("#EAF2F8")
LIGHT_GRAY = colors.HexColor("#F2F4F7")
MID_GRAY = colors.HexColor("#D9E0E7")
DARK_GRAY = colors.HexColor("#4B5563")
GREEN = colors.HexColor("#1F7A45")
PALE_GREEN = colors.HexColor("#E8F5EC")
AMBER = colors.HexColor("#A15C00")
PALE_AMBER = colors.HexColor("#FFF4DE")
BLACK = colors.HexColor("#111111")


def normalize_text(value: object) -> str:
    return (
        str(value)
        .replace("\u2011", "-")
        .replace("\u2013", " - ")
        .replace("\u2014", " - ")
        .replace("\u00a0", " ")
    )


def register_fonts() -> None:
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise FileNotFoundError("Arial fonts are required for the Cyrillic PDF")
    if "APArial" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("APArial", str(FONT_REGULAR)))
        pdfmetrics.registerFont(TTFont("APArial-Bold", str(FONT_BOLD)))
        pdfmetrics.registerFontFamily(
            "APArial",
            normal="APArial",
            bold="APArial-Bold",
            italic="APArial",
            boldItalic="APArial-Bold",
        )


def make_styles() -> dict[str, ParagraphStyle]:
    register_fonts()
    sample = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "APBody",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=9.6,
            leading=13.2,
            textColor=BLACK,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "APSmall",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=7.7,
            leading=10.1,
            textColor=DARK_GRAY,
        ),
        "table": ParagraphStyle(
            "APTable",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=7.5,
            leading=9.4,
            textColor=BLACK,
        ),
        "table_bold": ParagraphStyle(
            "APTableBold",
            parent=sample["BodyText"],
            fontName="APArial-Bold",
            fontSize=7.5,
            leading=9.4,
            textColor=BLACK,
        ),
        "table_header": ParagraphStyle(
            "APTableHeader",
            parent=sample["BodyText"],
            fontName="APArial-Bold",
            fontSize=7.7,
            leading=9.6,
            textColor=DARK_BLUE,
            alignment=TA_LEFT,
        ),
        "title_kicker": ParagraphStyle(
            "APTitleKicker",
            parent=sample["BodyText"],
            fontName="APArial-Bold",
            fontSize=9,
            leading=11,
            textColor=BLUE,
            spaceAfter=5,
        ),
        "title": ParagraphStyle(
            "APTitle",
            parent=sample["Title"],
            fontName="APArial-Bold",
            fontSize=23,
            leading=27,
            textColor=DARK_BLUE,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),
        "subtitle": ParagraphStyle(
            "APSubtitle",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=12,
            leading=16,
            textColor=DARK_GRAY,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "APH1",
            parent=sample["Heading1"],
            fontName="APArial-Bold",
            fontSize=16,
            leading=20,
            textColor=DARK_BLUE,
            spaceBefore=2,
            spaceAfter=9,
        ),
        "h2": ParagraphStyle(
            "APH2",
            parent=sample["Heading2"],
            fontName="APArial-Bold",
            fontSize=11.5,
            leading=15,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "APCaption",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=7.5,
            leading=9.2,
            textColor=DARK_GRAY,
            alignment=TA_CENTER,
            spaceBefore=3,
        ),
        "metric": ParagraphStyle(
            "APMetric",
            parent=sample["BodyText"],
            fontName="APArial-Bold",
            fontSize=15,
            leading=18,
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "APMetricLabel",
            parent=sample["BodyText"],
            fontName="APArial",
            fontSize=7.2,
            leading=9,
            textColor=DARK_GRAY,
            alignment=TA_CENTER,
        ),
        "callout": ParagraphStyle(
            "APCallout",
            parent=sample["BodyText"],
            fontName="APArial-Bold",
            fontSize=9.2,
            leading=12.5,
            textColor=GREEN,
        ),
    }


def paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    escaped = html.escape(normalize_text(text)).replace("\n", "<br/>")
    return Paragraph(escaped, style)


def styled_table(
    rows: Sequence[Sequence[object]],
    widths: Sequence[float],
    styles: dict[str, ParagraphStyle],
    *,
    header: bool = True,
    highlights: dict[tuple[int, int], colors.Color] | None = None,
    repeat_rows: int = 1,
) -> LongTable:
    rendered: list[list[object]] = []
    for row_index, row in enumerate(rows):
        rendered_row: list[object] = []
        for value in row:
            if isinstance(value, (Paragraph, Image, Table, Spacer)):
                rendered_row.append(value)
            else:
                key = "table_header" if header and row_index == 0 else "table"
                rendered_row.append(paragraph(value, styles[key]))
        rendered.append(rendered_row)
    table = LongTable(
        rendered,
        colWidths=list(widths),
        repeatRows=repeat_rows if header else 0,
        hAlign="LEFT",
    )
    commands: list[tuple] = [
        ("GRID", (0, 0), (-1, -1), 0.45, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY))
    for (row, column), fill in (highlights or {}).items():
        cell = (column, row)
        commands.append(("BACKGROUND", cell, cell, fill))
    table.setStyle(TableStyle(commands))
    return table


def image_flowable(path: Path, max_width: float, max_height: float) -> Image:
    if not path.exists():
        raise FileNotFoundError(path)
    with PILImage.open(path) as source_image:
        width, height = source_image.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def image_pair(
    left: tuple[Path, str],
    right: tuple[Path, str],
    styles: dict[str, ParagraphStyle],
    *,
    max_height: float = 2.65 * inch,
) -> Table:
    cell_width = CONTENT_WIDTH / 2 - 0.08 * inch
    rows = [
        [
            image_flowable(left[0], cell_width - 0.12 * inch, max_height),
            image_flowable(right[0], cell_width - 0.12 * inch, max_height),
        ],
        [paragraph(left[1], styles["caption"]), paragraph(right[1], styles["caption"])],
    ]
    table = Table(rows, colWidths=[cell_width, cell_width], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.45, MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.45, MID_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def add_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("APArial", 7.5)
    canvas.setFillColor(DARK_GRAY)
    canvas.drawString(LEFT_MARGIN, 0.34 * inch, "ГК «АП-Риал» | Итоговый отчёт")
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 0.34 * inch, f"Страница {doc.page}")
    canvas.restoreState()


def add_heading(story: list[object], text: str, styles: dict[str, ParagraphStyle], level: int = 1) -> None:
    story.append(paragraph(text, styles["h1" if level == 1 else "h2"]))


def add_callout(story: list[object], text: str, styles: dict[str, ParagraphStyle]) -> None:
    table = Table([[paragraph(text, styles["callout"])]], colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_GREEN),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#A7D5B7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([table, Spacer(1, 8)])


def included_domain_rows() -> list[list[str]]:
    midpoint = len(source.evidence.INCLUDED_DOMAINS) // 2
    rows = [["Сайт", "Статус", "Сайт", "Статус"]]
    for left, right in zip(
        source.evidence.INCLUDED_DOMAINS[:midpoint],
        source.evidence.INCLUDED_DOMAINS[midpoint:],
    ):
        rows.append([left, "Готово", right, "Готово"])
    return rows


def migration_live_rows() -> list[list[str]]:
    midpoint = (len(source.MIGRATIONS_LIVE) + 1) // 2
    left = source.MIGRATIONS_LIVE[:midpoint]
    right = source.MIGRATIONS_LIVE[midpoint:]
    rows = [["Сайт", "Результат", "Сайт", "Результат"]]
    for index in range(midpoint):
        right_domain = right[index] if index < len(right) else ""
        rows.append(
            [
                left[index],
                "Перенесён и открывается",
                right_domain,
                "Перенесён и открывается" if right_domain else "",
            ]
        )
    return rows


def build_report_pdf() -> dict[str, object]:
    styles = make_styles()
    result_index = source.load_result_index()
    delivery_index = source.load_delivery_index()
    checks = source.validate_inputs(result_index, delivery_index)

    boards = {
        domain: source.ASSET_DIR / f"{domain}-forms.png"
        for domain in source.evidence.INCLUDED_DOMAINS
    }
    sheets = sorted(source.ASSET_DIR.glob("migration-sheet-*.png"))
    if len(sheets) != 8:
        raise ValueError(f"Expected 8 migration evidence sheets, got {len(sheets)}")

    source.OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(source.OUTPUT_PDF),
        pagesize=LETTER,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Итоговый отчёт о работах по сайтам ГК «АП-Риал»",
        author="Никита Тихомиров",
        subject="Перенос, формы, маршрутизация заявок и последующие исправления",
        creator="Никита Тихомиров",
    )
    story: list[object] = []

    story.append(paragraph("ИТОГОВЫЙ ОТЧЁТ", styles["title_kicker"]))
    story.append(paragraph("Работы по сайтам ГК «АП-Риал»", styles["title"]))
    story.append(
        paragraph(
            "Перенос сайтов, формы обратной связи, маршрутизация заявок и последующие исправления",
            styles["subtitle"],
        )
    )
    metadata = [
        ["Заказчик", "Группа компаний «АП-Риал»"],
        ["Исполнитель", "Никита Тихомиров"],
        ["Дата", "2 августа 2026 года"],
        ["Проверка", "Повторная сверка исходных поручений и опубликованных версий"],
    ]
    story.append(styled_table(metadata, [1.35 * inch, CONTENT_WIDTH - 1.35 * inch], styles, header=False))
    story.append(Spacer(1, 12))
    add_heading(story, "Краткий итог", styles, 2)
    metrics = [
        [
            paragraph("30", styles["metric"]),
            paragraph("60 из 60", styles["metric"]),
            paragraph("48 из 48", styles["metric"]),
            paragraph("28", styles["metric"]),
        ],
        [
            paragraph("сайтов с формами", styles["metric_label"]),
            paragraph("заявок приняты", styles["metric_label"]),
            paragraph("маршрутов верны", styles["metric_label"]),
            paragraph("рабочих переносов", styles["metric_label"]),
        ],
    ]
    metric_table = Table(metrics, colWidths=[CONTENT_WIDTH / 4] * 4)
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, MID_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([metric_table, Spacer(1, 12)])
    story.append(
        paragraph(
            "Все требования к формам на 30 включённых сайтах выполнены и повторно проверены после "
            "публикации. По переносу 28 прямо порученных сайтов работают с перенесёнными версиями. "
            "Один доступный источник оказался стандартной страницей хостинга. Остальные открытые "
            "позиции ниже отделены от выполненных и не выданы за завершённые.",
            styles["body"],
        )
    )
    add_callout(
        story,
        "Повторно составлять список замечаний не требуется: исходные поручения восстановлены и сверены заново.",
        styles,
    )

    story.append(PageBreak())
    add_heading(story, "1. Формы обратной связи", styles)
    story.append(
        paragraph(
            "На 30 сайтах выполнена единая доработка двух форм. Внешний вид и работа обеих форм "
            "проверены на каждом сайте; все контрольные заявки приняты обработчиками. Получатели "
            "сверены отдельно по полной матрице маршрутов.",
            styles["body"],
        )
    )
    form_rows: list[list[object]] = [["Что требовалось", "Что сделано", "Статус"]]
    form_rows.extend([[title, detail, "Готово"] for title, detail in source.FORM_REQUIREMENTS])
    form_highlights = {(row, 2): PALE_GREEN for row in range(1, len(form_rows))}
    story.append(
        styled_table(
            form_rows,
            [1.35 * inch, 4.65 * inch, 0.78 * inch],
            styles,
            highlights=form_highlights,
        )
    )
    add_heading(story, "Сайты, входившие в доработку", styles, 2)
    story.append(
        styled_table(
            included_domain_rows(),
            [2.18 * inch, 1.18 * inch, 2.18 * inch, 1.18 * inch],
            styles,
        )
    )
    story.append(PageBreak())
    add_heading(story, "Сайты, где формы не требовались", styles, 2)
    excluded_rows = [["Сайт", "Статус"]] + [
        [domain, "Формы исключены из согласованного объёма"]
        for domain in source.evidence.EXCLUDED_DOMAINS
    ]
    story.append(styled_table(excluded_rows, [2.1 * inch, 4.7 * inch], styles))

    story.append(PageBreak())
    add_heading(story, "2. Отправка и маршрутизация заявок", styles)
    story.append(
        paragraph(
            "Проведены 60 контрольных отправок: две формы на каждом из 30 сайтов. Все 60 обработчиков "
            "приняли заявки. Отдельная проверка 48 актуальных и дополнительных конфигураций показала, "
            "что каждая форма направляет письмо на адрес из клиентской матрицы. Фактическое получение "
            "обеих форм в почте отдельно подтверждено для medlic.spb.ru.",
            styles["body"],
        )
    )
    story.append(
        styled_table(
            [
                [image_flowable(source.MAILBOX_RECEIPT_SCREENSHOT, CONTENT_WIDTH - 0.2 * inch, 3.2 * inch)],
                [
                    paragraph(
                        "В доступном ящике info@medlic.spb.ru подтверждены письма от обеих форм сайта medlic.spb.ru.",
                        styles["caption"],
                    )
                ],
            ],
            [CONTENT_WIDTH],
            styles,
            header=False,
            repeat_rows=0,
        )
    )
    add_callout(
        story,
        "Для остальных сайтов подтверждены принятие заявки обработчиком и правильный адрес получателя "
        "в конфигурации. Получение письма непосредственно в каждом закрытом клиентском ящике без "
        "доступа к этому ящику в отчёте не заявляется.",
        styles,
    )

    story.append(PageBreak())
    add_heading(story, "3. Перенос сайтов на Beget", styles)
    story.append(
        paragraph(
            "Исходное поручение охватывало 35 доменов. Статусы разделены: рабочий перенос, доступная "
            "заглушка, подготовленная версия без домена, отсутствующий источник и решение по объёму.",
            styles["body"],
        )
    )
    add_callout(
        story,
        "28 прямо порученных сайтов работают с перенесёнными версиями. Дополнительно перенесён 39mchs.ru.",
        styles,
    )
    add_heading(story, "Работающие перенесённые версии", styles, 2)
    story.append(
        styled_table(
            migration_live_rows(),
            [1.82 * inch, 1.58 * inch, 1.82 * inch, 1.58 * inch],
            styles,
        )
    )
    add_heading(story, "Особые позиции", styles, 2)
    special_rows = [
        ["Объект", "Фактическое состояние", "Статус"],
        ["othodi-spb.ru", "Перенесён весь доступный источник, но он является стандартной страницей хостинга.", "Нужен реальный источник"],
        ["mchs-vrn.ru", "Полная версия размещена на Beget и проверена на компьютере и телефоне.", "Нужны домен и DNS"],
        ["dpocenter.ru", "Рабочий сайт остаётся на Sprinthost; исходников и доступа нет.", "Нужен доступ"],
        ["feo-edem.ru", "Есть база данных, но нет домена и файлов сайта.", "Нужны домен и файлы"],
        ["linkedin.com.moopb.ru", "В источнике только служебная заглушка, архивной копии нет.", "Нужно решение и источник"],
        ["aklab-spb.ru", "Нет домена, файлов проекта и доступа к прежнему источнику.", "Нужны домен и источник"],
        ["elektro.spb.ru", "В исходном перечне был, позже локально помечен как ненужный без подтверждения клиента.", "Нужно решение по объёму"],
        ["39mchs.ru", "Перенесён дополнительно и работает.", "Готово"],
    ]
    special_highlights = {(row, 2): PALE_AMBER for row in range(1, len(special_rows) - 1)}
    special_highlights[(len(special_rows) - 1, 2)] = PALE_GREEN
    story.append(
        styled_table(
            special_rows,
            [1.45 * inch, 3.85 * inch, 1.5 * inch],
            styles,
            highlights=special_highlights,
        )
    )

    story.append(PageBreak())
    add_heading(story, "4. Дополнительные исправления", styles)
    additional_rows = [["Сайт", "Работа", "Фактический результат"]]
    additional_rows.extend([list(item) for item in source.ADDITIONAL_WORK])
    story.append(
        styled_table(
            additional_rows,
            [1.65 * inch, 1.65 * inch, 3.5 * inch],
            styles,
        )
    )
    add_heading(story, "Скрытый фоновый видеоэлемент и существующая камера", styles, 2)
    story.append(
        paragraph(
            "Фоновый видеоэлемент на nousro.ru и nousro-nn.ru не входил в поручение. Он временно появился "
            "при устранении JavaScript-ошибок, после чего был повторно проверен и скрыт на обоих сайтах. "
            "Дополнительное решение заказчика по этому элементу не требуется.",
            styles["body"],
        )
    )
    story.append(
        paragraph(
            "Блок Ivideon - отдельный ранее существовавший элемент. Он не изменялся и сейчас показывает "
            "ошибку подключения к камере. Для восстановления нужен актуальный доступ или идентификатор "
            "камеры; без него блок можно только скрыть после согласования.",
            styles["body"],
        )
    )
    story.append(
        image_pair(
            (
                source.POST_CORRECTION_QA_DIR / "nousro.ru-desktop-page.png",
                "nousro.ru после исправления: фоновый видеоэлемент скрыт.",
            ),
            (
                source.POST_CORRECTION_QA_DIR / "nousro-nn.ru-desktop-page.png",
                "nousro-nn.ru после исправления: фоновый видеоэлемент скрыт.",
            ),
            styles,
            max_height=2.2 * inch,
        )
    )
    story.append(PageBreak())
    add_heading(story, "Существующий блок Ivideon", styles, 2)
    story.append(
        image_pair(
            (
                source.VIDEO_QA_DIR / "nousro.ru-existing-ivideon-block.png",
                "Существующий блок Ivideon: камера сейчас недоступна.",
            ),
            (
                source.VIDEO_QA_DIR / "nousro-nn.ru-existing-ivideon-block.png",
                "На втором сайте тот же отдельный блок камеры.",
            ),
            styles,
            max_height=2.2 * inch,
        )
    )

    story.append(PageBreak())
    add_heading(story, "5. Что требуется от заказчика", styles)
    story.append(
        paragraph(
            "Ниже перечислены только отсутствующие домены, исходники, доступы или решения. Работы, "
            "которые можно было завершить без участия заказчика, в этот список не включены.",
            styles["body"],
        )
    )
    client_rows: list[list[object]] = [["Объект", "Фактическое состояние", "Что именно нужно"]]
    client_rows.extend([list(item) for item in source.CLIENT_INPUT_REQUIRED])
    client_highlights = {(row, 2): PALE_AMBER for row in range(1, len(client_rows))}
    story.append(
        styled_table(
            client_rows,
            [1.45 * inch, 2.75 * inch, 2.6 * inch],
            styles,
            highlights=client_highlights,
        )
    )
    story.append(Spacer(1, 9))
    add_callout(
        story,
        "Все остальные перечисленные в исходных поручениях исправления выполнены. Открытые позиции выше не выданы за завершённые.",
        styles,
    )

    story.append(PageBreak())
    add_heading(story, "6. Примеры отдельных исправлений", styles)
    evidence_pairs = [
        (
            (
                source.MAIL_EVIDENCE_DIR / "medlic.spb.ru-slider-desktop.png",
                "medlic.spb.ru: опубликованная версия на компьютере.",
            ),
            (
                source.MAIL_EVIDENCE_DIR / "medlic.spb.ru-slider-mobile.png",
                "medlic.spb.ru: та же версия на телефоне.",
            ),
        ),
        (
            (
                source.MIGRATION_QA_DIR / "mchs-vrn.ru-desktop-staged.png",
                "mchs-vrn.ru: версия на Beget до подключения домена.",
            ),
            (
                source.MIGRATION_QA_DIR / "mchs-vrn.ru-mobile-staged.png",
                "mchs-vrn.ru: исправленная мобильная версия.",
            ),
        ),
        (
            (
                source.MIGRATION_QA_DIR / "ohrana-truda.nousro.ru-desktop-final-acceptance.png",
                "ohrana-truda.nousro.ru: восстановленная desktop-версия.",
            ),
            (
                source.MIGRATION_QA_DIR / "ohrana-truda.nousro.ru-mobile-final-acceptance.png",
                "ohrana-truda.nousro.ru: восстановленная mobile-версия.",
            ),
        ),
    ]
    for index, pair in enumerate(evidence_pairs):
        story.append(image_pair(pair[0], pair[1], styles, max_height=2.55 * inch))
        if index != len(evidence_pairs) - 1:
            story.append(Spacer(1, 7))

    story.append(PageBreak())
    add_heading(story, "Приложение А. Проверка форм на 30 сайтах", styles)
    story.append(
        paragraph(
            "Для каждого сайта приведены четыре свежих снимка: страница и открытая форма на компьютере, "
            "страница и открытая форма на телефоне. Полные исходные снимки сохранены в машинном аудите.",
            styles["body"],
        )
    )
    for index, domain in enumerate(source.evidence.INCLUDED_DOMAINS, start=1):
        if index > 1:
            story.append(PageBreak())
        add_heading(story, f"А.{index}. {domain}", styles, 2)
        story.append(image_flowable(boards[domain], CONTENT_WIDTH, 5.1 * inch))
        story.append(Spacer(1, 5))
        story.append(
            paragraph(
                "Проверено: страница открывается, обе формы доступны, поля и подписи соответствуют "
                "согласованной схеме, элементы не выходят за экран на desktop/mobile.",
                styles["small"],
            )
        )

    story.append(PageBreak())
    add_heading(story, "Приложение Б. Визуальная проверка переноса", styles)
    story.append(
        paragraph(
            "Ниже приведены свежие desktop/mobile-снимки выборки перенесённых сайтов и отдельная "
            "маркировка служебной страницы othodi-spb.ru.",
            styles["body"],
        )
    )
    for index, sheet in enumerate(sheets, start=1):
        if index > 1:
            story.append(PageBreak())
        add_heading(story, f"Б.{index}. Лист визуальной проверки", styles, 2)
        story.append(image_flowable(sheet, CONTENT_WIDTH, 6.7 * inch))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    reader = PdfReader(str(source.OUTPUT_PDF))
    return {
        "path": str(source.OUTPUT_PDF.relative_to(ROOT)),
        "pages": len(reader.pages),
        "bytes": source.OUTPUT_PDF.stat().st_size,
        "checks": checks,
    }


def build_cover_pdf() -> dict[str, object]:
    styles = make_styles()
    source.COVER_NOTE_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(source.COVER_NOTE_PDF),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
        title="Сопроводительное письмо к итоговому отчёту ГК «АП-Риал»",
        author="Никита Тихомиров",
        creator="Никита Тихомиров",
    )
    paragraphs = [
        "Альберт, добрый день.",
        (
            "По итогам вашей обратной связи я полностью пересобрал контроль работ по сайтам. Ранее я "
            "преждевременно подтвердил завершение части многосайтовых задач: автоматические проверки "
            "показывали доступность отдельных страниц и сценариев, но мой процесс не требовал отдельного "
            "подтверждения каждого пункта на каждом сайте. Из-за этого часть фактических несоответствий не "
            "попала в мой отчёт. Это моя ошибка в организации контроля."
        ),
        (
            "Повторно составлять список замечаний вам не требуется. Я заново сверил исходные поручения, "
            "проверил опубликованные версии на компьютере и телефоне, выполнил 60 контрольных отправок форм, "
            "сверил 48 настроек получателей с согласованной матрицей и отдельно подтвердил обе формы "
            "medlic.spb.ru в доступном ящике info@medlic.spb.ru. Найденные дефекты устранены."
        ),
        (
            "В приложенном отчёте простым языком указано, что выполнено и чем это подтверждено. Отдельно "
            "перечислены только позиции, для которых объективно нужен отсутствующий домен, исходник, доступ "
            "или ваше решение. Они не выданы за завершённые."
        ),
        (
            "После этого случая я изменил порядок приёмки: многосайтовая задача не считается выполненной, "
            "пока по каждому требованию и каждому сайту нет отдельной проверки и доказательства результата."
        ),
        "С уважением,\nНикита Тихомиров",
    ]
    story: list[object] = [
        paragraph("СОПРОВОДИТЕЛЬНОЕ ПИСЬМО", styles["title_kicker"]),
        paragraph("К итоговому отчёту по сайтам", styles["title"]),
        Spacer(1, 10),
    ]
    for text in paragraphs:
        story.append(paragraph(text, styles["body"]))
        story.append(Spacer(1, 5))
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    reader = PdfReader(str(source.COVER_NOTE_PDF))
    return {
        "path": str(source.COVER_NOTE_PDF.relative_to(ROOT)),
        "pages": len(reader.pages),
        "bytes": source.COVER_NOTE_PDF.stat().st_size,
    }


def main() -> None:
    result = {
        "report": build_report_pdf(),
        "cover_note": build_cover_pdf(),
        "client_contact_performed": False,
        "renderer": "reportlab",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
