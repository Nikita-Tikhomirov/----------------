#!/usr/bin/env python3
"""Apply the medtex39.ru challenge flow to the downloaded live bundle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent / "medtex39.ru" / "deploy"
SCRIPT = ROOT / "client-standard-forms.js"


def replace_exact(source: str, old: str, new: str, expected: int) -> str:
    actual = source.count(old)
    if actual != expected:
        raise RuntimeError(f"Expected {expected} occurrence(s), found {actual}: {old[:60]}")
    return source.replace(old, new)


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    source = replace_exact(
        source,
        '<input type="hidden" name="page">',
        '<input type="hidden" name="page"><input type="hidden" name="form_token">',
        2,
    )
    source = replace_exact(
        source,
        ".csf-actions{position:fixed;right:96px;bottom:16px;z-index:2147483600;display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;max-width:calc(100vw - 112px)}",
        ".csf-actions{position:static;display:grid;gap:8px;max-width:none;margin:0 0 20px}",
        1,
    )
    source = replace_exact(
        source,
        ".csf-submit[disabled]{opacity:.65;cursor:wait}",
        ".csf-submit[disabled]{opacity:.65;cursor:wait}html.client-contact-modal-open body > jdiv{display:none!important}",
        1,
    )
    source = replace_exact(
        source,
        ".csf-actions{left:10px;right:72px;bottom:10px;display:grid;grid-template-columns:1fr 1fr;max-width:none}",
        ".csf-actions{display:grid;grid-template-columns:1fr 1fr;max-width:none}",
        1,
    )
    source = replace_exact(
        source,
        "document.body.appendChild(root);",
        "var actionHost=document.querySelector('.navigation-left.full-navigation');if(actionHost)actionHost.insertAdjacentElement('afterend',root);else document.body.appendChild(root);",
        1,
    )
    source = replace_exact(
        source,
        "var overlay=root.querySelector('.csf-overlay');",
        "var overlay=root.querySelector('.csf-overlay');"
        "function loadChallenge(form){"
        "var token=form.querySelector('[name=\"form_token\"]');"
        "var submit=form.querySelector('.csf-submit');"
        "var result=form.querySelector('.csf-result');"
        "token.value='';submit.disabled=true;"
        "return fetch('/client-standard-mail.php?challenge=1',{credentials:'same-origin',cache:'no-store'})"
        ".then(function(response){return response.json().then(function(payload){return {ok:response.ok,payload:payload};});})"
        ".then(function(outcome){if(!outcome.ok||!outcome.payload.token)throw new Error('Не удалось подготовить форму.');token.value=outcome.payload.token;})"
        ".catch(function(error){result.textContent=error.message||'Не удалось подготовить форму.';result.classList.add('is-visible','is-error');})"
        ".finally(function(){submit.disabled=false;});}",
        1,
    )
    source = replace_exact(
        source,
        "document.documentElement.style.overflow='';}",
        "document.documentElement.style.overflow='';document.documentElement.classList.remove('client-contact-modal-open');}",
        1,
    )
    source = replace_exact(
        source,
        "if(!modal)return;overlay.hidden=false;modal.hidden=false;",
        "if(!modal)return;overlay.hidden=false;modal.hidden=false;document.documentElement.classList.add('client-contact-modal-open');loadChallenge(modal.querySelector('.csf-form'));",
        1,
    )
    source = replace_exact(
        source,
        "form.querySelector('[name=\"page\"]').value=window.location.href;result.className='csf-result';",
        "if(!form.querySelector('[name=\"form_token\"]').value){result.textContent='Подождите, форма загружается.';result.className='csf-result is-visible is-error';loadChallenge(form);return;}"
        "form.querySelector('[name=\"page\"]').value=window.location.href;result.className='csf-result';",
        1,
    )
    source = replace_exact(
        source,
        "result.classList.add('is-visible');form.reset();",
        "result.classList.add('is-visible');form.reset();loadChallenge(form);",
        1,
    )
    SCRIPT.write_text(source, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
