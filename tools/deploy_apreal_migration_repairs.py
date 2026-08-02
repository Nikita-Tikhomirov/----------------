#!/usr/bin/env python3
"""Back up and publish the focused AP-Real migration-site repairs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re
import shlex
from typing import Callable

try:
    from tools.deploy_apreal_runtime_repairs import (
        REMOTE_HOME,
        connect,
        read_optional,
        remote_states,
        run_remote,
        state,
    )
except ModuleNotFoundError:
    from deploy_apreal_runtime_repairs import (  # type: ignore[no-redef]
        REMOTE_HOME,
        connect,
        read_optional,
        remote_states,
        run_remote,
        state,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-migration-repairs-snapshot-20260802"
OUTPUT = ROOT / "output/ap-real-migration-repairs-deploy-2026-08-02.json"
OHRANA_ROOT = REMOTE_HOME / "ohrana-truda.nousro.ru/public_html"
MOOPB_ROOT = REMOTE_HOME / "moopb.ru/public_html"
ELECTRO_ROOT = REMOTE_HOME / "electro-reg.ru/public_html"
RECTAVR_ROOT = REMOTE_HOME / "rectavr.ru/public_html"
MCHS_VRN_ROOT = REMOTE_HOME / "mchs-vrn.ru/public_html"
ICON_SOURCE = REMOTE_HOME / "nousro.ru/public_html/img/icon_folder.png"

ELECTRO_MOBILE_CSS = br"""

/* AP-REAL-ELECTRO-MOBILE-REPAIR: contain long slider and tariff labels. */
@media (max-width: 767px) {
  html,
  body {
    max-width: 100% !important;
    overflow-x: hidden !important;
  }

  #n2-ss-4item1 {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    font-size: 28px !important;
    line-height: 1.15 !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    text-align: center !important;
  }

  #n2-ss-4 .n2-ss-layer[data-desktopportraitmargin="10|*|10|*|10|*|10|*|px+"][data-cssselfalign="center"] {
    width: calc(100% - 1.25em) !important;
    max-width: calc(100% - 1.25em) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
  }

  ul.uk-tab.uk-tab-grid {
    display: flex !important;
    flex-direction: column !important;
    width: auto !important;
    max-width: 100% !important;
    margin-left: 0 !important;
  }

  ul.uk-tab.uk-tab-grid > li.uk-width-1-3 {
    width: 100% !important;
    max-width: 100% !important;
    padding-left: 0 !important;
  }

  ul.uk-tab.uk-tab-grid > li > a {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
  }
}
"""

MOOPB_MOBILE_CSS = br"""

