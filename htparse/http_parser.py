##
# An interface to the nodejs-sourced http-parser library
# Pure Python via ctypes
#
# Blame Steve Work, steve@work.renlabs.com, summer 2019

from ctypes import *
from ctypes.util import find_library
import faulthandler
import _internals

HTTP_DATA_CB_FUNC = CFUNCTYPE(c_int, c_void_p, POINTER(c_char), POINTER(c_size_t))
HTTP_CB_FUNC = CFUNCTYPE(c_int, c_void_p)

_lib = None

def setup_lib():
    """\
    One-time init of C library
    """
    global _lib
    if not _lib:
        for name in [ find_library("http_parser"), "libhttp_parser.so", "libhttp_parser" ]:
            try:
                _lib = cdll.LoadLibrary(name)
            except OSError as e:
                pass
            else:
                break
        if not _lib:
            _lib = cdll.http_parser  # propogate OSError if this fails

        _lib.http_parser_version.argtypes = []
        _lib.http_parser_version.restype = c_ulong

        _lib.http_parser_settings_init.argtypes = [c_void_p]
        _lib.http_parser_settings_init.restype = None

        _lib.http_parser_execute.argtypes = [c_void_p, c_void_p, POINTER(c_char), c_size_t]
        _lib.http_parser_execute.restype = c_size_t

        _lib.http_should_keep_alive.argtypes = [c_void_p]
        _lib.http_should_keep_alive.restype = c_int

        _lib.http_method_str.argtypes = [c_int]
        _lib.http_method_str.restype = c_char_p

        _lib.http_status_str.argtypes = [c_int]
        _lib.http_status_str.restype = c_char_p

        _lib.http_errno_name.argtypes = [c_int]
        _lib.http_errno_name.restype = c_char_p

        _lib.http_errno_description.argtypes = [c_int]
        _lib.http_errno_description.restype = c_char_p

        _lib.http_parser_url_init.argtypes = [c_void_p]
        _lib.http_parser_url_init.restype = None

        _lib.http_parser_parse_url.argtypes = [POINTER(c_char), c_size_t, c_int, c_void_p]
        _lib.http_parser_parse_url.restype = c_int

        _lib.http_parser_pause.argtypes = [c_void_p, c_int]
        _lib.http_parser_pause.restype = None

        _lib.http_body_is_final.argtypes = [c_void_p]
        _lib.http_body_is_final.restype = c_int

        _lib.http_parser_set_max_header_size.argtypes = [c_int]
        _lib.http_parser_set_max_header_size.restype = None

        return _lib

class HttpParserSettings(Structure):
    """\
    Instance of nginx http-parser http_parser_settings struct.
    """
    _fields_ = [
            ("on_message_begin", c_void_p),
            ("on_url", c_void_p),
            ("on_status", c_void_p),
            ("on_header_field", c_void_p),
            ("on_header_value", c_void_p),
            ("on_headers_complete", c_void_p),
            ("on_body", c_void_p),
            ("on_message_complete", c_void_p),
            ("on_chunk_header", c_void_p),
            ("on_chunk_complete", c_void_p)]
    _lib = None

    @classmethod
    def setup_class(cls):
        """\
        Find and load library, just once
        """
        if not cls._lib:
            cls._lib = setup_lib()

    def __init__(self):
        super().__init__()
        self.setup_class()
        self._lib.http_parser_settings_init(by_ref(self))


