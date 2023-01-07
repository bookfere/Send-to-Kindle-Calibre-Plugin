from calibre.customize import InterfaceActionBase


__license__ = 'GPL v3'
__copyright__ = '2022, BookFere <bookfere@gmail.com>'
__docformat__ = 'restructuredtext en'

load_translations()


class SendToKindle(InterfaceActionBase):
    name = 'Send to Kindle'
    title = _('Send to Kindle')
    description = _(
        'A calibre plugin for you to send ebook with the desired title.'
    )
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'bookfere.com'
    version = (1, 0, 0)
    minimum_calibre_version = (1, 0, 0)

    actual_plugin = 'calibre_plugins.send_to_kindle.ui:InterfacePlugin'

    @classmethod
    def get_version(cls):
        return 'v' + '.'.join(map(str, cls.version))

    def is_customizable(self):
        return False
