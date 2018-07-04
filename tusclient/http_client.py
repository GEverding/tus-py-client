from __future__ import absolute_import

import http.client
import errno
from future.moves.urllib.parse import urlparse

from tusclient.exceptions import TusUploadFailed


class TusHTTPClient(object):

    def __init__(self, uploader):
        url = urlparse(uploader.url)
        if url.scheme == 'https':
            self.handle = http.client.HTTPSConnection(url.hostname, url.port)
        else:
            self.handle = http.client.HTTPConnection(url.hostname, url.port)
        self._url = url


    def get_handle(self):
        return self.handle


    def close(self):
        """
        close request handle and end request session
        """
        self.handle.close()
