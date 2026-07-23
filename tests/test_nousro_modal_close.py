from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOOTER = (
    ROOT
    / "changes"
    / "2026-07-19"
    / "nousro.ru"
    / "wp-content"
    / "themes"
    / "Nousro-theme"
    / "footer.php"
)


def test_request_modal_uses_an_internal_materialize_close_button():
    source = FOOTER.read_text(encoding="utf-8")

    assert 'class="modal-close form-modal-close"' in source
    assert 'aria-label="Закрыть"' in source
    assert ".form-modal-close" in source
    assert "display: flex" in source
    assert "align-items: center" in source
    assert "justify-content: center" in source
    assert "modalOverlay.append(cross)" not in source
    assert "cross.innerHTML" not in source
