from calibre.customize import InterfaceActionBase
from calibre_plugins.send_to_kindle.utils import _z


__license__ = 'GPL v3'
__copyright__ = '2023, BookFere <bookfere@gmail.com>'
__docformat__ = 'restructuredtext en'

load_translations()


class SendToKindle(InterfaceActionBase):
    name = _z('Send to Kindle')
    description = _(
        'A calibre plugin to send your ebook to Kindle with a desired title.')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'bookfere.com'
    version = (1, 1, 1)
    __version__ = 'v' + '.'.join(map(str, version))
    minimum_calibre_version = (2, 0, 0)

    actual_plugin = 'calibre_plugins.send_to_kindle.ui:InterfacePlugin'

    def is_customizable(self):
        return False
