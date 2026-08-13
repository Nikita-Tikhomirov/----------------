#!/usr/bin/env python3
"""Back up and publish the 2026-08-13 MEDLIC/LFSB quality fixes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
from typing import Iterable

try:
    from tools.deploy_apreal_standard_family import ROOT, connect, run_remote
except ModuleNotFoundError:
    from deploy_apreal_standard_family import ROOT, connect, run_remote


REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
LFSB_ROOT = REMOTE_HOME / "lfsb.ru/public_html"
MEDLIC_ROOT = REMOTE_HOME / "medlic.spb.ru/public_html"
MARKER = "/* AP-Real mobile quality fix 2026-08-13 */"
CONSTRAINT_MARKER = "/* AP-Real mobile table constraint fix 2026-08-13 */"
TABLE_OVERRIDE_MARKER = "/* AP-Real mobile table width override 2026-08-13 */"
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1">'
STYLE_HREF = 'href="style.css?v=20260813-3"'

RESPONSIVE_CSS = r"""

/* AP-Real mobile quality fix 2026-08-13 */
@media (max-width: 767px) {
  html,
  body {
    width: 100%;
    max-width: 100%;
    overflow-x: hidden;
  }

  body {
    background: #fff;
  }

  table[width="1000"],
  table[width="950"],
  table[width="560"],
  table[width="220"] {
    width: 100% !important;
    max-width: 100% !important;
  }

  img,
  iframe {
    max-width: 100%;
  }

  #he1 {
    height: auto;
    min-height: 0;
    background: #fff;
  }

  #he1 > table > tbody > tr {
    display: flex;
    flex-direction: column;
  }

  #he1 > table > tbody > tr > td {
    display: block;
    width: 100% !important;
    box-sizing: border-box;
  }

  .hed1 {
    margin: 16px 16px 8px;
    font-size: 22px;
    line-height: 1.15;
  }

  .hed2,
  .hed3 {
    margin-left: 16px;
    margin-right: 16px;
    text-align: left;
  }

  .head_cont {
    margin: 14px 16px 0;
  }

  .men_cont {
    margin: 10px 16px 16px;
    line-height: 1.8;
  }

  #he2 {
    height: auto;
    padding: 8px;
    background: #64091d;
    box-sizing: border-box;
  }

  #he2 table,
  #he2 tbody,
  #he2 tr {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px 14px;
    width: 100% !important;
  }

  #he2 td {
    display: block;
    width: auto !important;
    padding: 5px 0;
  }

  #he2 td:has(> img),
  #he2 td:empty {
    display: none;
  }

  #he3 {
    display: none;
  }

  tr:has(> #ce1) {
    display: flex;
    flex-direction: column;
  }

  tr:has(> #ce1) > td {
    display: block;
    width: 100% !important;
    box-sizing: border-box;
  }

  tr:has(> #ce1) > td:first-child {
    order: 2;
  }

  tr:has(> #ce1) > #ce1 {
    order: 1;
  }

  tr:has(> #ce1) > td:last-child {
    order: 3;
  }

  #ce1 {
    background: #fff;
  }

  .cen_txt {
    margin: 18px 16px 22px;
    font-size: 15px;
    line-height: 1.5;
    text-align: left;
  }

  h1,
  h2 {
    margin: 10px 0;
    font-size: 17px;
    line-height: 1.3;
  }

  #le1,
  #le2,
  #le4,
  #ra2,
  #ra2a {
    display: none;
  }

  #le3,
  #le3a,
  #ra1,
  #ra3 {
    background: #777;
  }

  #le5 {
    background: #64091d;
  }

  #le6,
  #le8,
  #ra4,
  #ra5 {
    background: #f3f3f3;
  }

  .menu li {
    background: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
    padding: 7px 16px;
  }

  .rblok,
  .rblok_txt,
  .bl_cont,
  .rbl_txt {
    margin: 0;
    padding: 14px 16px;
  }

  #fo1 {
    height: auto;
    padding: 16px;
    background: #f3f3f3;
    box-sizing: border-box;
  }

  #fo1 > table > tbody > tr {
    display: flex;
    flex-direction: column;
  }

  #fo1 > table > tbody > tr > td {
    display: block;
    width: 100% !important;
  }

  .copyr,
  .niz_foot {
    margin: 0 0 14px;
    text-align: left;
  }

  .foot2,
  .foot3 {
    color: #64091d;
  }
}
"""

CONSTRAINT_CSS = r"""

