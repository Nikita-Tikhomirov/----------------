#!/usr/bin/env python3
"""Safely publish the remaining AP-Real custom form contract updates."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex

import paramiko


ROOT = Path(__file__).resolve().parents[1]
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
DEFAULT_SNAPSHOT = ROOT / "tmp" / "ap-real-custom-predeploy-20260731"
SUCCESS = "Спасибо за Ваше сообщение. Оно успешно отправлено"
POLICY = "https://www.apreal.ru/konfedencialnost.html"
CONSENT = (
    'Нажимая на кнопку "Отправить" я даю согласие на обработку '
    f'персональных данных на условиях <a href="{POLICY}" target="_blank" '
    'rel="noopener noreferrer">Политики обработки персональных данных</a>'
)


def _apreal_form(kind: str) -> str:
    if kind == "callback":
        title = "ЗАКАЗАТЬ ЗВОНОК"
        fields = """    <div class="uk-margin">
        [text f-name class:uk-input placeholder "Имя (необязательно)"]
    </div>
    <div class="uk-margin">
        [tel* f-phone class:uk-input placeholder "+7 (___) ___-__-__"]
    </div>
    <div class="uk-margin">
        [quiz callback-quiz class:uk-input "Введите цифрами: пять|5"]
    </div>"""
    else:
        title = "ЗАДАТЬ ВОПРОС"
        fields = """    <div class="uk-margin">
        [text f-name class:uk-input placeholder "Имя (необязательно)"]
    </div>
    <div class="uk-margin">
        [tel* f-phone class:uk-input placeholder "+7 (___) ___-__-__"]
    </div>
    <div class="uk-margin">
        [textarea f-text class:uk-textarea 40x4 placeholder "Ваш вопрос (необязательно)"]
    </div>
    <div class="uk-margin">
        [quiz question-quiz class:uk-input "Введите цифрами: пять|5"]
    </div>"""
    return (
        '<fieldset class="uk-fieldset">\n'
        f'    <legend class="uk-legend">{title}</legend>\n'
        f"{fields}\n"
        f'    <p class="policity">{CONSENT}</p>\n'
        '    [submit class:uk-button class:uk-button-default "ОТПРАВИТЬ"]\n'
        "</fieldset>"
    )


def _nousro_form(kind: str) -> str:
    if kind == "callback":
        fields = """<label>Имя: [text callback-name placeholder "Имя (необязательно)"]</label>
<label>Телефон: [tel* callback-phone placeholder "+7 (___) ___-__-__"]</label>
[quiz callback-quiz "Введите цифрами: пять|5"]"""
    else:
        fields = """<label>Имя: [text question-name placeholder "Имя (необязательно)"]</label>
