from ..models import UploadedMedia


class Uploader:
    UPLOADER_NAME = '<Uploader name>'
    SLUG = 'uploader'

    @staticmethod
    def upload(media: UploadedMedia):
        raise NotImplementedError()


from .gfycat import GfycatUploader
from .streamable import StreamableUploader
from .videobin import VideobinUploader

_uploaders_list = [StreamableUploader, GfycatUploader, VideobinUploader]
uploaders = {cls.SLUG: cls for cls in _uploaders_list}
uploader_options = tuple((cls.SLUG, cls.UPLOADER_NAME) for cls in _uploaders_list)