/* AP-Real mobile table constraint fix 2026-08-13 */
@media (max-width: 767px) {
  body > table *,
  .cen_txt,
  .rblok,
  .rblok_txt,
  .bl_cont,
  .rbl_txt {
    min-width: 0;
  }

  .cen_txt,
  .cen_txt *,
  .rblok,
  .rblok_txt,
  .bl_cont,
  .rbl_txt {
    overflow-wrap: anywhere;
    word-break: normal;
  }

  input,
  textarea,
  select {
    max-width: 100%;
    box-sizing: border-box;
  }
}
"""

TABLE_OVERRIDE_CSS = r"""

/* AP-Real mobile table width override 2026-08-13 */
@media (max-width: 767px) {
  body > table,
  body > table table {
    width: 100% !important;
    max-width: 100% !important;
    table-layout: auto !important;
  }

  body > table td {
    max-width: 100% !important;
  }
}
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_viewport(data: bytes) -> bytes:
    if VIEWPORT.encode("ascii") in data:
        return data
    lines = data.splitlines(keepends=True)
    for index, line in enumerate(lines):
        lowered = line.lower()
        if b"http-equiv=\"content-type\"" in lowered:
            ending = b"\r\n" if line.endswith(b"\r\n") else b"\n"
            lines.insert(index + 1, VIEWPORT.encode("ascii") + ending)
            return b"".join(lines)
    raise ValueError("Content-Type meta tag was not found")


def add_responsive_css(data: bytes) -> bytes:
    changed = data
    if MARKER.encode("ascii") not in changed:
        changed = changed.rstrip() + RESPONSIVE_CSS.encode("ascii") + b"\n"
    if CONSTRAINT_MARKER.encode("ascii") not in changed:
        changed = changed.rstrip() + CONSTRAINT_CSS.encode("ascii") + b"\n"
    if TABLE_OVERRIDE_MARKER.encode("ascii") not in changed:
        changed = changed.rstrip() + TABLE_OVERRIDE_CSS.encode("ascii") + b"\n"
    return changed


def version_stylesheet(data: bytes) -> bytes:
    versioned = STYLE_HREF.encode("ascii")
    if versioned in data:
        return data
    for original in (
        b'href="style.css?v=20260813-2"',
        b'href="style.css?v=20260813-1"',
        b'href="style.css"',
    ):
        if original in data:
            return data.replace(original, versioned, 1)
    if versioned not in data:
        raise ValueError("LFSB stylesheet link was not found")
    return data


def read_remote(sftp, path: PurePosixPath) -> bytes:
    with sftp.open(str(path), "rb") as handle:
        return handle.read()


def write_atomic(ssh, sftp, path: PurePosixPath, data: bytes, stamp: str) -> None:
    temporary = PurePosixPath(f"{path}.codex-{stamp}")
    with sftp.open(str(temporary), "wb") as handle:
        handle.write(data)
    sftp.chmod(str(temporary), 0o644)
    if sha256(read_remote(sftp, temporary)) != sha256(data):
        raise RuntimeError(f"Staged upload mismatch: {path}")
    if path.suffix == ".php":
        run_remote(ssh, f"php -l {shlex.quote(str(temporary))}")
    run_remote(
        ssh,
        f"mv -f {shlex.quote(str(temporary))} {shlex.quote(str(path))}",
    )
    if sha256(read_remote(sftp, path)) != sha256(data):
        raise RuntimeError(f"Published upload mismatch: {path}")


