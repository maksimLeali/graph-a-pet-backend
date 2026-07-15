"""Allowlist HTML sanitizer for user-authored rich text (WYSIWYG).

Used for shelter `public_story_html`: content is composed in the backoffice
WYSIWYG and shown on the public profile to EXTERNAL users, so unsanitized
input is a stored-XSS vector. We sanitize on write (single trusted boundary)
so every render site can output the stored value directly.

Model (same shape a library like bleach/nh3 uses, kept dependency-free with
the stdlib HTMLParser):
  * only a small allowlist of formatting tags survives;
  * ALL attributes are dropped except a scheme-validated `href` on <a>
    (links get rel/target forced on output) — this alone removes on*
    handlers, style, srcset, etc.;
  * dangerous tags (script/style/svg/iframe/…) are dropped together with
    their text content;
  * any other (unknown/disallowed) tag is unwrapped — its text is kept,
    the tag itself is discarded;
  * comments / PIs / declarations are dropped;
  * output text is re-escaped.

Note: HTMLParser is not a full HTML5 tree builder, so this does not defend
against every exotic mutation-XSS vector the way an html5lib-based sanitizer
would. It is safe for the constrained, attribute-free formatting this field
allows; if the allowlist ever grows (images, tables, inline styles),
switch to `nh3` (Rust/ammonia binding) instead of widening this.
"""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

# formatting tags kept as-is (both the legacy b/i and semantic strong/em)
ALLOWED_TAGS = frozenset({
    "p", "br", "strong", "b", "em", "i", "u", "s", "strike",
    "h2", "h3", "h4", "ul", "ol", "li", "a", "blockquote",
})
# void tags emitted self-closing, never expecting an end tag
VOID_TAGS = frozenset({"br"})
# tags whose *content* is discarded, not just the tag
DANGEROUS_TAGS = frozenset({
    "script", "style", "iframe", "frame", "frameset", "object", "embed",
    "applet", "noscript", "template", "svg", "math", "link", "meta", "base",
    "title", "head", "form", "input", "button", "textarea", "select", "option",
    "canvas", "audio", "video", "source", "track",
})
ALLOWED_URL_SCHEMES = frozenset({"http", "https", "mailto"})

MAX_LENGTH = 20000


def _safe_href(value):
    """Return a safe href string, or None if the URL must be dropped."""
    if not value:
        return None
    # collapse control chars/whitespace that could smuggle a scheme
    cleaned = "".join(ch for ch in value if ord(ch) >= 0x20).strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme:
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            return None
        return cleaned
    # no scheme → relative/anchor link, allowed but must not look like a
    # scheme-relative "//evil.com" or a sneaky "javascript:" without '//'
    if cleaned.startswith("//") or ":" in cleaned.split("/")[0]:
        return None
    return cleaned


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        # depth of currently-open dangerous tags; while > 0 everything is
        # dropped (including nested allowed tags and text)
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if self._skip_depth:
            if tag in DANGEROUS_TAGS and tag not in VOID_TAGS:
                self._skip_depth += 1
            return
        if tag in DANGEROUS_TAGS:
            if tag not in VOID_TAGS:
                self._skip_depth += 1
            return
        if tag not in ALLOWED_TAGS:
            return  # unwrap: keep children/text, drop the tag
        if tag == "a":
            href = _safe_href(dict(attrs).get("href"))
            if href:
                self.out.append(
                    f'<a href="{escape(href, quote=True)}" '
                    'rel="noopener noreferrer nofollow" target="_blank">'
                )
            else:
                self.out.append("<a>")
        elif tag in VOID_TAGS:
            self.out.append(f"<{tag}>")
        else:
            self.out.append(f"<{tag}>")

    def handle_startendtag(self, tag, attrs):
        # e.g. <br/> — treat like a start tag for void elements
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if self._skip_depth:
            if tag in DANGEROUS_TAGS and tag not in VOID_TAGS:
                self._skip_depth -= 1
            return
        if tag in VOID_TAGS:
            return
        if tag in ALLOWED_TAGS:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self.out.append(escape(data, quote=False))

    # comments, declarations, processing instructions → dropped
    def handle_comment(self, data):
        pass

    def handle_decl(self, decl):
        pass

    def handle_pi(self, data):
        pass


def sanitize_html(value):
    """Sanitize a WYSIWYG HTML string to the allowlist above.

    Returns the sanitized string, or None for empty/blank input (so an empty
    editor clears the field rather than storing "")."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    value = value[:MAX_LENGTH]
    parser = _Sanitizer()
    parser.feed(value)
    parser.close()
    result = "".join(parser.out).strip()
    return result or None
