"""Helpers for preserving CF7 headers while removing unauthorized copies."""

from __future__ import annotations


def remove_bcc_recipient(
    mail: dict[str, object],
    recipient: str,
) -> dict[str, object]:
    """Return a mail config without the selected address in Bcc headers."""
    updated = dict(mail)
    headers = updated.get("additional_headers")
    if not isinstance(headers, str) or not headers:
        return updated

    newline = "\r\n" if "\r\n" in headers else "\n"
    trailing_newline = headers.endswith(("\r", "\n"))
    target = recipient.casefold()
    changed = False
    output: list[str] = []

    for line in headers.splitlines():
        name, separator, value = line.partition(":")
        if not separator or name.strip().casefold() != "bcc":
            output.append(line)
            continue

        addresses = [item.strip() for item in value.split(",") if item.strip()]
        retained = [item for item in addresses if target not in item.casefold()]
        if len(retained) == len(addresses):
            output.append(line)
            continue

        changed = True
        if retained:
            spacing = " " if value.startswith(" ") else ""
            output.append(f"{name}:{spacing}{', '.join(retained)}")

    if changed:
        cleaned = newline.join(output)
        if trailing_newline:
            cleaned += newline
        updated["additional_headers"] = cleaned
    return updated
