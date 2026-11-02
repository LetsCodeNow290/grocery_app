"""Small JSON-LD importer. Remote images, scripts, and linked contexts are never fetched."""
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT = 10
TOTAL_TIMEOUT = 25
# Avoid transition mechanisms that can embed an otherwise private IPv4 address.
TRANSITION_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    '64:ff9b::/96', '64:ff9b:1::/48', '2002::/16', '2001::/32'))


class RecipeImportError(ValueError):
    """An expected, user-readable import failure."""


def _public_address(value):
    address = ipaddress.ip_address(value)
    if not address.is_global or address.is_multicast or address.is_reserved:
        return False
    if address.version == 6:
        if address.is_site_local or address.ipv4_mapped or any(address in network for network in TRANSITION_NETWORKS):
            return False
    if address.version == 4 and address in ipaddress.ip_network('192.0.0.0/24'):
        return False  # Special protocol assignments; consistent on Python 3.12–3.14.
    return str(address) != '168.63.129.16'  # Azure platform/metadata service.


def _destination(url):
    if len(url) > 2048 or '\\' in url or any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise RecipeImportError('Enter a valid public HTTP or HTTPS recipe URL.')
    try:
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https') or not parts.hostname:
            raise ValueError
        if parts.username is not None or parts.password is not None:
            raise ValueError
        host = parts.hostname.encode('idna').decode('ascii')
        port = parts.port if parts.port is not None else (443 if parts.scheme == 'https' else 80)
        if port != (443 if parts.scheme == 'https' else 80) or '%' in host:
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if not re.fullmatch(r'[a-zA-Z0-9.-]+', host):
                raise ValueError
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM,
                                       proto=socket.IPPROTO_TCP)
        if not addresses or any(
                family not in (socket.AF_INET, socket.AF_INET6) or not _public_address(addr[0])
                for family, _, _, _, addr in addresses):
            raise RecipeImportError('Only public websites are allowed; private or special network addresses are blocked.')
    except (ValueError, UnicodeError, OSError) as error:
        if isinstance(error, RecipeImportError):
            raise
        raise RecipeImportError('The URL is invalid or its public address could not be resolved.') from error
    authority = f'[{host}]' if ':' in host else host
    normalized = urlunsplit((parts.scheme, authority, parts.path or '/', parts.query, ''))
    target = quote(urlunsplit(('', '', parts.path or '/', parts.query, '')),
                   safe="/%?=&:+,;@!$'()*~-._")
    return normalized, host, port, target, addresses


def _connect(addresses, deadline):
    """Connect to already validated DNS results, with no second DNS lookup."""
    def connect(address, timeout=TIMEOUT, source_address=None):
        last_error = None
        for family, socktype, proto, _, sockaddr in addresses:
            sock = socket.socket(family, socktype, proto)
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                sock.settimeout(min(timeout, remaining))
                sock.connect(sockaddr)
                return sock
            except OSError as error:
                last_error = error
                sock.close()
        raise last_error or OSError('No reachable address')
    return connect


