from calibre.constants import DEBUG
from calibre.gui2 import Dispatcher
from calibre.gui2.preferences import show_config_widget
from calibre.gui2.threaded_jobs import ThreadedJob
from calibre.gui2.email import gui_sendmail
from calibre.utils.smtp import config as email_config
from calibre_plugins.send_to_kindle.config import get_config, set_config
from calibre_plugins.send_to_kindle import SendToKindle
from calibre.library.save_to_disk import save_to_disk

try:
    from qt.core import (
        Qt, QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel,
        QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QWidget,
        QListWidget, QListWidgetItem, QComboBox, QSize
    )
except ImportError:
    try:
        from PyQt5.Qt import (
            Qt, QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel,
            QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QWidget,
            QListWidget, QListWidgetItem, QComboBox, QSize
        )
    except ImportError:
        from PyQt4.Qt import (
            Qt, QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel,
            QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QWidget,
            QListWidget, QListWidgetItem, QComboBox, QSize
        )

load_translations()

app_title = _(SendToKindle.title)
app_description = SendToKindle.description
app_author = SendToKindle.author
app_version = SendToKindle.get_version()


def pop_alert(text):
    alert = QMessageBox()
    alert.setIcon(QMessageBox.Information)
    alert.setText(text)
    alert.exec_()


