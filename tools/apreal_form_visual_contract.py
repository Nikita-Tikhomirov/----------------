"""Shared, scoped visual contract for AP-Real contact-form controls."""

from __future__ import annotations

import json
import re


MANAGED_START = "CLIENT_FORM_VISUAL_CONTRACT_START"
MANAGED_END = "CLIENT_FORM_VISUAL_CONTRACT_END"
STYLE_ID = "client-form-visual-contract"

STANDARD_INPUTS = """.csf-root .csf-form input:not([type=\"hidden\"]):not([type=\"submit\"]):not([type=\"button\"]):not([type=\"checkbox\"]):not([type=\"radio\"]):not(.csf-honeypot)"""
STANDARD_TEXTAREAS = ".csf-root .csf-form textarea"
CUSTOM_INPUTS = """.unipop-form input:not([type=\"hidden\"]):not([type=\"submit\"]):not([type=\"button\"]):not([type=\"checkbox\"]):not([type=\"radio\"])"""
CUSTOM_TEXTAREAS = (
    '.unipop-form textarea,'
    '.unipop-form[data-form="question"] textarea[name="coment"]'
)
CF7_INPUTS = (
    '.wpcf7-form input[name="f-name"],'
    '.wpcf7-form input[name="f-phone"],'
    '.wpcf7-form input[name="callback-quiz"],'
    '.wpcf7-form input[name="question-quiz"],'
    '.wpcf7-form input[name="callback-name"],'
    '.wpcf7-form input[name="callback-phone"],'
    '.wpcf7-form input[name="question-name"],'
    '.wpcf7-form input[name="question-phone"]'
)
CF7_TEXTAREAS = (
    '.wpcf7-form textarea[name="f-text"],'
    '.wpcf7-form textarea[name="question-message"]'
)
LEGACY_CF7_LABEL_SELECTORS = (
    '.wpcf7-form:has(input[name="question-name"]) label:has(input[name="question-name"]),'
    '.wpcf7-form:has(input[name="question-name"]) label:has(input[name="question-phone"]),'
    '.wpcf7-form:has(input[name="question-name"]) label:has(textarea[name="question-message"]),'
    '.wpcf7-form:has(input[name="question-name"]) label:has(input[name="question-quiz"]),'
    '.wpcf7-form:has(input[name="callback-name"]) label:has(input[name="callback-name"]),'
    '.wpcf7-form:has(input[name="callback-name"]) label:has(input[name="callback-phone"]),'
    '.wpcf7-form:has(input[name="callback-name"]) label:has(input[name="callback-quiz"])'
)
LEGACY_CF7_CONTROL_SELECTORS = (
    '.wpcf7-form:has(input[name="question-name"]) input[name="question-name"],'
    '.wpcf7-form:has(input[name="question-name"]) input[name="question-phone"],'
    '.wpcf7-form:has(input[name="question-name"]) textarea[name="question-message"],'
    '.wpcf7-form:has(input[name="question-name"]) input[name="question-quiz"],'
    '.wpcf7-form:has(input[name="callback-name"]) input[name="callback-name"],'
    '.wpcf7-form:has(input[name="callback-name"]) input[name="callback-phone"],'
    '.wpcf7-form:has(input[name="callback-name"]) input[name="callback-quiz"]'
)

SINGLE_LINE_SELECTORS = ",".join((STANDARD_INPUTS, CUSTOM_INPUTS, CF7_INPUTS))
TEXTAREA_SELECTORS = ",".join((STANDARD_TEXTAREAS, CUSTOM_TEXTAREAS, CF7_TEXTAREAS))
ALL_CONTROL_SELECTORS = ",".join((SINGLE_LINE_SELECTORS, TEXTAREA_SELECTORS))
FOCUS_SELECTORS = ",".join(
    f"{selector}:focus" for selector in ALL_CONTROL_SELECTORS.split(",")
)
PLACEHOLDER_SELECTORS = ",".join(
    f"{selector}::placeholder" for selector in ALL_CONTROL_SELECTORS.split(",")
)

