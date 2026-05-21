"""Minimal requests-compatible shim for test environments missing external `requests` package."""
import json
import urllib.request
import urllib.parse
import http.cookiejar


class Response:
    def __init__(self, status_code: int, text: str, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):
        return json.loads(self.text) if self.text else {}


class Session:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(self, method: str, url: str, json=None):
        data = None
        headers = {}
        if json is not None:
            data = bytes(__import__('json').dumps(json), 'utf-8')
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener.open(req) as resp:
                body = resp.read().decode('utf-8')
                return Response(resp.getcode(), body, dict(resp.headers))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8') if e.fp else ''
            return Response(e.code, body, dict(e.headers or {}))

    def get(self, url, **kwargs):
        return self.request('GET', url, json=kwargs.get('json'))

    def post(self, url, json=None, **kwargs):
        return self.request('POST', url, json=json)

    def put(self, url, json=None, **kwargs):
        return self.request('PUT', url, json=json)


def get(url, **kwargs):
    return Session().get(url, **kwargs)


def post(url, json=None, **kwargs):
    return Session().post(url, json=json, **kwargs)


def put(url, json=None, **kwargs):
    return Session().put(url, json=json, **kwargs)