class ProcessDialog(QDialog):
    def __init__(self, gui, icon, ebooks):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.icon = icon
        self.ebooks = ebooks
        self.email_list = None

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.layout_send(), _('Send'))

        config_widget = QWidget()
        self.config_layout = QVBoxLayout(config_widget)
        self.tabs.addTab(config_widget, _('Setting'))
        self.layout_config()

        self.tabs.addTab(self.layout_about(), _('About'))
        self.tabs.setStyleSheet('QTabBar::tab {width:100px;}')
        layout.addWidget(self.tabs)

    def layout_send(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(_('Double-click to edit the book title:'))
        layout.addWidget(label)

        table = QTableWidget()
        table.setRowCount(len(self.ebooks))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([_('Title'), _('Format')])

        header = table.horizontalHeader()
        try:
            stretch = QHeaderView.ResizeMode.Stretch
        except Exception:
            stretch = QHeaderView.Stretch
        header.setSectionResizeMode(0, stretch)

        for index, (title, fmts, fmt) in self.ebooks.items():
            item = QTableWidgetItem(title)
            item.setSizeHint(table.sizeHint())
            table.setItem(index, 0, item)

            select = QComboBox()
            fmts = list(fmts.keys())
            for fmt in fmts:
                select.addItem(fmt)
                select.setStyleSheet('text-transform:uppercase;')
                # todo: set current index according to email setting.
                if fmt == 'epub':
                    select.setCurrentIndex(fmts.index(fmt))
                    self.ebooks[index][2] = fmt
            table.setCellWidget(index, 1, select)
            select.currentTextChanged.connect(
                lambda fmt: self.alter_ebook_format(index, fmt)
            )
        layout.addWidget(table)

        send_button = QPushButton(_('Send to Kindle'))
        send_button.clicked.connect(self.send_ebooks)
        layout.addWidget(send_button)

        table.itemChanged.connect(
            lambda item: self.alter_ebook_title(item.row(), item.text())
        )

        return widget

    def alter_ebook_title(self, row, title):
        self.ebooks[row][0] = title

    def alter_ebook_format(self, row, fmt):
        self.ebooks[row][2] = fmt

    def layout_config(self):
        for i in range(self.config_layout.count()):
            item = self.config_layout.itemAt(i)
            item.widget().close()
            self.config_layout.removeItem(item)

        if len(self.get_destnations()) < 1:
            self.email_list = None
            widget = self.layout_config_notice()
            self.config_layout.addWidget(widget)
        else:
            widget = self.layout_config_data()
            self.config_layout.addWidget(widget)

    def layout_config_notice(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addStretch(1)

        label = QLabel(_(
            'This plugin uses the Calibre email configuration; '
            'please click the button below to add email:'
        ))
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        button = QPushButton(_('Email Setting'))
        button.clicked.connect(self.open_email_setting)
        layout.addWidget(button)

        layout.addStretch(2)

        return widget

    def layout_config_data(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(_('Choose the email address to receive ebook:'))
        layout.addWidget(label)

        self.email_list = QListWidget()
        for email, options in self.get_destnations().items():
            item = QListWidgetItem(email, self.email_list)
            item.setSizeHint(QSize(0, 20))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if options['default']
                or item.text() in get_config('kindle_emails', [])
                else Qt.Unchecked
            )
        self.email_list.sortItems(Qt.AscendingOrder)
        layout.addWidget(self.email_list)

        config_button = QPushButton(_('Email Setting'))
        config_button.clicked.connect(self.open_email_setting)
        layout.addWidget(config_button)

        save_button = QPushButton(_('Save'))
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        return widget

    def open_email_setting(self):
        show_config_widget('Sharing', 'Email', gui=self.gui)
        self.layout_config()

    def layout_about(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addStretch(1)

        logo = QLabel()
        logo.setPixmap(self.icon.pixmap(80, 80))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        name = QLabel(app_title.upper())
        name.setStyleSheet('font-size:20px;font-weight:300;')
        name.setAlignment(Qt.AlignCenter)
        name.setTextFormat(Qt.RichText)
        layout.addWidget(name)

        version = QLabel(app_version)
        version.setStyleSheet('font-size:14px;')
        version.setAlignment(Qt.AlignCenter)
        version.setTextFormat(Qt.RichText)
        layout.addWidget(version)

        description = QLabel(app_description)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setMargin(15)
        layout.addWidget(description)

        donate = QLabel((
            '<a href="https://bookfere.com">{}</a>'
            ' ｜ <a href="https://bookfere.com/post/1042.html">{}</a>'
            ' ｜ <a href="https://bookfere.com/donate">{}</a>'
        ).format(app_author, _('Feedback'), _('Donate')))
        donate.setAlignment(Qt.AlignCenter)
        donate.setOpenExternalLinks(True)
        layout.addWidget(donate)

        layout.addStretch(2)

        return widget

    def save_config(self):
        set_config('kindle_emails', self.get_checked_destnations())
        pop_alert(_('The configuration has been saved.'))

    def get_checked_destnations(self):
        emails = []
        if self.email_list is not None:
            for i in range(self.email_list.count()):
                item = self.email_list.item(i)
                if item.checkState() == Qt.Checked:
                    emails.append(item.text())
        return emails

    def get_destnations(self):
        emails = {}
        opts = email_config().parse()
        for email, options in opts.accounts.items():
            fmts = map(lambda s: s.strip(), options[0].split(','))
            emails[email] = {
                'formats': fmts,
                'default': options[2],
            }
        return emails

    def email_sent(self, job):
        if job.failed:
            self.gui.job_exception(job, dialog_title=_('Failed to email book'))
            return
        self.gui.status_bar.show_message(
            job.description + ' ' + _('sent'), 5000
        )

    def send_ebooks(self):
        emails = self.get_checked_destnations()
        if len(self.ebooks) < 1:
            return
        if len(emails) < 1:
            pop_alert(_('You must provide an email address.'))
            self.tabs.setCurrentIndex(1)
            return
        for title, fmts, fmt in self.ebooks.values():
            path = fmts[fmt]
            name = '%s.%s' % (title, fmt)
            for email in emails:
                self.send_ebook(email, path, name)
        self.ebooks.clear()

        info = QMessageBox()
        detail = info.addButton(_('Show Details ...'), QMessageBox.ActionRole)
        info.addButton(QMessageBox.Ok)
        info.setIcon(QMessageBox.Information)
        info.setText(_('The ebook has been added to the send job queue.'))
        info.exec_()

        if info.clickedButton() == detail:
            self.gui.jobs_dialog.show()

        self.done(0)

    def send_ebook(self, email, path, name):
        description = _('Email {} to {}').format(name, email)
        if DEBUG:
            print(description)
            return
        job = ThreadedJob(
            'email', description, gui_sendmail,
            (path, name, email, name, name), {},
            Dispatcher(self.email_sent),
        )
        self.gui.job_manager.run_threaded_job(job)
