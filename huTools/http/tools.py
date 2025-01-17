#!/usr/bin/env python
# encoding: utf-8
"""
tools.py - various helpers for HTTP access

Created by Maximillian Dornseif on 2010-10-24.
Copyright (c) 2010, 2011 HUDORA. All rights reserved.
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import map
from builtins import chr
from builtins import str
from builtins import range
from past.builtins import basestring
import base64
from . import poster_encode
import urllib.request, urllib.parse, urllib.error
import urllib.parse


# quoting based on
# http://svn.python.org/view/python/branches/release27-maint/Lib/urllib.py?view=markup&pathrev=82940
# by Matt Giuca
always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789' '_.-')
_safe_map = {}
for i, c in zip(range(256), [chr(x) for x in range(256)]):
    _safe_map[c] = c if (i < 128 and c in always_safe) else ('%%%02X' % i)
_safe_quoters = {}


def quote(s, safe='/', encoding=None, errors=None):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted.

    RFC 2396 Uniform Resource Identifiers (URI): Generic Syntax lists
    the following reserved characters.

    reserved    = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
                  "$" | ","

    Each of these characters is reserved in some component of a URL,
    but not necessarily in all of them.

    By default, the quote function is intended for quoting the path
    section of a URL.  Thus, it will not encode '/'.  This character
    is reserved, but in typical usage the quote function is being
    called on a path where the existing slash characters are used as
    reserved characters.

    string and safe may be either str or unicode objects.

    The optional encoding and errors parameters specify how to deal with the
    non-ASCII characters, as accepted by the unicode.encode method.
    By default, encoding='utf-8' (characters are encoded with UTF-8), and
    errors='strict' (unsupported characters raise a UnicodeEncodeError).
    """
    # fastpath
    if not s:
        return s

    if encoding is not None or isinstance(s, str):
        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'strict'
        s = s.encode(encoding, errors)
    if isinstance(safe, str):
        # Normalize 'safe' by converting to str and removing non-ASCII chars
        safe = safe.encode('ascii', 'ignore')

    cachekey = (safe, always_safe)
    try:
        (quoter, safe) = _safe_quoters[cachekey]
    except KeyError:
        safe_map = _safe_map.copy()
        safe_map.update([(c, c) for c in safe])
        quoter = safe_map.__getitem__
        safe = always_safe + safe
        _safe_quoters[cachekey] = (quoter, safe)
    if not s.rstrip(safe):
        return s
    return ''.join(map(quoter, s))


def quote_plus(s, safe='', encoding=None, errors=None):
    """Quote the query fragment of a URL; replacing ' ' with '+'"""
    if ' ' in s:
        s = quote(s, safe + ' ', encoding, errors)
        return s.replace(' ', '+')
    return quote(s, safe, encoding, errors)


def urlencode(query):
    """Encode a sequence of two-element tuples or dictionary into a URL query string.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query, 'items'):
        # mapping objects
        query = list(query.items())
    l = []
    for k, v in query:
        k = quote_plus(k)
        if isinstance(v, basestring):
            v = quote_plus(v)
            l.append(k + '=' + v)
        else:
            v = quote_plus(str(v))
            l.append(k + '=' + v)
    return '&'.join(l)


def add_query(url, params):
    """
    Add GET parameters to a given URL

    >>> add_query('/sicrit/', {'passphrase': 'fiftyseveneleven'})
    '/sicrit/?passphrase=fiftyseveneleven'
    >>> add_query('/sicrit/test.html?hello=world', {'passphrase': 'fiftyseveneleven'})
    '/sicrit/test.html?hello=world&passphrase=fiftyseveneleven'
    >>> add_query('/sicrit/test.html?hello=world', {'passphrase': ['fiftyseven', 'eleven']})
    '/sicrit/test.html?hello=world&passphrase=fiftyseven&passphrase=eleven'
    """

    url_parts = list(urllib.parse.urlparse(url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.parse.urlencode(query, doseq=1)
    return urllib.parse.urlunparse(url_parts)


def prepare_headers(url, content='', method='GET', credentials=None, headers=None, multipart=False, ua='',
                    timeout=50, caching=None):
    """Prepares a request, returns (url, method, content, headers, timeout)"""

    myheaders = {'Accept-Encoding': 'gzip',
                 'User-Agent': '%s/huTools.http (gzip)' % ua}
    if headers:
        myheaders.update(headers)
    if method in ['POST', 'PUT']:
        if hasattr(content, 'items'):
            # we assume content is a dict which needs to be encoded
            # decide to use multipart/form-data encoding or application/x-www-form-urlencoded
            for val in list(content.values()):
                if hasattr(val, 'read'):  # file() or StringIO()
                    multipart = True
                    break
            if multipart:
                datagen, mp_headers = poster_encode.multipart_encode(content)
                myheaders.update(mp_headers)
                content = "".join(datagen)
            else:
                myheaders.update({'Content-Type': 'application/x-www-form-urlencoded'})
                content = urlencode(content)
    else:
        # url parmater encoding
        if hasattr(content, 'items'):
            scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
            qdict = urllib.parse.parse_qs(query)
            # ugly Unicode issues, see http://bugs.python.org/issue1712522
            qdict.update(content)
            query = urlencode(qdict)
            url = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
            content = ''
    # convert all header values to strings (what about unicode?)
    for key, val in list(myheaders.items()):
        myheaders[key] = str(val)
    # add authentication
    if credentials and not 'Authorization' in list(myheaders.keys()):
        myheaders["Authorization"] = 'Basic %s' % base64.b64encode(credentials)
    return url, method, content, myheaders, timeout, caching
