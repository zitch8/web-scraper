from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from posixpath import normpath

def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    # Lowercase scheme and hostname
    scheme = parsed.scheme.lower()
    netloc = parsed.hostname.lower() if parsed.hostname else ""

    # Include port if it's non-default
    if parsed.port and not (
        (scheme == "http" and parsed.port == 80) or
        (scheme == "https" and parsed.port == 443)
    ):
        netloc += f":{parsed.port}"

    # Remove duplicate slashes and resolve . and ..
    path = normpath(parsed.path)
    if not path.startswith("/"):
        path = "/" + path

    # Sort query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    query = urlencode(sorted(query_params))

    # Remove fragment
    fragment = ""

    # Build normalized URL
    return urlunparse((scheme, netloc, path, "", query, fragment))
