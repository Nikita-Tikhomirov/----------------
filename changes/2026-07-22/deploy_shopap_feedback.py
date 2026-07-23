#!/usr/bin/env python3
"""Deploy the shopap.ru form placement and registration captcha settings."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex

import paramiko


REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
REMOTE_ROOT = REMOTE_HOME / "shopap.ru/public_html"
REMOTE_SCRIPT = REMOTE_ROOT / "client-standard-forms.js"
REMOTE_HANDLER = REMOTE_ROOT / "client-standard-mail.php"
REMOTE_FORM_FILES = (REMOTE_SCRIPT, REMOTE_HANDLER)
CACHE_BUSTER = "20260723-1"
REMOTE_FOOTERS = tuple(
    REMOTE_ROOT / relative
    for relative in (
        "catalog/view/theme/default/template/common/footer.tpl",
        "catalog/view/theme/simplica/template/common/footer.tpl",
        "system/storage/modification/catalog/view/theme/default/template/common/footer.tpl",
        "system/storage/modification/catalog/view/theme/simplica/template/common/footer.tpl",
    )
)


def run(ssh: paramiko.SSHClient, command: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(command)
    del stdin
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"Remote command failed ({status}): {error.strip()}")
    return output.strip()


def connect(host: str, user: str) -> paramiko.SSHClient:
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        host,
        username=user,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
    )
    return ssh


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_remote(sftp: paramiko.SFTPClient, remote: PurePosixPath) -> bytes:
    with sftp.open(str(remote), "rb") as handle:
        return handle.read()


def build_antispam_php(root: str) -> str:
    config = f"{root}/config.php"
    return f"""require {config!r};
$backupRoot = getenv('SHOPAP_BACKUP_ROOT');
if (!$backupRoot || !is_dir($backupRoot)) {{
    fwrite(STDERR, "Backup directory is missing.\\n");
    exit(2);
}}
$db = new mysqli(DB_HOSTNAME, DB_USERNAME, DB_PASSWORD, DB_DATABASE, DB_PORT);
if ($db->connect_errno) {{
    fwrite(STDERR, "Database connection failed.\\n");
    exit(3);
}}
$keys = array('config_captcha', 'config_captcha_page', 'basic_captcha_status');
$quoted = array_map(function ($key) use ($db) {{
    return "'" . $db->real_escape_string($key) . "'";
}}, $keys);
$keyColumn = chr(96) . 'key' . chr(96);
$valueColumn = chr(96) . 'value' . chr(96);
$query = 'SELECT setting_id, store_id, code, ' . $keyColumn . ', ' .
    $valueColumn . ', serialized FROM ' . DB_PREFIX . 'setting WHERE ' .
    $keyColumn . ' IN (' . implode(',', $quoted) . ') ORDER BY setting_id';
$result = $db->query($query);
if (!$result) {{
    fwrite(STDERR, "Could not read current captcha settings.\\n");
    exit(4);
}}
$before = array();
while ($row = $result->fetch_assoc()) {{
    $before[] = $row;
}}
$backupFile = $backupRoot . '/settings-before.json';
if (file_put_contents($backupFile, json_encode($before, JSON_PRETTY_PRINT)) === false) {{
    fwrite(STDERR, "Could not save settings backup.\\n");
    exit(5);
}}