/* AP-REAL-MOOPB-MOBILE-REPAIR: stack the legacy table layout on phones. */
@media (max-width: 767px) {
  html,
  body {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
  }

  body {
    margin: 0 !important;
    padding: 0 10px !important;
    box-sizing: border-box;
  }

  body table {
    width: 100% !important;
    max-width: 100% !important;
    table-layout: fixed !important;
    box-sizing: border-box;
  }

  body td {
    max-width: 100% !important;
    box-sizing: border-box;
    overflow-wrap: anywhere;
  }

  #he1 > table > tbody > tr:first-child {
    display: grid;
    grid-template-columns: 92px minmax(0, 1fr);
    align-items: center;
  }

  #he1 > table > tbody > tr:first-child > td {
    display: block;
    width: auto !important;
    min-width: 0;
  }

  #he1 > table > tbody > tr:first-child > td:nth-child(3) {
    grid-column: 1 / -1;
    padding: 8px 0 12px;
  }

  #he1 .logo {
    width: 86px !important;
    max-width: 100%;
  }

  .hed1,
  .hed2,
  .hed3,
  .hed4 {
    width: auto !important;
    max-width: 100% !important;
    box-sizing: border-box;
  }

  .hed1 {
    font-size: 22px !important;
  }

  .hed2 {
    font-size: 12px !important;
  }

  .hed3,
  .hed4 {
    text-align: center !important;
  }

  .foot6 {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: auto;
    white-space: nowrap;
    box-sizing: border-box;
  }

  .toparea_cat_menu {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: auto;
    box-sizing: border-box;
  }

  .toparea_cat_menu ul {
    display: flex !important;
    width: max-content !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 0 4px !important;
  }

  .toparea_cat_menu li {
    flex: 0 0 auto;
  }

  .toparea_cat_menu h2 {
    width: auto !important;
    max-width: none !important;
  }

  body > table > tbody > tr > td > table[width="1000"]
    > tbody > tr:nth-child(4) {
    display: flex;
    flex-direction: column;
    width: 100%;
  }

  body > table > tbody > tr > td > table[width="1000"]
    > tbody > tr:nth-child(4) > td {
    display: block;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
  }

  body > table > tbody > tr > td > table[width="1000"]
    > tbody > tr:nth-child(4) > td:nth-child(2) {
    order: 1;
  }

  body > table > tbody > tr > td > table[width="1000"]
    > tbody > tr:nth-child(4) > td:nth-child(1) {
    order: 2;
  }

  body > table > tbody > tr > td > table[width="1000"]
    > tbody > tr:nth-child(4) > td:nth-child(3) {
    order: 3;
  }

  img {
    max-width: 100%;
    height: auto;
  }

  .foot3,
  .foot4,
  .foot5 {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box;
  }
}
"""

OHRANA_MOBILE_CSS = br"""

