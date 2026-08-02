from __future__ import annotations


def test_hidden_underlay_video_passes():
    from tools.verify_apreal_hidden_videos import inspect_html

    result = inspect_html(
        '<div class="underlay" hidden aria-hidden="true">'
        '<video class="underlay__video" src="/bg.mp4"></video>'
        "</div>"
    )

    assert result["passed"] is True
    assert result["underlays"][0]["videos"][0]["src"] == "/bg.mp4"


def test_visible_underlay_video_fails():
    from tools.verify_apreal_hidden_videos import inspect_html

    result = inspect_html(
        '<div class="underlay"><video class="underlay__video" src="/bg.mp4"></video></div>'
    )

    assert result["passed"] is False


def test_aria_hidden_without_hidden_attribute_fails():
    from tools.verify_apreal_hidden_videos import inspect_html

    result = inspect_html(
        '<div class="underlay" aria-hidden="true">'
        '<video class="underlay__video" src="/bg.mp4"></video>'
        "</div>"
    )

    assert result["passed"] is False
