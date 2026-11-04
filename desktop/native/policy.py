"""Small, testable URL policy shared by navigation and the request interceptor."""

from urllib.parse import urlsplit


def same_origin(url: str, origin: str):
    try:
        parsed = urlsplit(url)
        expected = urlsplit(origin)
        return (parsed.scheme, parsed.hostname, parsed.port) == (
            expected.scheme,
            expected.hostname,
            expected.port,
        ) and parsed.netloc == expected.netloc
    except ValueError:
        return False


def resource_allowed(url: str, origin: str):
    return (
        same_origin(url, origin)
        or url.startswith("data:image/")
        or (url.startswith("blob:") and same_origin(url[5:], origin))
    )


def navigation_allowed(url: str, origin: str):
    return same_origin(url, origin) and urlsplit(url).path == "/"


def notice_allowed(url: str, origin: str):
    return same_origin(url, origin) and urlsplit(url).path == "/third-party-notices.txt"


def download_allowed(url: str, origin: str):
    # Draft exports are browser-generated JSON blobs. Server/external downloads
    # are not an alternate means to read arbitrary filesystem paths.
    return url.startswith("blob:") and same_origin(url[5:], origin)