VISUAL_CONTRACT_CSS = f"""
.csf-root .csf-form{{gap:16px!important}}
.csf-root .csf-form label{{display:block!important;width:100%!important;max-width:100%!important;box-sizing:border-box!important;font:600 14px/1.35 Arial,sans-serif!important;letter-spacing:0!important;color:#222!important}}
.csf-root .csf-form .csf-optional{{display:inline!important;margin-left:3px!important;font-weight:400!important;color:#667085!important}}
{LEGACY_CF7_LABEL_SELECTORS}{{display:block!important;font-family:inherit!important;font-size:14px!important;font-weight:500!important;line-height:1.35!important;letter-spacing:0!important;color:#344054!important}}
{ALL_CONTROL_SELECTORS}{{display:block!important;width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important;border:1px solid #aeb7c2!important;border-radius:4px!important;background:#fff!important;color:#1f2933!important;font-family:inherit!important;font-size:16px!important;font-weight:400!important;line-height:22px!important;letter-spacing:0!important;box-shadow:none!important;outline:0!important;appearance:none!important;transition:border-color .15s ease,box-shadow .15s ease!important}}
{SINGLE_LINE_SELECTORS}{{height:48px!important;min-height:48px!important;padding:12px 14px!important}}
{TEXTAREA_SELECTORS}{{height:120px!important;min-height:120px!important;padding:12px 14px!important;resize:vertical!important}}
.csf-root .csf-form label>{STANDARD_INPUTS.split(' ', 3)[-1]},.csf-root .csf-form label>textarea{{margin-top:7px!important}}
{CUSTOM_INPUTS},{CUSTOM_TEXTAREAS}{{margin:0 0 14px!important}}
{LEGACY_CF7_CONTROL_SELECTORS}{{margin-top:6px!important}}
{PLACEHOLDER_SELECTORS}{{color:#667085!important;opacity:1!important;font:inherit!important}}
{FOCUS_SELECTORS}{{border-color:#1d5f9f!important;box-shadow:0 0 0 3px rgba(29,95,159,.18)!important}}
""".strip()


def _replace_or_append(
    source: str,
    block: str,
    start_marker: str,
    end_marker: str,
    *,
    before: str | None = None,
) -> str:
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        flags=re.DOTALL,
    )
    if pattern.search(source):
        return pattern.sub(lambda _: block, source, count=1)
    if before and before in source:
        return source.replace(before, f"{block}\n{before}", 1)
    return f"{source.rstrip()}\n\n{block}\n"


def patch_javascript(source: str) -> str:
    start = f"/* {MANAGED_START} */"
    end = f"/* {MANAGED_END} */"
    css_literal = json.dumps(VISUAL_CONTRACT_CSS, ensure_ascii=False)
    block = (
        f"{start}\n"
        "(function(){"
        f"var id={json.dumps(STYLE_ID)};"
        "var style=document.getElementById(id);"
        "if(!style){style=document.createElement('style');style.id=id;document.head.appendChild(style);}"
        f"style.textContent={css_literal};"
        "})();\n"
        f"{end}"
    )
    return _replace_or_append(source, block, start, end)


def patch_html(source: str) -> str:
    start = f"<!-- {MANAGED_START} -->"
    end = f"<!-- {MANAGED_END} -->"
    block = (
        f"{start}\n"
        f'<style id="{STYLE_ID}">\n{VISUAL_CONTRACT_CSS}\n</style>\n'
        f"{end}"
    )
    return _replace_or_append(source, block, start, end, before="</body>")


def build_wordpress_plugin() -> str:
    return f'''<?php
/**
 * Plugin Name: AP-Real Form Visual Contract
 * Description: Keeps contact-form controls visually consistent without changing site content.
 */

if (!defined('ABSPATH')) {{
    exit;
}}

function apreal_form_visual_contract_render() {{
    ?>
    <style id="{STYLE_ID}">
    {VISUAL_CONTRACT_CSS}
    </style>
    <?php
}}
add_action('wp_footer', 'apreal_form_visual_contract_render', PHP_INT_MAX);
'''