$db->begin_transaction();
try {{
    $db->query('DELETE FROM ' . DB_PREFIX . 'setting WHERE ' . $keyColumn .
        ' IN (' . implode(',', $quoted) . ')');
    $pageValue = $db->real_escape_string(json_encode(array('register')));
    $rows = array(
        "(0,'config','config_captcha','basic_captcha',0)",
        "(0,'config','config_captcha_page','" . $pageValue . "',1)",
        "(0,'basic_captcha','basic_captcha_status','1',0)"
    );
    $insert = 'INSERT INTO ' . DB_PREFIX . 'setting '
        . '(store_id, code, ' . $keyColumn . ', ' . $valueColumn . ', serialized) VALUES '
        . implode(',', $rows);
    if (!$db->query($insert)) {{
        throw new RuntimeException('Could not write captcha settings.');
    }}
    $db->commit();
}} catch (Throwable $error) {{
    $db->rollback();
    fwrite(STDERR, $error->getMessage() . "\\n");
    exit(6);
}}
echo "registration-captcha-enabled\\n";
"""


def update_footer_include(payload: bytes) -> bytes:
    marker = b"/client-standard-forms.js"
    if marker not in payload:
        raise RuntimeError("Standard form script include was not found")
    versioned = marker + f"?v={CACHE_BUSTER}".encode("ascii")
    return re.sub(marker + rb"(?:\?v=[^\"']*)?", versioned, payload)


def download(ssh: paramiko.SSHClient, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with ssh.open_sftp() as sftp:
        for remote in REMOTE_FORM_FILES:
            sftp.get(str(remote), str(target / remote.name))


def deploy(ssh: paramiko.SSHClient, source: Path, baseline: Path) -> str:
    for remote in REMOTE_FORM_FILES:
        candidate = source / remote.name
        reference = baseline / remote.name
        if not candidate.is_file():
            raise RuntimeError(f"Missing deployment file: {candidate}")
        if not reference.is_file():
            raise RuntimeError(f"Missing baseline file: {reference}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-shopap-feedback"
    run(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")

    with ssh.open_sftp() as sftp:
        for remote in REMOTE_FORM_FILES:
            live = read_remote(sftp, remote)
            reference = (baseline / remote.name).read_bytes()
            if digest(live) != digest(reference):
                raise RuntimeError(
                    f"Live {remote.name} changed since download: "
                    f"{digest(live)} != {digest(reference)}"
                )

        for remote in REMOTE_FORM_FILES:
            run(
                ssh,
                f"cp -p {shlex.quote(str(remote))} "
                f"{shlex.quote(str(backup_root / remote.name))}",
            )
            temporary = PurePosixPath(
                posixpath.join(str(REMOTE_ROOT), f".{remote.name}.new")
            )
            sftp.put(str(source / remote.name), str(temporary))
            run(
                ssh,
                f"chmod 0644 {shlex.quote(str(temporary))} && "
                f"mv {shlex.quote(str(temporary))} {shlex.quote(str(remote))}",
            )

        for footer in REMOTE_FOOTERS:
            backup = backup_root / footer.relative_to(REMOTE_ROOT)
            run(ssh, f"mkdir -p {shlex.quote(str(backup.parent))}")
            run(
                ssh,
                f"cp -p {shlex.quote(str(footer))} {shlex.quote(str(backup))}",
            )
            with sftp.open(str(footer), "rb") as handle:
                before = handle.read()
            after = update_footer_include(before)
            footer_temporary = PurePosixPath(str(footer) + ".new")
            with sftp.open(str(footer_temporary), "wb") as handle:
                handle.write(after)
            sftp.chmod(str(footer_temporary), 0o644)
            run(
                ssh,
                f"mv {shlex.quote(str(footer_temporary))} {shlex.quote(str(footer))}",
            )

    php = build_antispam_php(str(REMOTE_ROOT))
    encoded = base64.b64encode(php.encode("utf-8")).decode("ascii")
    php_command = f'eval(base64_decode("{encoded}"));'
    antispam = run(
        ssh,
        f"SHOPAP_BACKUP_ROOT={shlex.quote(str(backup_root))} "
        f"php -r {shlex.quote(php_command)}",
    )
    cache_root = REMOTE_ROOT / "system/storage/cache"
    run(ssh, f"find {shlex.quote(str(cache_root))} -type f -name 'cache.*' -delete")
    checksums = run(
        ssh,
        "sha256sum " + " ".join(shlex.quote(str(path)) for path in REMOTE_FORM_FILES),
    )
    print(antispam)
    print(checksums)
    return str(backup_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args.host, args.user)
    try:
        if args.mode == "download":
            download(ssh, args.path)
            print(args.path.resolve())
        else:
            if args.baseline is None:
                raise RuntimeError("--baseline is required for deploy")
            print(deploy(ssh, args.path, args.baseline))
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