/* AP-REAL-MOBILE-REPAIR: responsive layout for the restored legacy site. */
@media (max-width: 767px) {
  html,
  body {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
  }

  .inner {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: auto !important;
    box-sizing: border-box;
    padding-left: 12px;
    padding-right: 12px;
  }

  .header {
    width: 100% !important;
    height: auto !important;
    min-height: 60px;
    margin-bottom: 16px;
  }

  .header > .inner {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }

  .header .logo {
    width: 78px;
    height: auto;
  }

  .header p {
    width: calc(100% - 90px) !important;
    margin: 6px 0 !important;
    top: 0;
    font-size: 10px;
    line-height: 1.25;
  }

  .header .menu {
    width: 100% !important;
    height: auto !important;
    overflow-x: auto;
  }

  .header ul {
    float: none !important;
    display: flex;
    width: max-content !important;
    margin: 0 !important;
    padding: 0 0 8px !important;
  }

  .header li {
    flex: 0 0 auto;
    padding: 0 10px !important;
  }

  body > .inner {
    display: block;
  }

  .left_block,
  .right_block {
    width: 100% !important;
    float: none !important;
    margin: 0 !important;
  }

  .choose_study {
    width: 100% !important;
    height: auto !important;
    box-sizing: border-box;
    padding: 10px !important;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .choose_study .noh1 {
    width: 100% !important;
    text-align: center;
  }

  .choose_study .choose_btn {
    width: calc(50% - 4px) !important;
    margin: 0 !important;
  }

  .och-dist_left_block_content,
  .left_block_content {
    width: 100% !important;
    box-sizing: border-box;
    padding: 18px 14px !important;
  }

  .och-dist_left_block_content h1,
  .left_block_content h1 {
    font-size: 27px !important;
    line-height: 1.18 !important;
    overflow-wrap: anywhere;
  }

  .och-dist_left_block_content table,
  .left_block_content table {
    width: 100% !important;
    table-layout: fixed;
  }

  .och-dist_left_block_content img,
  .left_block_content img {
    max-width: 100% !important;
    height: auto !important;
  }

  .lifted {
    width: 100% !important;
    box-sizing: border-box;
  }

  .right_block {
    margin-top: 28px !important;
  }

  .right_block > a:first-child {
    display: block;
    width: 100% !important;
  }

  .right_block > a:first-child h2 {
    width: calc(100% - 72px) !important;
    font-size: 20px !important;
  }

  .right_block1,
  .right_block2,
  .right_block3 {
    width: 100% !important;
    box-sizing: border-box;
  }

  .right_block1 > a,
  .right_block1_ul1,
  .right_block1_ul2 {
    width: 50% !important;
    box-sizing: border-box;
  }

  .right_block3 {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    height: auto !important;
    padding: 12px !important;
  }

  .right_block3 .kursi_btn1,
  .right_block3 .kursi_btn2 {
    width: calc(50% - 4px) !important;
    box-sizing: border-box;
    margin: 0 !important;
  }

  .right_block3 > img {
    display: none;
  }

  .right_block4,
  .right_block5,
  .right_block6,
  .right_block7 {
    width: calc(50% - 8px) !important;
    margin: 16px 4px 0 !important;
    box-sizing: border-box;
  }

  .right_block4 a,
  .right_block5 a,
  .right_block6 a,
  .right_block7 a,
  .right_block5 img,
  .right_block6 img {
    max-width: 100% !important;
  }

  .footer_och-dist,
  .footer {
    width: 100% !important;
    height: auto !important;
    top: 0 !important;
    margin-top: 32px;
    padding: 24px 0 !important;
  }

  .footer_och-dist > .inner,
  .footer > .inner {
    display: flex;
    flex-wrap: wrap;
  }

  .footer_items {
    width: 50% !important;
    float: none !important;
    box-sizing: border-box;
    margin: 0 0 20px !important;
    padding-right: 12px;
  }
}
"""

RECTAVR_MOBILE_CSS_V1 = br"""

/* AP-REAL-RECTAVR-MOBILE-REPAIR: contain the fixed-width branding row. */
@media (max-width: 767px) {
  .site-branding .container {
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: flex-start;
    max-width: 100% !important;
  }

  .site-branding .container > div:first-child {
    flex: 0 0 70px;
  }

  .site-branding .left-brand {
    flex: 1 1 240px;
    width: auto !important;
    min-width: 0 !important;
    max-width: 100% !important;
    float: none !important;
    box-sizing: border-box;
  }

  .site-branding .container > div:nth-of-type(3) {
    flex: 1 1 260px;
    float: none !important;
    box-sizing: border-box;
  }
}
"""

RECTAVR_MOBILE_CSS_V2 = RECTAVR_MOBILE_CSS_V1.replace(
    b"AP-REAL-RECTAVR-MOBILE-REPAIR:",
    b"AP-REAL-RECTAVR-MOBILE-REPAIR-V2:",
).replace(
    b"  .site-branding .container > div:nth-of-type(3) {",
    b"  .site-title-centered .site-title {\n"
    b"    width: 100% !important;\n"
    b"    max-width: 100% !important;\n"
    b"    overflow-wrap: anywhere;\n"
    b"  }\n\n"
    b"  .site-branding .container > div:nth-of-type(3) {",
)

RECTAVR_MOBILE_CSS = RECTAVR_MOBILE_CSS_V2.replace(
    b"AP-REAL-RECTAVR-MOBILE-REPAIR-V2:",
    b"AP-REAL-RECTAVR-MOBILE-REPAIR-V3:",
).replace(
    b"    display: flex !important;\n"
    b"    flex-wrap: wrap !important;\n"
    b"    align-items: flex-start;",
    b"    display: block !important;",
).replace(
    b"    flex: 0 0 70px;",
    b"    width: 100%;\n"
    b"    float: none !important;\n"
    b"    text-align: center;",
).replace(
    b"    flex: 1 1 240px;\n    width: auto !important;",
    b"    width: 100% !important;",
).replace(
    b"    flex: 1 1 260px;",
    b"    width: 100% !important;",
)

MCHS_VRN_MOBILE_CSS_V1 = br"""

/* AP-REAL-MCHS-VRN-MOBILE-REPAIR: keep the staged banner inside phones. */
@media (max-width: 767px) {
  html,
  body {
    max-width: 100% !important;
    overflow-x: hidden !important;
  }

  .top-banner {
    overflow: hidden;
    padding: 70px 0;
  }

  .top-banner .container,
  .top-banner .row,
  .top-banner [class*="col-"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box;
  }

  .section-banner__title {
    width: auto !important;
    max-width: 100% !important;
    margin-bottom: 28px;
    font-size: 38px;
    line-height: 1.15;
    overflow-wrap: anywhere;
  }

  .section-banner__text {
    width: auto !important;
    max-width: 100% !important;
    overflow-wrap: anywhere;
  }
}
"""

MCHS_VRN_MOBILE_CSS = MCHS_VRN_MOBILE_CSS_V1.replace(
    b"AP-REAL-MCHS-VRN-MOBILE-REPAIR:",
    b"AP-REAL-MCHS-VRN-MOBILE-REPAIR-V2:",
).replace(
    b"    font-size: 38px;\n"
    b"    line-height: 1.15;\n"
    b"    overflow-wrap: anywhere;",
    b"    font-size: 32px;\n"
    b"    line-height: 1.15;\n"
    b"    overflow-wrap: normal;\n"
    b"    word-break: normal;",
    1,
)


Transform = Callable[[bytes], bytes]


@dataclass(frozen=True)
class RepairTarget:
    domain: str
    destination: PurePosixPath
    transform: Transform | None = None
    source: PurePosixPath | None = None


def replace_required(data: bytes, old: bytes, new: bytes, label: str) -> bytes:
    if new in data and old not in data:
        return data
    if old not in data:
        raise RuntimeError(f"Expected {label} marker was not found")
    return data.replace(old, new)


def repair_moopb_htaccess(data: bytes) -> bytes:
    return replace_required(
        data,
        b"http://www.moopb.ru/$1",
        b"https://www.moopb.ru/$1",
        "moopb HTTPS redirect",
    )


def repair_electro_reg_style(data: bytes) -> bytes:
    if b"AP-REAL-ELECTRO-MOBILE-REPAIR" in data:
        return data
    return data.rstrip() + ELECTRO_MOBILE_CSS


def repair_electro_reg_config(data: bytes) -> bytes:
    return replace_required(
        data,
        b"$this['asset']->addFile('css', 'css:custom.css');",
        b"$this['asset']->addFile('css', get_template_directory_uri() "
        b". '/css/custom.css?v=20260802');",
        "electro-reg custom CSS cache version",
    )


def repair_moopb_style(data: bytes) -> bytes:
    if b"AP-REAL-MOOPB-MOBILE-REPAIR" in data:
        return data
    return data.rstrip() + MOOPB_MOBILE_CSS


def repair_ohrana_slider(data: bytes) -> bytes:
    marker = b" var slider = document.getElementById(target);"
    guard = marker + b"\n if (!slider) {\n  return;\n }"
    if guard in data:
        return data
    return replace_required(data, marker, guard, "ohrana slider")


def repair_ohrana_fonts(data: bytes) -> bytes:
    repaired, count = re.subn(
        rb"url\(http://fonts\.gstatic\.com/[^)]+\.woff\)",
        b"url(../fonts/PTS55F-webfont.woff)",
        data,
    )
    if count:
        return repaired
    if b"url(../fonts/PTS55F-webfont.woff)" in data:
        return data
    raise RuntimeError("Expected ohrana font URL was not found")


def repair_ohrana_style(data: bytes) -> bytes:
    repaired = replace_required(
        data,
        b"https://nousro.ru/bitrix/templates/content/img/icon_folder.png",
        b"../images/icon_folder.png",
        "ohrana folder icon",
    )
    if b"AP-REAL-MOBILE-REPAIR" not in repaired:
        repaired = repaired.rstrip() + OHRANA_MOBILE_CSS
    return repaired


def repair_rectavr_style(data: bytes) -> bytes:
    if b"AP-REAL-RECTAVR-MOBILE-REPAIR-V3" in data:
        return data
    if b"AP-REAL-RECTAVR-MOBILE-REPAIR-V2" in data:
        if RECTAVR_MOBILE_CSS_V2 not in data:
            raise RuntimeError("Existing rectavr mobile repair differs from v2")
        return data.replace(RECTAVR_MOBILE_CSS_V2, RECTAVR_MOBILE_CSS)
    if b"AP-REAL-RECTAVR-MOBILE-REPAIR:" in data:
        if RECTAVR_MOBILE_CSS_V1 not in data:
            raise RuntimeError("Existing rectavr mobile repair differs from v1")
        return data.replace(RECTAVR_MOBILE_CSS_V1, RECTAVR_MOBILE_CSS)
    return data.rstrip() + RECTAVR_MOBILE_CSS


def repair_mchs_vrn_style(data: bytes) -> bytes:
    if b"AP-REAL-MCHS-VRN-MOBILE-REPAIR-V2" in data:
        return data
    if b"AP-REAL-MCHS-VRN-MOBILE-REPAIR:" in data:
        if MCHS_VRN_MOBILE_CSS_V1 not in data:
            raise RuntimeError("Existing mchs-vrn mobile repair differs from v1")
        return data.replace(MCHS_VRN_MOBILE_CSS_V1, MCHS_VRN_MOBILE_CSS)
    return data.rstrip() + MCHS_VRN_MOBILE_CSS


def repair_ohrana_html(data: bytes) -> bytes:
    repaired = data.replace(
        b"http://counter.rambler.ru", b"https://counter.rambler.ru"
    ).replace(b"http://top100.rambler.ru", b"https://top100.rambler.ru")
    if not (
        b"https://counter.rambler.ru" in repaired
        and b"https://top100.rambler.ru" in repaired
    ):
        raise RuntimeError("Expected Rambler counter URLs were not found")

    wrong_main = (
        b'<script type="text/javascript" src="scripts/jquery_003.js"></script>'
    )
    right_main = (
        b'<script type="text/javascript" src="scripts/jquery_002.js"></script>'
    )
    wrong_carousel = (
        b'<script src="scripts/jquery_002.js" type="text/javascript"></script>'
    )
    right_carousel = (
        b'<script src="scripts/jquery_003.js" type="text/javascript"></script>'
    )
    if wrong_main in repaired:
        if wrong_carousel not in repaired:
            raise RuntimeError("Expected swapped Fancybox carousel script was not found")
        repaired = repaired.replace(wrong_main, right_main, 1)
        repaired = repaired.replace(wrong_carousel, right_carousel, 1)

    highslide_block = re.compile(
        rb"\s*<script[^>]+src=\"[^\"]*highslide/highslide\.js\""
        rb"[^>]*></script>\s*<script[^>]*>.*?"
        rb"hs\.graphicsDir\s*=.*?</script>",
        re.DOTALL,
    )
    repaired = highslide_block.sub(b"\n", repaired)
    repaired = re.sub(
        rb"\s+onclick=\"return hs\.expand\(this\)\"",
        b' target="_blank" rel="noopener"',
        repaired,
    )
    repaired = re.sub(
        rb"\s*<!-- Yandex\.Metrika informer -->.*?"
        rb"<!-- /Yandex\.Metrika informer -->",
        b"\n",
        repaired,
        flags=re.DOTALL,
    )
    return repaired


def remote_targets() -> tuple[RepairTarget, ...]:
    html_pages = (
        "attestacija-rabochih-mest.html",
        "bazovyj-kurs.html",
        "index.html",
        "ohrana-truda.html",
        "ohrana-tryda-na-vusote.html",
        "outsourcing-ohrana-truda.html",
        "pk-ohrana-truda.html",
        "Pomosh_neschastnii_sluchai.html",
        "proverka-ohrana-truda.html",
        "sitemap.html",
    )
    return (
        RepairTarget(
            "electro-reg.ru",
            ELECTRO_ROOT / "wp-content/themes/yoo_finch_wp/css/custom.css",
            repair_electro_reg_style,
        ),
        RepairTarget(
            "electro-reg.ru",
            ELECTRO_ROOT / "wp-content/themes/yoo_finch_wp/layouts/theme.config.php",
            repair_electro_reg_config,
        ),
        RepairTarget("moopb.ru", MOOPB_ROOT / ".htaccess", repair_moopb_htaccess),
        RepairTarget(
            "moopb.ru",
            MOOPB_ROOT / "ssi/right.php",
            repair_ohrana_html,
        ),
        RepairTarget("moopb.ru", MOOPB_ROOT / "style.css", repair_moopb_style),
        RepairTarget(
            "rectavr.ru",
            RECTAVR_ROOT / "wp-content/themes/miteri/style.css",
            repair_rectavr_style,
        ),
        RepairTarget(
            "mchs-vrn.ru",
            MCHS_VRN_ROOT / "wp-content/themes/license-center/css/style.css",
            repair_mchs_vrn_style,
        ),
        RepairTarget(
            "ohrana-truda.nousro.ru",
            OHRANA_ROOT / "scripts/slider1.js",
            repair_ohrana_slider,
        ),
        RepairTarget(
            "ohrana-truda.nousro.ru",
            OHRANA_ROOT / "css/css.css",
            repair_ohrana_fonts,
        ),
        RepairTarget(
            "ohrana-truda.nousro.ru",
            OHRANA_ROOT / "css/style.css",
            repair_ohrana_style,
        ),
        *(
            RepairTarget(
                "ohrana-truda.nousro.ru",
                OHRANA_ROOT / page,
                repair_ohrana_html,
            )
            for page in html_pages
        ),
        RepairTarget(
            "ohrana-truda.nousro.ru",
            OHRANA_ROOT / "images/icon_folder.png",
            source=ICON_SOURCE,
        ),
    )


def snapshot_path(snapshot_root: Path, remote: PurePosixPath) -> Path:
    return snapshot_root / Path(str(remote.relative_to(REMOTE_HOME)))


def take_snapshot(ssh, sftp, snapshot_root: Path) -> dict[str, object]:
    targets = remote_targets()
    probe_paths = {str(item.destination) for item in targets}
    probe_paths.add(str(ICON_SOURCE))
    states = remote_states(ssh, sorted(probe_paths))
    if not states[str(ICON_SOURCE)]["exists"]:
        raise RuntimeError(f"Missing icon recovery source: {ICON_SOURCE}")

    manifest: dict[str, object] = {
        "source": {str(ICON_SOURCE): states[str(ICON_SOURCE)]},
        "destinations": {},
    }
    for item in targets:
        current = states[str(item.destination)]
        manifest["destinations"][str(item.destination)] = {
            "domain": item.domain,
            **current,
        }
        if item.transform is None:
            continue
        if not current["exists"]:
            raise RuntimeError(f"Missing repair target: {item.destination}")
        data = read_optional(sftp, item.destination)
        if state(data) != current:
            raise RuntimeError(f"Target changed during snapshot: {item.destination}")
        local = snapshot_path(snapshot_root, item.destination)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)

    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def desired_payloads(snapshot_root: Path) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for item in remote_targets():
        if item.transform is None:
            payloads.append(
                {
                    "target": item,
                    "data": None,
                    "desired": None,
                }
            )
            continue
        original = snapshot_path(snapshot_root, item.destination).read_bytes()
        repaired = item.transform(original)
        payloads.append(
            {
                "target": item,
                "data": repaired,
                "desired": state(repaired),
            }
        )
    return payloads


def compact_state(value: dict[str, object]) -> dict[str, object]:
    return {key: value[key] for key in ("exists", "size", "sha256")}


def deploy(ssh, sftp, snapshot_root: Path) -> dict[str, object]:
    manifest_path = snapshot_root / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Snapshot manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payloads = desired_payloads(snapshot_root)
    source_state = manifest["source"][str(ICON_SOURCE)]
    for payload in payloads:
        target: RepairTarget = payload["target"]
        if target.source is not None:
            payload["desired"] = compact_state(source_state)

    probe_paths = {str(payload["target"].destination) for payload in payloads}
    probe_paths.add(str(ICON_SOURCE))
    live = remote_states(ssh, sorted(probe_paths))
    if live[str(ICON_SOURCE)] != compact_state(source_state):
        raise RuntimeError(f"Icon source changed: {ICON_SOURCE}")

    changed: list[dict[str, object]] = []
    for payload in payloads:
        target: RepairTarget = payload["target"]
        expected = compact_state(manifest["destinations"][str(target.destination)])
        if live[str(target.destination)] != expected:
            raise RuntimeError(f"Live target changed: {target.destination}")
        if live[str(target.destination)] != payload["desired"]:
            changed.append(payload)

    if not changed:
        return {"backup_root": None, "published": [], "skipped": len(payloads)}

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-ap-real-migration-repairs"
    run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}", timeout=30)
    staged: list[dict[str, object]] = []
    published: list[RepairTarget] = []
    try:
        for payload in changed:
            target: RepairTarget = payload["target"]
            temporary = PurePosixPath(f"{target.destination}.codex-{stamp}")
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(target.destination.parent))}",
                timeout=30,
            )
            if payload["data"] is not None:
                with sftp.open(str(temporary), "wb") as handle:
                    handle.write(payload["data"])
                sftp.chmod(str(temporary), 0o644)
            else:
                run_remote(
                    ssh,
                    f"cp {shlex.quote(str(target.source))} "
                    f"{shlex.quote(str(temporary))} && chmod 644 "
                    f"{shlex.quote(str(temporary))}",
                    timeout=30,
                )
            staged_state = remote_states(ssh, [str(temporary)])[str(temporary)]
            if staged_state != payload["desired"]:
                raise RuntimeError(f"Staged upload mismatch: {target.destination}")
            staged.append({**payload, "temporary": temporary})

        for payload in staged:
            target: RepairTarget = payload["target"]
            expected = manifest["destinations"][str(target.destination)]
            if not expected["exists"]:
                continue
            backup = backup_root / target.destination.relative_to(REMOTE_HOME)
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(target.destination))} "
                f"{shlex.quote(str(backup))}",
                timeout=30,
            )

        for payload in staged:
            target: RepairTarget = payload["target"]
            temporary: PurePosixPath = payload["temporary"]
            run_remote(
                ssh,
                f"mv -f {shlex.quote(str(temporary))} "
                f"{shlex.quote(str(target.destination))}",
                timeout=30,
            )
            published_state = remote_states(ssh, [str(target.destination)])[
                str(target.destination)
            ]
            if published_state != payload["desired"]:
                raise RuntimeError(f"Published file mismatch: {target.destination}")
            published.append(target)

        return {
            "backup_root": str(backup_root),
            "published": [
                {"domain": item.domain, "destination": str(item.destination)}
                for item in published
            ],
            "skipped": len(payloads) - len(published),
        }
    except Exception:
        for target in reversed(published):
            expected = manifest["destinations"][str(target.destination)]
            try:
                if expected["exists"]:
                    backup = backup_root / target.destination.relative_to(REMOTE_HOME)
                    run_remote(
                        ssh,
                        f"cp -p {shlex.quote(str(backup))} "
                        f"{shlex.quote(str(target.destination))}",
                        timeout=30,
                    )
                else:
                    run_remote(
                        ssh,
                        f"rm -f {shlex.quote(str(target.destination))}",
                        timeout=30,
                    )
            except Exception:
                pass
        raise
    finally:
        for payload in staged:
            try:
                sftp.remove(str(payload["temporary"]))
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--deploy", action="store_true")
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        result = (
            take_snapshot(ssh, sftp, args.snapshot_root)
            if args.snapshot
            else deploy(ssh, sftp, args.snapshot_root)
        )
    finally:
        sftp.close()
        ssh.close()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