def page_paths(sftp) -> list[PurePosixPath]:
    paths: list[PurePosixPath] = []
    for item in sftp.listdir_attr(str(LFSB_ROOT)):
        if not item.filename.endswith(".php"):
            continue
        path = LFSB_ROOT / item.filename
        data = read_remote(sftp, path)
        if b'href="style.css' in data and b"ssi/header.php" in data:
            paths.append(path)
    return sorted(paths)


def backup_files(ssh, sftp, paths: Iterable[PurePosixPath], backup_root: PurePosixPath) -> dict[str, object]:
    files: dict[str, object] = {}
    for path in paths:
        relative = str(path).removeprefix(str(REMOTE_HOME)).lstrip("/")
        backup = backup_root / relative
        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup.parent))}")
        run_remote(ssh, f"cp -p {shlex.quote(str(path))} {shlex.quote(str(backup))}")
        original = read_remote(sftp, path)
        copied = read_remote(sftp, backup)
        if original != copied:
            raise RuntimeError(f"Backup mismatch: {path}")
        files[str(path)] = {
            "backup": str(backup),
            "sha256": sha256(original),
            "bytes": len(original),
        }
    return files


def backup_medlic(ssh, backup_root: PurePosixPath) -> dict[str, str]:
    root = shlex.quote(str(MEDLIC_ROOT))
    backup = shlex.quote(str(backup_root))
    run_remote(ssh, f"mkdir -p {backup}")
    run_remote(ssh, f"cd {root} && wp db export {backup}/medlic-database.sql --add-drop-table")
    run_remote(ssh, f"cd {root} && wp post get 13 --field=post_content > {backup}/medlic-post-13.html")
    checks = run_remote(
        ssh,
        f"sha256sum {backup}/medlic-database.sql {backup}/medlic-post-13.html",
    )
    return {
        "database": f"{backup_root}/medlic-database.sql",
        "post_content": f"{backup_root}/medlic-post-13.html",
        "sha256sum": checks,
    }


def restore_files(ssh, paths: Iterable[PurePosixPath], backup_root: PurePosixPath) -> None:
    for path in paths:
        relative = str(path).removeprefix(str(REMOTE_HOME)).lstrip("/")
        backup = backup_root / relative
        run_remote(
            ssh,
            f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(path))}",
        )


