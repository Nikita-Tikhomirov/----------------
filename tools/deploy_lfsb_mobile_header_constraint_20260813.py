#!/usr/bin/env python3
"""Back up and constrain the remaining fixed-width LFSB mobile header blocks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

try:
    from tools.deploy_apreal_standard_family import ROOT, connect
    from tools.deploy_residual_quality_fixes_20260813 import (
        LFSB_ROOT,
        REMOTE_HOME,
        backup_files,
        page_paths,
        read_remote,
        restore_files,
        sha256,
        write_atomic,
    )
except ModuleNotFoundError:
    from deploy_apreal_standard_family import ROOT, connect
    from deploy_residual_quality_fixes_20260813 import (
        LFSB_ROOT,
        REMOTE_HOME,
        backup_files,
        page_paths,
        read_remote,
        restore_files,
        sha256,
        write_atomic,
    )


MARKER = "/* AP-Real mobile legacy-card flow 2026-08-13 */"
OLD_STYLE = b'href="style.css?v=20260813-9"'
NEW_STYLE = b'href="style.css?v=20260813-10"'
CSS = r"""

/* AP-Real mobile legacy-card flow 2026-08-13 */
@media (max-width: 767px) {
  .cen_txt .entry,
  .cen_txt .entry * {
    position: static !important;
    float: none !important;
    width: auto !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-sizing: border-box;
  }

  .cen_txt .entry .rounded,
  .cen_txt .entry .pricing,
  .cen_txt .entry .showform {
    display: block !important;
    clear: both !important;
    margin: 12px 0 !important;
    padding: 12px !important;
    overflow: visible !important;
  }

  .cen_txt > [class^="block"] {
    position: static !important;
    float: none !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 12px 0 !important;
    padding: 12px !important;
    overflow: hidden !important;
    box-sizing: border-box;
  }

  .cen_txt > [class^="block"] .block-desc1,
  .cen_txt > [class^="block"] .m-title,
  .cen_txt > [class^="block"] .m-title2,
  .cen_txt > [class^="block"] .blue-block {
    position: static !important;
    float: none !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 0 10px !important;
    box-sizing: border-box;
  }

  .cen_txt > [class^="block"] .blok-picture23 {
    position: static !important;
    float: none !important;
    display: block !important;
    width: 120px !important;
    height: 120px !important;
    margin: 0 auto 12px !important;
  }

  .cen_txt > [class^="block"] .inf-block {
    position: static !important;
    float: none !important;
    display: flex !important;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 8px 0 0 !important;
  }

  .cen_txt > [class^="block"] .inf-block * {
    position: static !important;
    float: none !important;
    width: auto !important;
    height: auto !important;
    max-width: 100% !important;
  }

  .cen_txt > div,
  .cen_txt div[style*="width: 525px"],
  .cen_txt div[style*="width:525px"] {
    clear: both !important;
  }

  .cen_txt div[style*="width: 525px"] img,
  .cen_txt div[style*="width:525px"] img {
    float: none !important;
    display: block !important;
    width: auto !important;
    height: auto !important;
    margin: 0 auto 12px !important;
  }

  .cen_txt table,
  .cen_txt tbody,
  .cen_txt tr,
  .cen_txt td {
    height: auto !important;
    min-height: 0 !important;
  }
}
"""


def add_header_constraint(data: bytes) -> bytes:
    if MARKER.encode("ascii") in data:
        return data
    return data.rstrip() + CSS.encode("ascii") + b"\n"


def version_stylesheet(data: bytes) -> bytes:
    if NEW_STYLE in data:
        return data
    if OLD_STYLE not in data:
        raise ValueError("Expected LFSB stylesheet version was not found")
    return data.replace(OLD_STYLE, NEW_STYLE, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--stamp", default="20260813-210000-lfsb-mobile-header-constraint")
    args = parser.parse_args()
    if not args.deploy:
        parser.error("Use --deploy for the guarded live publication")

    ssh = connect(args)
    sftp = ssh.open_sftp()
    result: dict[str, object] = {"status": "started", "stamp": args.stamp}
    backup_root: PurePosixPath | None = None
    paths: list[PurePosixPath] = []
    backup_complete = False
    try:
        pages = page_paths(sftp)
        style_path = LFSB_ROOT / "style.css"
        paths = [*pages, style_path]
        backup_root = REMOTE_HOME / "_backups" / args.stamp
        result["backup_root"] = str(backup_root)
        result["backups"] = backup_files(ssh, sftp, paths, backup_root)
        backup_complete = True

        for path in pages:
            write_atomic(ssh, sftp, path, version_stylesheet(read_remote(sftp, path)), args.stamp)
        style_data = add_header_constraint(read_remote(sftp, style_path))
        write_atomic(ssh, sftp, style_path, style_data, args.stamp)

        if any(NEW_STYLE not in read_remote(sftp, path) for path in pages):
            raise RuntimeError("Not every public LFSB page references the new stylesheet version")
        live_style = read_remote(sftp, style_path)
        if MARKER.encode("ascii") not in live_style:
            raise RuntimeError("Published CSS marker is missing")
        result.update(
            status="published",
            page_count=len(pages),
            stylesheet_sha256=sha256(live_style),
        )
    except Exception as error:
        result.update(status="failed", error=str(error))
        if backup_complete and backup_root is not None:
            restore_files(ssh, paths, backup_root)
            result["rollback_performed"] = True
        output = ROOT / "output/residual-quality-fixes-20260813/lfsb-mobile-header-constraint-failed.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/residual-quality-fixes-20260813/lfsb-mobile-header-constraint.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
