import http.client
import errno
import logging
from future.moves.urllib.parse import urlparse

from tusclient.exceptions import TusUploadFailed


class TusRequest(object):
    """
    Http Request Abstraction.

    Sets up tus custom http request on instantiation.

    requires argument 'uploader' an instance of tusclient.uploader.Uploader
    on instantiation.

    :Attributes:
        - handle (<http.client.HTTPConnection>)
        - response_headers (dict)
        - file (file):
            The file that is being uploaded.
    """

    def __init__(self, uploader):
        url = urlparse(uploader.url)
        self.handle = uploader.http_client.get_handle()
        logging.info("HTTP Handle %s", self.handle)
        self._url = url
        logging.info("Url: %s", self._url)

        self.response_headers = {}
        self.status_code = None
        self.file = uploader.get_file_stream()
        self.file.seek(uploader.offset)

        self._request_headers = {
            'upload-offset': uploader.offset,
            'Content-Type': 'application/offset+octet-stream'
        }
        self._request_headers.update(uploader.headers)
        self._content_length = uploader.request_length
        self._response = None

    @property
    def response_content(self):
        """
        Return response data
        """
        return self._response.read()

    def perform(self):
        """
        Perform actual request.
        """
        try:
            host = '{}://{}'.format(self._url.scheme, self._url.netloc)
            path = self._url.geturl().replace(host, '', 1)

            self.handle.request("PATCH", path, self.file.read(self._content_length), self._request_headers)
            self._response = self.handle.getresponse()
            self._response.read()
            self.status_code = self._response.status
            logging.info("HTTP Response Cod: %s", self.status_code)
            self.response_headers = {k.lower(): v for k, v in self._response.getheaders()}
        except http.client.HTTPException as e:
            logging.exception("HTTP Upload Failed")
            raise TusUploadFailed(e)
        # wrap connection related errors not raised by the http.client.HTTP(S)Connection
        # as TusUploadFailed exceptions to enable retries
        except OSError as e:
            logging.exception("Unknown Error in HTTP Uploader")
            if e.errno in (errno.EPIPE, errno.ESHUTDOWN, errno.ECONNABORTED, errno.ECONNREFUSED, errno.ECONNRESET):
                raise TusUploadFailed(e)
            raise e