# Methods, parallel to http_parser.h
HTTP_DELETE         = 0
HTTP_GET            = 1
HTTP_HEAD           = 2
HTTP_POST           = 3
HTTP_PUT            = 4
HTTP_CONNECT        = 5
HTTP_OPTIONS        = 6
HTTP_TRACE          = 7
HTTP_COPY           = 8
HTTP_LOCK           = 9
HTTP_MKCOL          = 10
HTTP_MOVE           = 11
HTTP_PROPFIND       = 12
HTTP_PROPPATCH      = 13
HTTP_SEARCH         = 14
HTTP_UNLOCK         = 15
HTTP_BIND           = 16
HTTP_REBIND         = 17
HTTP_UNBIND         = 18
HTTP_ACL            = 19
HTTP_REPORT         = 20
HTTP_MKACTIVITY     = 21
HTTP_CHECKOUT       = 22
HTTP_MERGE          = 23
HTTP_MSEARCH        = 24
HTTP_NOTIFY         = 25
HTTP_SUBSCRIBE      = 26
HTTP_UNSUBSCRIBE    = 27
HTTP_PATCH          = 28
HTTP_PURGE          = 29
HTTP_MKCALENDAR     = 30
HTTP_LINK           = 31
HTTP_UNLINK         = 32
HTTP_SOURCE         = 33

# Types, parallel to http_parser.h
HTTP_REQUEST    = 0
HTTP_RESPONSE   = 1
HTTP_BOTH       = 2

# Flags, parallel to http_parser.h
F_CHUNKED               = 1 << 0
F_CONNECTION_KEEP_ALIVE = 1 << 1
F_CONNECTION_CLOSE      = 1 << 2
F_CONNECTION_UPGRADE    = 1 << 3
F_TRAILING              = 1 << 4
F_UPGRADE               = 1 << 5
F_SKIPBODY              = 1 << 6
F_CONTENTLENGTH         = 1 << 7

class HttpParser(Structure):
    """\
    Instance of the nginx http-parser library http_parser struct,
    wrapped up with associated http-parser library calls.
    """
    _fields_ = [
        ("type", c_uint, 2),
        ("flags", c_uint, 8),
        ("state", c_uint, 7),
        ("header_state", c_uint, 7),
        ("index", c_uint, 7),
        ("lenient_http_headers", c_uint, 1),
        ("nread", c_uint),
        ("content_length", c_uint),
        ("http_major", c_ushort),
        ("http_minor", c_ushort),
        ("status_code", c_uint, 16),
        ("method", c_uint, 8),
        ("http_errno", c_uint, 7),
        ("upgrade", c_uint, 1),
        ("data", c_void_p)]
    _lib = None
    
    @classmethod
    def setup_class(cls):
        """\
        Find and load library, just once
        """
        if not cls._lib:
            cls._lib = setup_lib()

    @classmethod
    def version(cls):
        cls.setup_class()
        return cls._lib.http_parser_version()

    
    def __init__(self, parser_type):
        """\
        wraps http_parser_init
        """
        super().__init__()
        self.setup_class()
        self._lib.http_parser_init(by_ref(self), parser_type)

    def execute(self, settings, data, length):
        """\
        wraps http_parser_execute
        """
        return self._lib.http_parser_execute(by_ref(self), by_ref(settings), by_ref(data), length)

    def pause(self, paused):
        """\
        wraps http_parser_pause
        """
        self._lib.http_parser_pause(by_ref(self), paused)

    def http_body_is_final(self):
        """\
        wraps http_body_is_final
        """
        return self._lib.http_body_is_final(by_ref(self))


UF_SCHEMA       = 0
UF_HOST         = 1
UF_PORT         = 2
UF_PATH         = 3
UF_QUERY        = 4
UF_FRAGMENT     = 5
UF_USERINFO     = 6
UF_MAX          = 7

class OffLen(Structure):
    _fields_ = [
        ("off", c_ushort),
        ("len", c_ushort)]

class HttpParserUrl(Structure):
    """\
    Instance of http_parser_url, wrapped with
    associated http-parser library calls
    """
    _fields_ = [
        ("field_set", c_ushort),
        ("port", c_ushort),
        ("field_data", OffLen * UF_MAX)]

if __name__ == '__main__':
    v = HttpParser.version()
    major = (v >> 16) & 255
    minor = (v >> 8) & 255
    patch = v & 255
    print("http_parser version", major, minor, patch)
