#!/usr/bin/env python3
"""Deploy the corrected question fields after verifying the live baseline."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
FILES = {
    "changes/2026-07-19/mhsl.ru/wp-content/themes/license-center/footer.php": (
        HOME / "mhsl.ru/public_html/wp-content/themes/license-center/footer.php"
    ),
    "changes/2026-07-19/mhsl.ru/mail.php": (
        HOME / "mhsl.ru/public_html/mail.php"
    ),
    "changes/2026-07-19/med-license.ru/wp-content/themes/license-center/footer.php": (
        HOME
        / "med-license.ru/public_html/wp-content/themes/license-center/footer.php"
    ),
    "changes/2026-07-19/med-license.ru/mail.php": (
        HOME / "med-license.ru/public_html/mail.php"
    ),
}

NEW_FOOTER = """            <textarea name="coment" placeholder="Вопрос"></textarea>
            <input type="tel" name="phone" required placeholder="+7 (___) ___-__-__">
            <input type="text" name="name" placeholder="Имя">"""
OLD_FOOTER = """            <input type="email" name="email" required placeholder="mail@example.com">
            <textarea name="coment" placeholder="Вопрос" id=""></textarea>"""
NEW_MAIL = """    $phone = esc_html(wp_unslash(isset($_POST['phone']) ? $_POST['phone'] : ''));
    $name = esc_html(wp_unslash(isset($_POST['name']) ? $_POST['name'] : ''));
    $comment = esc_html(wp_unslash(isset($_POST['coment']) ? $_POST['coment'] : ''));
    if ($phone === '') {
        respond(false, 'Введите телефон.');
    }
    $subject = 'Задать вопрос';
    $message = "<p><strong>Вопрос:</strong> {$comment}</p><p><strong>Телефон:</strong> {$phone}</p><p><strong>Имя:</strong> {$name}</p><p><strong>Страница:</strong> {$page}</p>";"""
OLD_MAIL = """    $email = sanitize_email(wp_unslash(isset($_POST['email']) ? $_POST['email'] : ''));
    $comment = esc_html(wp_unslash(isset($_POST['coment']) ? $_POST['coment'] : ''));
    if (!is_email($email)) {
        respond(false, 'Введите корректный email.');
    }
    $subject = 'Задать вопрос';
    $message = "<p><strong>Email:</strong> {$email}</p><p><strong>Вопрос:</strong> {$comment}</p><p><strong>Страница:</strong> {$page}</p>";
    $headers[] = "Reply-To: {$email}";"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def accepted_live_versions(root: Path, relative: str) -> tuple[bytes, ...]:
    text = (root / relative).read_text(encoding="utf-8")
    if relative.endswith("footer.php"):
        stage_one = text.replace("z-index: 2147483600", "z-index: 999").replace(
            "z-index: 2147483601", "z-index: 1000"
        )
        if stage_one == text or stage_one.count(NEW_FOOTER) != 1:
            raise RuntimeError(f"Cannot reconstruct live baseline for {relative}")
        original = stage_one.replace(NEW_FOOTER, OLD_FOOTER)
        return stage_one.encode("utf-8"), original.encode("utf-8")

    if text.count(NEW_MAIL) != 1:
        raise RuntimeError(f"Cannot reconstruct live baseline for {relative}")
    original = text.replace(NEW_MAIL, OLD_MAIL)
    return text.encode("utf-8"), original.encode("utf-8")


def run(command: str, ssh: paramiko.SSHClient) -> None:
    _, stdout, stderr = ssh.exec_command(command)
    if stdout.channel.recv_exit_status():
        raise RuntimeError(stderr.read().decode("utf-8", "replace"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_root = HOME / f"_backups/{stamp}-question-fields"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, username=args.user, password=password, timeout=20)
    sftp = ssh.open_sftp()
    try:
        for relative, remote_path in FILES.items():
            remote = str(remote_path)
            with sftp.open(remote, "rb") as handle:
                live = handle.read()
            expected_versions = accepted_live_versions(args.root, relative)
            expected_hashes = {sha256(version) for version in expected_versions}
            if sha256(live) not in expected_hashes:
                raise RuntimeError(
                    f"Live file changed since baseline: {remote} "
                    f"({sha256(live)} not in {sorted(expected_hashes)})"
                )

        for relative, remote_path in FILES.items():
            remote = str(remote_path)
            backup = str(backup_root) + remote.removeprefix(str(HOME))
            run(
                f"mkdir -p {posixpath.dirname(backup)!r} "
                f"&& cp -p {remote!r} {backup!r}",
                ssh,
            )
            local = (args.root / relative).read_bytes()
            with sftp.open(remote, "wb") as handle:
                handle.write(local)
            sftp.chmod(remote, 0o644)
            with sftp.open(remote, "rb") as handle:
                deployed = handle.read()
            if sha256(deployed) != sha256(local):
                raise RuntimeError(f"Hash mismatch after upload: {remote}")
            print(f"OK {remote} sha256={sha256(deployed)}")
        print(f"BACKUP {backup_root}")
    finally:
        sftp.close()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