<label>Телефон: [tel* question-phone placeholder "+7 (___) ___-__-__"]</label>
<label>Ваш вопрос: [textarea question-message placeholder "Ваш вопрос (необязательно)"]</label>
[quiz question-quiz "Введите цифрами: пять|5"]"""
    return f'{fields}\n<p class="policity">{CONSENT}</p>\n[submit "Отправить"]'


CF7_FORMS = {
    "apreal.ru": {
        "root": "/home/n/nousroc9/apreal.ru/public_html",
        "callback": {
            "id": 6740,
            "title": "ЗАКАЗАТЬ ЗВОНОК",
            "form": _apreal_form("callback"),
            "mail": {
                "subject": "Заказ звонка - ГК АП-Риал",
                "sender": "ГК АП-Риал <wordpress@apreal.ru>",
                "recipient": "info@apreal.ru",
                "body": (
                    "Заказ звонка с сайта apreal.ru\n"
                    "Имя: [f-name]\nТелефон: [f-phone]\nСтраница: [_url]"
                ),
                "additional_headers": "Reply-To: wordpress@apreal.ru",
            },
            "success": SUCCESS,
        },
        "question": {
            "id": 4399,
            "title": "ЗАДАТЬ ВОПРОС",
            "form": _apreal_form("question"),
            "mail": {
                "subject": "Вопрос с сайта - ГК АП-Риал",
                "sender": "ГК АП-Риал <wordpress@apreal.ru>",
                "recipient": "info@apreal.ru",
                "body": (
                    "Вопрос с сайта apreal.ru\nИмя: [f-name]\n"
                    "Телефон: [f-phone]\nВопрос: [f-text]\nСтраница: [_url]"
                ),
                "additional_headers": "Reply-To: wordpress@apreal.ru",
            },
            "success": SUCCESS,
        },
    },
    "nousro-spb.ru": {
        "root": "/home/n/nousroc9/nousro-spb.ru/public_html",
        "callback": {
            "id": 2438,
            "title": "ЗАКАЗАТЬ ЗВОНОК",
            "form": _nousro_form("callback"),
            "mail": {
                "subject": "Заказ звонка с сайта nousro-spb.ru",
                "sender": "nousro-spb.ru <wordpress@nousro-spb.ru>",
                "recipient": "spb@nousro.ru",
                "body": (
                    "Имя: [callback-name]\nТелефон: [callback-phone]\n"
                    "Страница: [_url]"
                ),
                "additional_headers": "Reply-To: wordpress@nousro-spb.ru",
            },
            "success": SUCCESS,
        },
        "question": {
            "id": 2005,
            "title": "ЗАДАТЬ ВОПРОС",
            "form": _nousro_form("question"),
            "mail": {
                "subject": "Вопрос с сайта nousro-spb.ru",
                "sender": "nousro-spb.ru <wordpress@nousro-spb.ru>",
                "recipient": "spb@nousro.ru",
                "body": (
                    "Имя: [question-name]\nТелефон: [question-phone]\n"
                    "Вопрос: [question-message]\nСтраница: [_url]"
                ),
                "additional_headers": "Reply-To: wordpress@nousro-spb.ru",
            },
            "success": SUCCESS,
        },
    },
}


def deployment_files(
    domains: set[str] | None = None,
) -> tuple[dict[str, object], ...]:
    entries = (
        (
            "apreal.ru",
            ROOT / "changes/2026-08-02/cf7-envelope-sender/apreal.ru.php",
            REMOTE_HOME
            / "apreal.ru/public_html/wp-content/mu-plugins/client-form-envelope-sender.php",
        ),
        (
            "nousro-spb.ru",
            ROOT / "changes/2026-08-02/cf7-envelope-sender/nousro-spb.ru.php",
            REMOTE_HOME
            / "nousro-spb.ru/public_html/wp-content/mu-plugins/client-form-envelope-sender.php",
        ),
        (
            "mca24.ru",
            ROOT / "changes/2026-07-19/mca24.ru/wp-content/themes/mca/footer.php",
            REMOTE_HOME / "mca24.ru/public_html/wp-content/themes/mca/footer.php",
        ),
        (
            "mca24.ru",
            ROOT / "changes/2026-07-19/mca24.ru/mail.php",
            REMOTE_HOME / "mca24.ru/public_html/mail.php",
        ),
        (
            "med-license.ru",
            ROOT / "changes/2026-07-19/med-license.ru/wp-content/themes/license-center/footer.php",
            REMOTE_HOME / "med-license.ru/public_html/wp-content/themes/license-center/footer.php",
        ),
        (
            "med-license.ru",
            ROOT / "changes/2026-07-19/med-license.ru/mail.php",
            REMOTE_HOME / "med-license.ru/public_html/mail.php",
        ),
        (
            "mhsl.ru",
            ROOT / "changes/2026-07-19/mhsl.ru/wp-content/themes/license-center/footer.php",
            REMOTE_HOME / "mhsl.ru/public_html/wp-content/themes/license-center/footer.php",
        ),
        (
            "mhsl.ru",
            ROOT / "changes/2026-07-19/mhsl.ru/mail.php",
            REMOTE_HOME / "mhsl.ru/public_html/mail.php",
        ),
        (
            "apreal36.ru",
            ROOT / "changes/2026-07-23/apreal36.ru/deploy/wp-content/themes/basic/footer.php",
            REMOTE_HOME / "apreal36.ru/public_html/wp-content/themes/basic/footer.php",
        ),
        (
            "apreal36.ru",
            ROOT / "changes/2026-07-23/apreal36.ru/deploy/mail.php",
            REMOTE_HOME / "apreal36.ru/public_html/mail.php",
        ),
        (
            "fsa-lab.ru",
            ROOT / "changes/2026-08-01/runtime-repairs/fsa-lab.ru/public_html/index.html",
            REMOTE_HOME / "fsa-lab.ru/public_html/index.html",
        ),
        (
            "fsa-lab.ru",
            ROOT / "changes/2026-07-19/fsa-lab.ru/mail.php",
            REMOTE_HOME / "fsa-lab.ru/public_html/mail.php",
        ),
        (
            "nousro-spb.ru",
            ROOT / "changes/2026-07-22/nousro-spb-question-fix.php",
            REMOTE_HOME
            / "nousro-spb.ru/public_html/wp-content/mu-plugins/nousro-spb-question-fix.php",
        ),
    )
    files = tuple(
        {"domain": domain, "source": source, "remote": remote}
        for domain, source, remote in entries
    )
    if domains is None:
        return files
    return tuple(item for item in files if item["domain"] in domains)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_password(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"Пароль:\s*(\S+)", text)
    if not match:
        raise RuntimeError(f"Password marker was not found in {path}")
    return match.group(1)


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.host,
        username=args.user,
        password=read_password(args.credentials),
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return ssh


def run_remote(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip() or f"Exit code {status}")
    return output.strip()


def wp_command(root: str, *parts: str) -> str:
    quoted = " ".join(shlex.quote(part) for part in parts)
    return f"wp --path={shlex.quote(root)} {quoted} 2>/dev/null"


def get_meta(ssh: paramiko.SSHClient, root: str, form_id: int, key: str):
    if key in {"_mail", "_messages"}:
        raw = run_remote(
            ssh,
            wp_command(root, "post", "meta", "get", str(form_id), key, "--format=json"),
        )
        return json.loads(raw)
    return run_remote(
        ssh,
        wp_command(root, "post", "meta", "get", str(form_id), key),
    )


def set_meta(ssh: paramiko.SSHClient, root: str, form_id: int, key: str, value) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, dict) else str(value)
    suffix = ("--format=json",) if isinstance(value, dict) else ()
    run_remote(
        ssh,
        wp_command(
            root,
            "post",
            "meta",
            "update",
            str(form_id),
            key,
            payload,
            *suffix,
        ),
    )


def get_form_state(ssh: paramiko.SSHClient, root: str, form_id: int) -> dict[str, object]:
    return {
        "title": run_remote(
            ssh,
            wp_command(root, "post", "get", str(form_id), "--field=post_title"),
        ),
        "form": get_meta(ssh, root, form_id, "_form"),
        "mail": get_meta(ssh, root, form_id, "_mail"),
        "messages": get_meta(ssh, root, form_id, "_messages"),
    }


def set_form_state(
    ssh: paramiko.SSHClient,
    root: str,
    form_id: int,
    state: dict[str, object],
) -> None:
    run_remote(
        ssh,
        wp_command(
            root,
            "post",
            "update",
            str(form_id),
            f"--post_title={state['title']}",
        ),
    )
    set_meta(ssh, root, form_id, "_form", state["form"])
    set_meta(ssh, root, form_id, "_mail", state["mail"])
    set_meta(ssh, root, form_id, "_messages", state["messages"])


def desired_state(current: dict[str, object], definition: dict[str, object]) -> dict[str, object]:
    mail = dict(current["mail"])
    mail.update(definition["mail"])
    messages = dict(current["messages"])
    messages["mail_sent_ok"] = definition["success"]
    return {
        "title": definition["title"],
        "form": definition["form"],
        "mail": mail,
        "messages": messages,
    }


def snapshot_file(snapshot_root: Path, remote: PurePosixPath) -> Path:
    relative = str(remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
    return snapshot_root / "files" / relative


def read_remote_optional(sftp: paramiko.SFTPClient, remote: PurePosixPath) -> bytes | None:
    try:
        with sftp.open(str(remote), "rb") as handle:
            return handle.read()
    except OSError as error:
        if getattr(error, "errno", None) == 2:
            return None
        raise


def take_snapshot(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
    domains: set[str] | None = None,
) -> dict[str, object]:
    manifest: dict[str, object] = {"files": {}, "cf7": {}}
    for item in deployment_files(domains):
        remote = item["remote"]
        data = read_remote_optional(sftp, remote)
        local = snapshot_file(snapshot_root, remote)
        if data is not None:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
        elif local.exists():
            local.unlink()
        manifest["files"][str(remote)] = {
            "domain": item["domain"],
            "exists": data is not None,
            "size": len(data) if data is not None else 0,
            "sha256": sha256(data) if data is not None else None,
        }
    for domain, forms in CF7_FORMS.items():
        if domains is not None and domain not in domains:
            continue
        root = forms["root"]
        manifest["cf7"][domain] = {}
        for kind in ("callback", "question"):
            form_id = forms[kind]["id"]
            manifest["cf7"][domain][kind] = get_form_state(ssh, root, form_id)
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_snapshot(snapshot_root: Path) -> dict[str, object]:
    path = snapshot_root / "manifest.json"
    if not path.is_file():
        raise RuntimeError(f"Missing snapshot manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_remote_json(sftp: paramiko.SFTPClient, path: PurePosixPath, value) -> None:
    with sftp.open(str(path), "wb") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"))


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
    domains: set[str] | None = None,
) -> dict[str, object]:
    snapshot = load_snapshot(snapshot_root)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-custom-form-completion"
    files = deployment_files(domains)
    selected_cf7 = tuple(
        (domain, forms)
        for domain, forms in CF7_FORMS.items()
        if domains is None or domain in domains
    )
    staged: list[tuple[dict[str, object], str, bytes, bool]] = []
    changed_forms: list[tuple[str, str, dict[str, object]]] = []
    published_files: list[dict[str, object]] = []
    try:
        for item in files:
            source = item["source"]
            remote = item["remote"]
            if not source.is_file():
                raise RuntimeError(f"Missing candidate: {source}")
            baseline_state = snapshot["files"][str(remote)]
            baseline_exists = bool(baseline_state.get("exists", True))
            baseline = (
                snapshot_file(snapshot_root, remote).read_bytes()
                if baseline_exists
                else None
            )
            current = read_remote_optional(sftp, remote)
            if current != baseline:
                raise RuntimeError(f"Live file changed after snapshot: {remote}")
            candidate = source.read_bytes()
            temporary = f"{remote}.codex-{stamp}"
            run_remote(ssh, f"mkdir -p {shlex.quote(str(remote.parent))}")
            with sftp.open(temporary, "wb") as handle:
                handle.write(candidate)
            sftp.chmod(temporary, 0o644)
            with sftp.open(temporary, "rb") as handle:
                if handle.read() != candidate:
                    raise RuntimeError(f"Staged upload mismatch: {remote}")
            staged.append((item, temporary, candidate, baseline_exists))

        for item, temporary, _, _ in staged:
            if item["remote"].suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(temporary)}")

        for domain, forms in selected_cf7:
            root = forms["root"]
            for kind in ("callback", "question"):
                form_id = forms[kind]["id"]
                current = get_form_state(ssh, root, form_id)
                baseline = snapshot["cf7"][domain][kind]
                if current != baseline:
                    raise RuntimeError(
                        f"CF7 form changed after snapshot: {domain} {kind} {form_id}"
                    )

        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for item, _, _, baseline_exists in staged:
            if not baseline_exists:
                continue
            remote = item["remote"]
            relative = str(remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
            backup = backup_root / "files" / relative
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(remote))} {shlex.quote(str(backup))}",
            )
        write_remote_json(sftp, backup_root / "cf7-before.json", snapshot["cf7"])

        for domain, forms in selected_cf7:
            root = forms["root"]
            for kind in ("callback", "question"):
                definition = forms[kind]
                baseline = snapshot["cf7"][domain][kind]
                target = desired_state(baseline, definition)
                set_form_state(ssh, root, definition["id"], target)
                changed_forms.append((domain, kind, baseline))
                verified = get_form_state(ssh, root, definition["id"])
                if verified != target:
                    raise RuntimeError(
                        f"CF7 verification failed: {domain} {kind} {definition['id']}"
                    )

        for item, temporary, candidate, _ in staged:
            remote = item["remote"]
            run_remote(ssh, f"mv -f {shlex.quote(temporary)} {shlex.quote(str(remote))}")
            with sftp.open(str(remote), "rb") as handle:
                live = handle.read()
            if live != candidate:
                raise RuntimeError(f"Published file mismatch: {remote}")
            published_files.append(
                {
                    "domain": item["domain"],
                    "remote": str(remote),
                    "size": len(live),
                    "sha256": sha256(live),
                }
            )

        for domain, forms in selected_cf7:
            root = forms["root"]
            run_remote(ssh, wp_command(root, "cache", "flush"))
            code = base64.b64encode(
                b'if (class_exists("autoptimizeCache")) { autoptimizeCache::clearall(); }'
            ).decode("ascii")
            run_remote(
                ssh,
                wp_command(
                    root,
                    "eval",
                    f'eval(base64_decode("{code}"));',
                ),
            )

        return {
            "backup_root": str(backup_root),
            "published_files": published_files,
            "updated_cf7": [
                {
                    "domain": domain,
                    "kind": kind,
                    "form_id": CF7_FORMS[domain][kind]["id"],
                }
                for domain, kind, _ in changed_forms
            ],
        }
    except Exception:
        for domain, kind, baseline in reversed(changed_forms):
            forms = CF7_FORMS[domain]
            try:
                set_form_state(ssh, forms["root"], forms[kind]["id"], baseline)
            except Exception:
                pass
        for item in files:
            remote = item["remote"]
            relative = str(remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
            backup = backup_root / "files" / relative
            try:
                baseline_state = snapshot["files"][str(remote)]
                if baseline_state.get("exists", True):
                    run_remote(
                        ssh,
                        f"test -f {shlex.quote(str(backup))} && "
                        f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(remote))} || true",
                    )
                else:
                    run_remote(ssh, f"rm -f {shlex.quote(str(remote))}")
            except Exception:
                pass
        raise
    finally:
        for _, temporary, _, _ in staged:
            try:
                sftp.remove(temporary)
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
    parser.add_argument("--domains", nargs="*")
    args = parser.parse_args()
    domains = set(args.domains) if args.domains else None

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        result = (
            take_snapshot(ssh, sftp, args.snapshot_root, domains)
            if args.snapshot
            else deploy(ssh, sftp, args.snapshot_root, domains)
        )
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output" / "ap-real-custom-form-deploy-2026-07-31.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
