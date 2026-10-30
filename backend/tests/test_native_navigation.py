"""Window creation is a security boundary: deny before allocating any widget."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from desktop.native.application import open_notice_request  # noqa: E402
from desktop.native.policy import notice_allowed  # noqa: E402

ORIGIN = "http://127.0.0.1:32187"


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/",
        "file:///etc/passwd",
        "about:blank",
        ORIGIN + "/",
        ORIGIN + "/api/notes",
        ORIGIN + "/third-party-notices.txt/extra",
        "http://127.0.0.1:32188/third-party-notices.txt",
        "http://localhost:32187/third-party-notices.txt",
        "http://user@127.0.0.1:32187/third-party-notices.txt",
        "http://127.0.0.1:32187@evil.invalid/third-party-notices.txt",
    ],
)
def test_denied_destinations_do_not_create_a_blank_window(url):
    request = Mock()
    request.isUserInitiated.return_value = True
    request.requestedUrl.return_value.toString.return_value = url
    make_page = Mock()
    assert not notice_allowed(url, ORIGIN)
    assert not open_notice_request(request, ORIGIN, make_page)
    make_page.assert_not_called()
    request.openIn.assert_not_called()


def test_automatic_popup_cannot_open_even_the_notices_page():
    request = Mock()
    request.isUserInitiated.return_value = False
    request.requestedUrl.return_value.toString.return_value = (
        ORIGIN + "/third-party-notices.txt"
    )
    make_page = Mock()
    assert not open_notice_request(request, ORIGIN, make_page)
    make_page.assert_not_called()
    request.openIn.assert_not_called()


def test_user_notices_request_opens_only_the_approved_page():
    request = Mock()
    request.isUserInitiated.return_value = True
    request.requestedUrl.return_value.toString.return_value = (
        ORIGIN + "/third-party-notices.txt"
    )
    make_page = Mock()
    assert open_notice_request(request, ORIGIN, make_page)
    make_page.assert_called_once_with()
    request.openIn.assert_called_once_with(make_page.return_value)
