"""Narrow static-HTML favicon linkage; never rewrite or synthesize business DOM."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import PurePosixPath
import re
from urllib.parse import unquote, urljoin, urlsplit


class HeadReferences(HTMLParser):
    # HTMLParser otherwise tokenizes apparent tags inside title RCDATA. For
    # boundary detection, treating title like raw text is sufficient: original
    # bytes are retained and its character references are never rewritten.
    CDATA_CONTENT_ELEMENTS = ("script", "style", "title")

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.source = text
        # HTMLParser counts only LF characters for getpos(), not Python's wider
        # splitlines() set (CR, NEL and Unicode line/paragraph separators).
        self.offsets = [0, *(index + 1 for index, character in enumerate(text) if character == "\n")]
        self.heads = self.ends = self.templates = 0
        self.in_head = False
        self.invalid = False
        self.ambiguous = False
        self.base = False
        self.raw_text = None
        self.close_offset = None
        self.links = []
        self.owned = []

    def handle_starttag(self, tag, attrs):
        if self.raw_text:
            self.invalid = True
            return
        attributes = dict(attrs)
        if self.heads == 0 and tag not in {"html", "head"}:
            self.invalid = True
        if self.in_head and not self.templates and tag not in {"head", "title", "base", "link", "meta", "style", "script", "noscript", "template"}:
            self.invalid = True
        if self.in_head and tag in {"base", "link"} and len(attributes) != len(attrs):
            self.ambiguous = True
        if tag == "head":
            self.heads += 1
            self.in_head = True
        elif tag == "body" and self.in_head:
            self.invalid = True
        elif self.in_head and tag in {"template", "noscript"}:
            # These require additional browser insertion modes or scripting
            # state. They are outside the deliberately narrow supported head.
            self.invalid = True
            self.templates += 1
        elif self.in_head and not self.templates:
            if tag in {"title", "style", "script"}:
                self.raw_text = tag
            if tag == "base" and attributes.get("href") is not None:
                self.base = True
            if tag == "link":
                if attributes.get("data-autonomous-company-icon") is not None:
                    self.owned.append(attributes)
                if "icon" in (attributes.get("rel") or "").lower().split():
                    self.links.append(attributes)

    def handle_startendtag(self, tag, attrs):
        if tag in {"head", "template", "noscript", *self.CDATA_CONTENT_ELEMENTS}:
            self.invalid = True
        self.handle_starttag(tag, attrs)
        if tag in {"head", "template", "noscript"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.in_head or self.raw_text or tag == "head":
            line, column = self.getpos()
            offset = self.offsets[line - 1] + column
            end = self.source.find(">", offset)
            token = self.source[offset:end + 1] if end >= 0 else ""
            # HTMLParser accepts spellings such as </ head> and </ script>
            # which browsers do not use to close these elements. A conventional
            # exact end token is the only supported boundary.
            if not re.fullmatch(r"</" + re.escape(tag) + r"[ \t\n\r\f]*>", token, re.IGNORECASE):
                self.invalid = True
        if self.raw_text:
            if tag == self.raw_text:
                self.raw_text = None
            else:
                self.invalid = True
            return
        if self.heads == 0:
            self.invalid = True
        if self.in_head and not self.templates and tag != "head":
            # In particular </br>, </body> and </html> may end the browser head
            # before our closing token. Unknown end tags are also fail-closed.
            self.invalid = True
            return
        if tag in {"template", "noscript"} and self.in_head:
            self.templates = max(0, self.templates - 1)
        elif tag == "head":
            self.ends += 1
            if not self.in_head or self.templates:
                self.invalid = True
            self.in_head = False
            line, column = self.getpos()
            self.close_offset = self.offsets[line - 1] + column

    def handle_data(self, data):
        if self.raw_text == "script" and "<" in data:
            # Script escaped/double-escaped tokenizer states differ from this
            # stdlib parser. Conservatively exclude all script less-than text
            # instead of attempting a complete HTML5 script-state parser.
            self.invalid = True
        if self.getpos() == (1, 0):
            data = data.removeprefix("\ufeff")
        non_whitespace = data.strip(" \t\n\r\f")
        if self.heads == 0 and non_whitespace:
            self.invalid = True
        if self.in_head and not self.templates and not self.raw_text and non_whitespace:
            self.invalid = True


def inspect_reference(project, profile, icon, *, write=False):
    """Return evidence for the entry's static favicon; only explicit writes insert.

    A source-level reference is not a claim about later JavaScript changes or
    browser icon selection. Existing usable custom favicon choices are retained.
    """
    from product_media import atomic_bytes, digest, read_bytes, safe_path, validate_icon

    result = {"state": "unsupported", "reason": "static_html_required", "unified": None, "managed": False}
    if profile.get("type") != "static":
        if profile.get("type") == "none":
            result.update(state="not_applicable", reason="nonvisual_product")
        elif profile.get("type") == "node":
            result.update(state="unconfirmed", reason="dynamic_entry_reference_unconfirmed")
        return result
    entry = profile.get("entry", "/")
    relative = entry.lstrip("/")
    if not relative or relative.endswith("/"):
        relative += "index.html"
    if PurePosixPath(relative).suffix.lower() not in {".html", ".htm"}:
        return result
    try:
        web_root = safe_path(project, profile.get("webRoot", "."))
        target = safe_path(web_root, relative)
        raw = read_bytes(target, 2 * 1024 * 1024)
        text = raw.decode("utf-8")
        result.update(entryPath=target.relative_to(project).as_posix(), entrySha256=digest(raw))
        parser = HeadReferences(text)
        parser.feed(text)
        parser.close()
        if parser.heads != 1 or parser.ends != 1 or parser.invalid or parser.raw_text or parser.close_offset is None:
            result.update(state="unsupported", reason="explicit_html_head_required")
            return result
        if parser.base:
            result.update(state="unconfirmed", reason="base_url_reference_unconfirmed")
            return result
        if parser.ambiguous:
            result.update(state="unconfirmed", reason="ambiguous_head_attributes")
            return result
        canonical_path = safe_path(web_root, "autonomous-company-icon.svg")
        canonical_valid = False
        try:
            canonical_valid = digest(validate_icon(read_bytes(canonical_path, 32 * 1024))) == icon.get("sha256")
        except (OSError, ValueError):
            pass
        usable = []
        unconfirmed = False
        for link in parser.links:
            href = link.get("href") or ""
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not href or "\\" in href or "\x00" in href:
                if href and (parsed.scheme in {"http", "https", "data"} or parsed.netloc):
                    unconfirmed = True
                continue
            resolved = urlsplit(urljoin("http://product.invalid" + entry, href))
            resolved_path = unquote(resolved.path).lstrip("/")
            try:
                path = safe_path(web_root, resolved_path)
                value = read_bytes(path, 1024 * 1024)
                valid = False
                if path.suffix.lower() == ".svg":
                    validate_icon(value)
                    valid = True
                elif path.suffix.lower() in {".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}:
                    # The static-SVG validator cannot prove an arbitrary raster
                    # favicon renders correctly. Preserve the user's choice but
                    # do not call a magic-byte/header sniff "validated".
                    unconfirmed = True
                if valid:
                    usable.append({"href": href, "unified": digest(value) == icon.get("sha256"),
                                   "managed": link.get("data-autonomous-company-icon") == "v1", "conditional": bool(link.get("media"))})
            except (OSError, ValueError):
                continue
        if usable:
            if any(not row["unified"] for row in usable):
                selected = next(row for row in usable if not row["unified"])
                result.update(state="preserved", reason="user_favicon_preserved", href=selected["href"], unified=False)
            elif unconfirmed or any(row["conditional"] for row in usable):
                result.update(state="unconfirmed", reason="multiple_or_conditional_icon_choices", href=usable[0]["href"])
            else:
                result.update(state="linked", reason=None, href=usable[0]["href"], unified=True,
                              managed=any(row["managed"] for row in usable))
            return result
        if unconfirmed:
            result.update(state="unconfirmed", reason="existing_icon_reference_unconfirmed")
            return result
        if parser.owned:
            result.update(state="conflict", reason="owned_reference_modified")
            return result
        if not canonical_valid or icon.get("publicationStatus") not in {"published", "existing_valid"}:
            result.update(state="conflict", reason="canonical_icon_unavailable")
            return result
        result.update(state="missing", reason="icon_reference_missing")
        if not write:
            return result
        # Insert one metadata link at a parsed head boundary, preserving every
        # original byte and all existing user-authored references/content.
        newline = "\r\n" if "\r\n" in text else "\n"
        href = "../" * (len(PurePosixPath(relative).parts) - 1) + "autonomous-company-icon.svg"
        link = f'<link rel="icon" type="image/svg+xml" href="{href}" data-autonomous-company-icon="v1">'
        offset = parser.close_offset
        updated = (text[:offset] + newline + link + newline + text[offset:]).encode("utf-8")
        if read_bytes(target, 2 * 1024 * 1024) != raw:
            result.update(state="failed", reason="entry_changed_during_icon_linkage")
            return result
        atomic_bytes(target, updated)
        result.update(state="inserted", reason=None, href=href, unified=True, managed=True,
                      entrySha256=digest(updated))
    except UnicodeError:
        result.update(state="unsupported", reason="entry_encoding_unsupported")
    except (OSError, ValueError, TypeError):
        result.update(state="failed", reason="icon_reference_unavailable")
    return result
