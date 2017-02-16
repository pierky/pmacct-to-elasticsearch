# This code is Copyright 2014-2017 by Pier Carlo Chiodi.
# See full license in LICENSE file.

try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