def fetch_html(url):
    """Fetch bounded HTML, checking and pinning each redirect destination."""
    deadline = time.monotonic() + TOTAL_TIMEOUT
    try:
        for hop in range(MAX_REDIRECTS + 1):
            url, host, port, target, addresses = _destination(url)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            if url.startswith('https:'):
                connection = http.client.HTTPSConnection(
                    host, port, timeout=min(TIMEOUT, remaining), context=ssl.create_default_context())
            else:
                connection = http.client.HTTPConnection(host, port, timeout=min(TIMEOUT, remaining))
            # http.client uses this hook for TCP; HTTPS still checks the original hostname.
            connection._create_connection = _connect(addresses, deadline)
            try:
                connection.request('GET', target, headers={
                    'User-Agent': 'GroceryAppRecipeImporter/1.0',
                    'Accept': 'text/html, application/xhtml+xml',
                    'Accept-Encoding': 'identity',
                })
                with connection.getresponse() as response:
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.getheader('Location')
                        if not location or hop == MAX_REDIRECTS:
                            raise RecipeImportError('The website returned a missing or excessive redirect.')
                        try:
                            next_url = urljoin(url, location)
                            next_scheme = urlsplit(next_url).scheme
                        except ValueError:
                            raise RecipeImportError('The website returned an invalid redirect URL.') from None
                        if url.startswith('https:') and next_scheme != 'https':
                            raise RecipeImportError('An insecure redirect was blocked. Use the final HTTPS recipe URL.')
                        url = next_url
                        continue
                    if response.status in (401, 403, 429):
                        raise RecipeImportError(
                            f'The website blocked automatic downloading (HTTP {response.status}). '
                            'Open the page in your browser, then use Copy from browser below.')
                    if response.status != 200:
                        raise RecipeImportError(f'The website returned HTTP {response.status}. Try another public recipe URL.')
                    if response.headers.get_content_type() not in ('text/html', 'application/xhtml+xml'):
                        raise RecipeImportError('The URL must return an HTML recipe page.')
                    if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                        raise RecipeImportError('The website returned unsupported compressed content.')
                    if response.length is not None and response.length > MAX_BYTES:
                        raise RecipeImportError('The page is too large to import (maximum 2 MB).')
                    body = bytearray()
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        if connection.sock is not None:
                            connection.sock.settimeout(min(TIMEOUT, remaining))
                        chunk = response.read1(min(65536, MAX_BYTES + 1 - len(body)))
                        if not chunk:
                            break
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise RecipeImportError('The page is too large to import (maximum 2 MB).')
                    encoding = response.headers.get_content_charset() or 'utf-8'
                    try:
                        return body.decode(encoding, errors='replace'), url
                    except LookupError:
                        raise RecipeImportError('The website uses an unsupported text encoding.') from None
            finally:
                connection.close()
    except (OSError, http.client.HTTPException) as error:
        raise RecipeImportError('The website could not be downloaded securely. It may be unavailable or blocking imports.') from error


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            kind = dict(attrs).get('type', '').split(';')[0].strip().lower()
            self.current = [] if kind == 'application/ld+json' else None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.scripts.append(''.join(self.current))
            self.current = None


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ('br', 'p', 'li', 'div'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('p', 'li', 'div'):
            self.parts.append('\n')


def _text(value):
    if not isinstance(value, str):
        return ''
    parser = _Text()
    parser.feed(value)
    return '\n'.join(line.strip() for line in ''.join(parser.parts).splitlines() if line.strip())


def _instructions(value):
    if isinstance(value, str):
        return _text(value)
    if isinstance(value, list):
        return '\n\n'.join(filter(None, (_instructions(item) for item in value)))
    if isinstance(value, dict):
        children = value.get('itemListElement')
        if children:
            return '\n\n'.join(filter(None, (_text(value.get('name')), _instructions(children))))
        return _text(value.get('text') or value.get('name'))
    return ''


def _recipes(value):
    # Iterative traversal also handles @graph and embedded mainEntity objects.
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(reversed(node))
        elif isinstance(node, dict):
            kinds = node.get('@type', [])
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if isinstance(kinds, list) and any(
                    isinstance(kind, str) and kind.rstrip('/').split('/')[-1] == 'Recipe' for kind in kinds):
                yield node
            stack.extend(reversed(list(node.values())))


def extract_recipe(html):
    scripts = _Scripts()
    if html.lstrip('\ufeff \r\n\t').startswith(('{', '[')):
        scripts.scripts.append(html.lstrip('\ufeff'))
    else:
        scripts.feed(html)
    try:
        for script in scripts.scripts:
            try:
                data = json.loads(script.lstrip('\ufeff'))
            except (ValueError, RecursionError):
                continue
            for recipe in _recipes(data):
                name = _text(recipe.get('name'))
                raw = recipe.get('recipeIngredient', [])
                raw = [raw] if isinstance(raw, str) else raw
                if not isinstance(raw, list):
                    continue
                # Objects are kept verbatim instead of losing unsupported quantity/unit details.
                ingredients = '\n'.join(_text(line) if isinstance(line, str) else
                                         json.dumps(line, ensure_ascii=False) for line in raw)
                instructions = _instructions(recipe.get('recipeInstructions'))
                if name and ingredients.strip() and instructions:
                    if max(len(ingredients), len(instructions)) > 100000:
                        raise RecipeImportError('The recipe text is too large to review. Try another URL.')
                    return {'recipe_name': name, 'ingredient_text': ingredients,
                            'recipe_instructions': instructions}
    except RecursionError:
        raise RecipeImportError('The website has overly nested recipe data. Try another URL.') from None
    raise RecipeImportError('No complete Recipe JSON-LD data was found. Try a direct recipe page with a name, ingredients, and instructions, or enter the recipe manually.')


def import_url(url):
    html, source = fetch_html(url)
    return {**extract_recipe(html), 'source_url': source}


def extract_browser_content(content):
    """Read user-supplied content only: never follow a URL, script, or context."""
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise RecipeImportError('The supplied content is too large (maximum 2 MB).')
    stripped = content.lstrip('\ufeff \r\n\t')
    if stripped.startswith(('{', '[')) or re.search(
            r'<(?:!doctype\b|html\b|head\b|body\b|script\b)', stripped, re.IGNORECASE):
        return extract_recipe(stripped)
    if len(content) > 100000:
        raise RecipeImportError('Copy just the recipe text (maximum 100,000 characters).')
    # Heading recognition is deliberately conservative. All copied text is kept
    # in notes, including preambles, unrecognized sections, and quantity labels.
    lines = content.strip().splitlines()
    headings = [line.strip().rstrip(':').strip().casefold() for line in lines]
    ingredient_heading = next((i for i, value in enumerate(headings) if value == 'ingredients'), None)
    instruction_heading = next((i for i, value in enumerate(headings)
                                if value in ('instructions', 'directions', 'method', 'preparation')
                                and ingredient_heading is not None and i > ingredient_heading), None)
    draft = {'recipe_name': '', 'ingredient_text': '',
             'recipe_instructions': content.strip(), 'comments': content.strip()}
    if ingredient_heading is not None and instruction_heading is not None:
        titles = [line.strip() for line in lines[:ingredient_heading] if line.strip()]
        if titles and len(titles[0]) <= 100:
            draft['recipe_name'] = titles[0]
        draft['ingredient_text'] = '\n'.join(lines[ingredient_heading + 1:instruction_heading]).strip()
        draft['recipe_instructions'] = '\n'.join(lines[instruction_heading + 1:]).strip()
    return draft
