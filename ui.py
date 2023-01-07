from calibre.gui2.actions import InterfaceAction
from calibre_plugins.send_to_kindle import SendToKindle
from calibre_plugins.send_to_kindle.main import ProcessDialog, pop_alert


load_translations()


class InterfacePlugin(InterfaceAction):
    name = _(SendToKindle.title)
    action_spec = (
        name, None, _('Send ebooks to Kindle via email'), None
    )

    def genesis(self):
        try:
            icon = get_icons('images/icon.png', name)
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
        window.setMinimumWidth(400)
        window.setMinimumHeight(400)
        window.setWindowTitle(self.name + ' - ' + SendToKindle.get_version())
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
            id = model.id(row)
            print(id)
            fmts = api.formats(id)
            ebooks[index] = [
                model.title(row_number),
                dict(zip(
                    map(lambda fmt: fmt.lower(), fmts),
                    map(lambda fmt: api.format_abspath(id, fmt), fmts),
                )),
                fmts[0].lower(),
            ]
        return ebooks
