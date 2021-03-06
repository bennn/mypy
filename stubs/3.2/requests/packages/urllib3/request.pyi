# Stubs for requests.packages.urllib3.request (Python 3.4)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Undefined, Any

class RequestMethods:
    headers = Undefined(Any)
    def __init__(self, headers=None): pass
    def urlopen(self, method, url, body=None, headers=None, encode_multipart=True, multipart_boundary=None, **kw): pass
    def request(self, method, url, fields=None, headers=None, **urlopen_kw): pass
    def request_encode_url(self, method, url, fields=None, **urlopen_kw): pass
    def request_encode_body(self, method, url, fields=None, headers=None, encode_multipart=True, multipart_boundary=None, **urlopen_kw): pass
