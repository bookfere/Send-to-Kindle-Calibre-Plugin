from calibre.gui2.actions import InterfaceAction
from calibre_plugins.send_to_kindle import SendToKindle
from calibre_plugins.send_to_kindle.main import ProcessDialog, pop_alert


load_translations()


class InterfacePlugin(InterfaceAction):
    name = SendToKindle.name
    action_spec = (
        _(name), None, _('Send ebooks to Kindle via email'), None)

    def genesis(self):
        try:
            icon = get_icons('images/icon.png', _(self.name))
        except Exception:
            icon = get_icons('images/icon.png')

        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_dialog)

    def show_dialog(self):
        ebooks = self.get_selected_ebooks()

        if len(ebooks) < 1:
            pop_alert(_('You must choose at least one ebook.'))
            return

        window = ProcessDialog(self.gui, self.qaction.icon(), ebooks)
        window.setModal(True)
        window.setMinimumWidth(500)
        window.setMinimumHeight(420)
        window.setWindowTitle(
            '%s - %s' % (_(self.name), SendToKindle.__version__))
        window.setWindowIcon(self.qaction.icon())
        window.show()

    def get_selected_ebooks(self):
        ebooks = {}
        db = self.gui.current_db
        api = db.new_api
        rows = self.gui.library_view.selectionModel().selectedRows()
        model = self.gui.library_view.model()
        for index, row in enumerate(rows):
            row_number = row.row()
            ebook_id = model.id(row)
            formats = api.formats(ebook_id)
            title = model.title(row_number)
            ebooks[index] = [ebook_id, title, title]
        return ebooks
