import json
import re
from types import SimpleNamespace

import paramiko

from tools import apreal_form_visual_contract as contract
from tools import build_apreal_acceptance_report as acceptance
from tools import deploy_apreal_form_visual_contract as deploy


def test_css_contract_covers_every_form_family_without_global_leakage():
    css = contract.VISUAL_CONTRACT_CSS

    for selector in (
        ".csf-root .csf-form",
        ".unipop-form",
        '.wpcf7-form input[name="f-name"]',
        '.wpcf7-form input[name="question-name"]',
    ):
        assert selector in css

    assert "height:48px!important" in css
    assert "min-height:120px!important" in css
    assert "font-size:16px!important" in css
    assert "border-radius:4px!important" in css
    assert "::placeholder" in css
    assert ":focus" in css
    assert not re.search(r"(?m)^\s*(?:input|textarea)\s*\{", css)


def test_standard_labels_keep_optional_copy_on_the_label_line():
    css = contract.VISUAL_CONTRACT_CSS

    assert (
        ".csf-root .csf-form label{display:block!important;"
        "width:100%!important;max-width:100%!important"
    ) in css
    assert ".csf-root .csf-form .csf-optional{display:inline!important" in css


def test_legacy_cf7_question_labels_are_readable_without_affecting_new_forms():
    css = contract.VISUAL_CONTRACT_CSS

    assert '.wpcf7-form:has(input[name="question-name"]) label:has(' in css
    assert "font-size:14px!important" in css
    assert "color:#344054!important" in css
    assert '.wpcf7-form label:has(input[name="f-name"])' not in css


def test_legacy_custom_question_padding_beats_late_theme_important_rule():
    css = contract.VISUAL_CONTRACT_CSS

    assert '.unipop-form[data-form="question"] textarea[name="coment"]' in css
    assert "padding:12px 14px!important" in css


def test_static_javascript_patch_is_idempotent():
    source = "(function(){console.log('forms');})();\n"

    first = contract.patch_javascript(source)
    second = contract.patch_javascript(first)

    assert first == second
    assert first.count(contract.MANAGED_START) == 1
    assert first.count(contract.MANAGED_END) == 1
    assert json.dumps(contract.VISUAL_CONTRACT_CSS, ensure_ascii=False) in first


def test_static_html_patch_is_idempotent_and_stays_before_body_end():
    source = "<!doctype html><html><head></head><body><main>Site</main></body></html>"

    first = contract.patch_html(source)
    second = contract.patch_html(first)

    assert first == second
    assert first.count(contract.MANAGED_START) == 1
    assert first.index(contract.MANAGED_START) < first.index("</body>")


def test_wordpress_plugin_renders_the_same_contract_at_footer_end():
    plugin = contract.build_wordpress_plugin()

    assert "PHP_INT_MAX" in plugin
    assert 'id="client-form-visual-contract"' in plugin
    assert contract.VISUAL_CONTRACT_CSS in plugin


def test_deployment_plan_covers_every_included_site_exactly_once():
    specs = deploy.target_specs()
    domains = [spec.domain for spec in specs]

    assert len(domains) == len(set(domains))
    assert set(domains) == set(acceptance.INCLUDED_DOMAINS)
    assert sum(spec.kind == "wordpress" for spec in specs) == 25
    assert sum(spec.kind == "javascript" for spec in specs) == 4
    assert sum(spec.kind == "html" for spec in specs) == 1
    medtex = next(spec for spec in specs if spec.domain == "medtex39.ru")
    assert "/39mchs.ru/public_html/__shared/medtex39/" in str(medtex.remote)


def test_ssh_connection_retries_transient_session_failure(monkeypatch, tmp_path):
    attempts = []

    class FakeSSHClient:
        def set_missing_host_key_policy(self, _policy):
            return None

        def connect(self, *_args, **_kwargs):
            attempts.append(1)
            if len(attempts) < 3:
                raise paramiko.SSHException("No existing session")

        def close(self):
            return None

    monkeypatch.setattr(deploy.paramiko, "SSHClient", FakeSSHClient)
    monkeypatch.setattr(deploy, "read_password", lambda _path: "secret")
    monkeypatch.setattr(deploy.time, "sleep", lambda _seconds: None)
    args = SimpleNamespace(
        host="example.test",
        user="user",
        credentials=tmp_path / "credentials.txt",
    )

    client = deploy.connect(args)

    assert isinstance(client, FakeSSHClient)
    assert len(attempts) == 3


def test_known_page_cache_is_flushed_after_wordpress_css_publication():
    assert deploy.PAGE_CACHE_DOMAINS == ("apreal.spb.ru",)

    command = deploy.wordpress_cache_flush_command("apreal.spb.ru")

    assert "/apreal.spb.ru/public_html" in command
    assert "wp cache flush" in command
    assert "wp w3-total-cache flush all" in command