def restore_medlic_post(ssh, backup_root: PurePosixPath) -> None:
    backup = backup_root / "medlic-post-13.html"
    php = (
        f'$content=file_get_contents({json.dumps(str(backup))}); '
        'if($content===false){fwrite(STDERR,"Cannot read MEDLIC backup"); exit(1);} '
        '$result=wp_update_post(array("ID"=>13,"post_content"=>$content),true); '
        'if(is_wp_error($result)){fwrite(STDERR,$result->get_error_message()); exit(1);} '
        'echo "restored_post=".$result;'
    )
    run_remote(
        ssh,
        f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp eval {shlex.quote(php)}",
    )
    run_remote(ssh, f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp cache flush")


def update_medlic(ssh) -> str:
    before_a = "Всеь процессы".encode("utf-8").hex()
    before_b = "Росздравнадзоррешает".encode("utf-8").hex()
    after_a = "Все процессы".encode("utf-8").hex()
    after_b = "Росздравнадзор решает".encode("utf-8").hex()
    php = (
        '$id=13; $content=get_post_field("post_content",$id,"raw"); '
        f'$from=array(hex2bin("{before_a}"),hex2bin("{before_b}")); '
        f'$to=array(hex2bin("{after_a}"),hex2bin("{after_b}")); '
        '$new=str_replace($from,$to,$content,$count); '
        'if($count!==0 && $count!==2){fwrite(STDERR,"Expected 0 or 2 replacements, got ".$count); exit(1);} '
        'if(strpos($new,$to[0])===false || strpos($new,$to[1])===false){fwrite(STDERR,"Corrected MEDLIC text is missing"); exit(1);} '
        '$result=wp_update_post(array("ID"=>$id,"post_content"=>$new),true); '
        'if(is_wp_error($result)){fwrite(STDERR,$result->get_error_message()); exit(1);} '
        'echo "updated_post=".$result." replacements=".$count;'
    )
    result = run_remote(
        ssh,
        f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp eval {shlex.quote(php)}",
    )
    run_remote(ssh, f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp cache flush")
    run_remote(
        ssh,
        f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp eval "
        + shlex.quote(
            'if(class_exists("WpFastestCache")){'
            '$cache=new WpFastestCache(); $cache->deleteCache(true);}'
        ),
    )
    return result


def verify_medlic(ssh) -> str:
    bad_a = "Всеь процессы".encode("utf-8").hex()
    bad_b = "Росздравнадзоррешает".encode("utf-8").hex()
    good_a = "Все процессы".encode("utf-8").hex()
    good_b = "Росздравнадзор решает".encode("utf-8").hex()
    php = (
        '$c=get_post_field("post_content",13,"raw"); '
        f'$ok=strpos($c,hex2bin("{bad_a}"))===false && strpos($c,hex2bin("{bad_b}"))===false '
        f'&& strpos($c,hex2bin("{good_a}"))!==false && strpos($c,hex2bin("{good_b}"))!==false; '
        'if(!$ok){fwrite(STDERR,"MEDLIC content verification failed"); exit(1);} echo "verified";'
    )
    return run_remote(
        ssh,
        f"cd {shlex.quote(str(MEDLIC_ROOT))} && wp eval {shlex.quote(php)}",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--stamp", default="20260813-200000-residual-quality-fixes")
    args = parser.parse_args()
    if not args.deploy:
        parser.error("Use --deploy for the guarded live publication")

    ssh = connect(args)
    sftp = ssh.open_sftp()
    result: dict[str, object] = {"status": "started", "stamp": args.stamp}
    changed_paths: list[PurePosixPath] = []
    backup_root: PurePosixPath | None = None
    backup_complete = False
    medlic_update_started = False
    try:
        pages = page_paths(sftp)
        if not pages:
            raise RuntimeError("No LFSB template pages were discovered")
        style_path = LFSB_ROOT / "style.css"
        changed_paths = [*pages, style_path]
        backup_root = REMOTE_HOME / "_backups" / args.stamp
        result["backup_root"] = str(backup_root)
        result["file_backups"] = backup_files(ssh, sftp, changed_paths, backup_root)
        result["medlic_backup"] = backup_medlic(ssh, backup_root)
        backup_complete = True

        for path in pages:
            original = read_remote(sftp, path)
            candidate = version_stylesheet(add_viewport(original))
            write_atomic(ssh, sftp, path, candidate, args.stamp)
        style_candidate = add_responsive_css(read_remote(sftp, style_path))
        write_atomic(ssh, sftp, style_path, style_candidate, args.stamp)

        medlic_update_started = True
        result["medlic_update"] = update_medlic(ssh)
        result["medlic_verification"] = verify_medlic(ssh)
        result["lfsb_pages"] = [str(path) for path in pages]
        result["lfsb_page_count"] = len(pages)
        result["lfsb_viewport_count"] = sum(
            VIEWPORT.encode("ascii") in read_remote(sftp, path) for path in pages
        )
        result["lfsb_css_marker"] = MARKER.encode("ascii") in read_remote(sftp, style_path)
        if result["lfsb_viewport_count"] != len(pages) or not result["lfsb_css_marker"]:
            raise RuntimeError("LFSB publication verification failed")
        result["status"] = "published"
    except Exception as error:
        result["status"] = "failed"
        result["error"] = str(error)
        if backup_complete and backup_root is not None:
            rollback_errors: list[str] = []
            try:
                restore_files(ssh, changed_paths, backup_root)
            except Exception as rollback_error:
                rollback_errors.append(f"LFSB: {rollback_error}")
            if medlic_update_started:
                try:
                    restore_medlic_post(ssh, backup_root)
                except Exception as rollback_error:
                    rollback_errors.append(f"MEDLIC: {rollback_error}")
            result["rollback_performed"] = not rollback_errors
            if rollback_errors:
                result["rollback_errors"] = rollback_errors
        output = ROOT / "output/residual-quality-fixes-20260813/deployment-failed.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/residual-quality-fixes-20260813/deployment.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
