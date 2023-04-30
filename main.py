import os.path

from calibre.constants import DEBUG
from calibre.utils.localization import get_lang
from calibre.gui2.preferences import show_config_widget
from calibre.gui2.threaded_jobs import ThreadedJob
from calibre.gui2.email import gui_sendmail
from calibre.utils.smtp import config as email_config
from calibre.customize.ui import available_output_formats
from calibre.utils.short_uuid import uuid4
from calibre_plugins.send_to_kindle.config import (
    init_config, get_config, set_config)
from calibre_plugins.send_to_kindle import SendToKindle

try:
    from qt.core import (
        Qt, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox,
        QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
        QWidget, QListWidget, QListWidgetItem, QSize, QCheckBox, QComboBox,
        QGroupBox, QGridLayout, QSpacerItem, QFrame)
except ImportError:
    from PyQt5.Qt import (
        Qt, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox,
        QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
        QWidget, QListWidget, QListWidgetItem, QSize, QCheckBox, QComboBox,
        QGroupBox, QGridLayout, QSpacerItem, QFrame)

load_translations()


def pop_alert(text):
    alert = QMessageBox()
    alert.setIcon(QMessageBox.Information)
    alert.setText(text)
    alert.exec_()


def get_divider():
    divider = QFrame()
    divider.setFrameShape(QFrame.HLine)
    divider.setFrameShadow(QFrame.Sunken)
    return divider


class ProcessDialog(QDialog):
    def __init__(self, gui, icon, ebooks):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.icon = icon
        self.ebooks = ebooks
        self.email_list = None

        init_config()

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

        layout.addWidget(self.layout_footer())

    def layout_send(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(_('Double-click to edit the ebook title for '
                         'display on your Kindle.'))
        layout.addWidget(label)

        table = QTableWidget()
        table.setRowCount(len(self.ebooks))
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels([_('Ebook Title')])

        header = table.horizontalHeader()
        stretch = getattr(QHeaderView, 'Stretch', None) or \
            QHeaderView.ResizeMode.Stretch
        header.setSectionResizeMode(0, stretch)

        for row, item in self.ebooks.items():
            title = QTableWidgetItem(item[1])
            title.setSizeHint(table.sizeHint())
            table.setItem(row, 0, title)
        layout.addWidget(table)

        send_button = QPushButton(_('Send to Kindle'))
        send_button.clicked.connect(self.send_ebooks)
        layout.addWidget(send_button)

        table.itemChanged.connect(
            lambda item: self.alter_ebook_info(item.row(), 2, item.text()))

        return widget

    def alter_ebook_info(self, row, index, info):
        self.ebooks[row][index] = info

    def layout_config(self):
        for i in range(self.config_layout.count()):
            item = self.config_layout.itemAt(i)
            item.widget().close()
            self.config_layout.removeItem(item)

        if len(self.get_destinations()) < 1:
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
            'please click the button below to add email.'))
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)

        button = QPushButton(_('Email Setting'))
        button.clicked.connect(self.open_email_setting)
        layout.addWidget(button)

        layout.addStretch(1)
        return widget

    def layout_config_data(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        preferred_widget = QGroupBox(_('Preferred Setting'))
        preferred_layout = QVBoxLayout(preferred_widget)
        preferred_format_widget = QWidget()
        preferred_format_layout = QHBoxLayout(preferred_format_widget)
        preferred_format_layout.setContentsMargins(0, 0, 0, 0)
        self.preferred_format = QComboBox()
        self.preferred_format.setStyleSheet('text-transform:uppercase')
        self.preferred_format.addItems(available_output_formats())
        self.preferred_format.model().sort(0, Qt.AscendingOrder)
        self.preferred_format.insertItem(0, _('Unset'))
        self.preferred_format.setCurrentText(
            get_config('preferred_format') or _('Unset'))
        preferred_format_layout.addWidget(QLabel(_('Preferred Format')))
        preferred_format_layout.addWidget(self.preferred_format, 1)
        self.delete_from_library = QCheckBox(
            _('Delete ebook from library after sending'))
        self.delete_from_library.setChecked(get_config('delete_from_library'))
        preferred_layout.addWidget(preferred_format_widget)
        preferred_layout.addWidget(self.delete_from_library)
        layout.addWidget(preferred_widget)

        email_widget = QGroupBox(_('Email Address'))
        email_layout = QVBoxLayout(email_widget)
        config_button = QPushButton(_('Manage Email Address'))
        config_button.clicked.connect(self.open_email_setting)
        email_layout.addWidget(config_button)
        layout.addWidget(email_widget)
        self.email_list = QListWidget()
        self.email_list.setMaximumHeight(120)
        for email, options in self.get_destinations().items():
            alias = options['alias']
            item_text = email if alias is None else '%s (%s)' % (alias, email)
            item = QListWidgetItem(item_text, self.email_list)
            item.setData(Qt.UserRole, email)
            item.setSizeHint(QSize(0, 20))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            config = get_config('kindle_emails', [])
            item.setCheckState(
                Qt.Checked if len(config) < 1 and options['default']
                or item.data(Qt.UserRole) in config else Qt.Unchecked)
        self.email_list.sortItems(Qt.AscendingOrder)
        email_layout.addWidget(self.email_list)

        save_button = QPushButton(_('Save'))
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        return widget

    def open_email_setting(self):
        show_config_widget('Sharing', 'Email', gui=self.gui)
        self.layout_config()

    def save_config(self):
        preferred_format = self.preferred_format.currentText()
        set_config('preferred_format', None if preferred_format == _('Unset')
                   else preferred_format)
        set_config('delete_from_library', self.delete_from_library.isChecked())
        destinations = self.get_checked_destinations()
        if len(destinations) < 1:
            return pop_alert(_('You must provide an email address.'))
        set_config('kindle_emails', destinations)
        pop_alert(_('The configuration has been saved.'))

    def get_checked_destinations(self):
        emails = []
        if self.email_list is not None:
            for i in range(self.email_list.count()):
                item = self.email_list.item(i)
                if item.checkState() == Qt.Checked:
                    emails.append(item.data(Qt.UserRole))
        return emails

    def get_destinations(self):
        emails = {}
        opts = email_config().parse()
        for email, options in opts.accounts.items():
            emails[email] = {
                'formats': [f.strip().lower() for f in options[0].split(',')],
                'default': options[2],  # Default email
                'alias': opts.aliases.get(email),
                'subject': opts.subjects.get(email) or '',
            }
        return emails

    def layout_about(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addStretch(1)

        logo = QLabel()
        logo.setPixmap(self.icon.pixmap(80, 80))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        name = QLabel(_(SendToKindle.name).upper())
        name.setStyleSheet('font-size:20px;font-weight:300;')
        name.setAlignment(Qt.AlignCenter)
        name.setTextFormat(Qt.RichText)
        layout.addWidget(name)

        version = QLabel(SendToKindle.__version__)
        version.setStyleSheet('font-size:14px;')
        version.setAlignment(Qt.AlignCenter)
        version.setTextFormat(Qt.RichText)
        layout.addWidget(version)

        description = QLabel(SendToKindle.description)
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setMargin(15)
        layout.addWidget(description)

        layout.addStretch(1)

        return widget

    def layout_footer(self):
        widget = QWidget()
        widget.setStyleSheet('color:grey')
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        app_author = SendToKindle.author
        site = QLabel('♥ by <a href="https://{0}">{0}</a>'.format(app_author))
        site.setOpenExternalLinks(True)
        layout.addWidget(site)
        layout.addStretch(1)
        github = 'https://github.com/bookfere/Send-to-Kindle-Calibre-Plugin'
        if 'zh' in get_lang():
            feedback = 'https://{}/post/1042.html'.format(app_author)
            donate = 'https://{}/donate'.format(app_author)
        else:
            feedback = '{}/issues'.format(github)
            donate = 'https://www.paypal.com/paypalme/bookfere'
        link = QLabel((
            '<a href="{0}">GitHub</a> ｜ <a href="{1}">{3}</a>'
            ' ｜ <a href="{2}">{4}</a>')
            .format(github, feedback, donate, _('Feedback'), _('Donate')))
        link.setOpenExternalLinks(True)
        layout.addWidget(link)

        return widget

    def get_changed_aname(self, aname):
        ext = os.path.splitext(aname)[1].lower()
        for item in self.ebooks.values():
            if aname == item[1].lower() + ext:
                return item[2] + ext
        return aname

    def send_ebooks(self):
        if len(self.ebooks) < 1:
            return

        emails = self.get_checked_destinations()
        if len(emails) < 1:
            pop_alert(_('You must provide an email address.'))
            self.tabs.setCurrentIndex(1)
            return

        def send_mails(jobnames, callback, attachments, to_s, subjects,
                       texts, attachment_names, job_manager):
            data = zip(
                jobnames, attachments, to_s, subjects, texts, attachment_names)
            for name, attachment, to, subject, text, aname in data:
                description = _(
                    'Email %(name)s to %(to)s') % dict(name=name, to=to)
                subject = subject or uuid4()
                text = text or uuid4()
                aname = self.get_changed_aname(aname.lower())
                if DEBUG:
                    print(attachment, aname, to, subject, text)
                    return
                job = ThreadedJob(
                    'email', description, gui_sendmail,
                    (attachment, aname, to, subject, text), {}, callback)
                job_manager.run_threaded_job(job)
        import calibre.gui2.email
        calibre.gui2.email.send_mails = send_mails

        destinations = self.get_destinations()
        ids = [ebook[0] for ebook in self.ebooks.values()]
        preferred_format = get_config('preferred')
        for email in emails:
            destination = destinations.get(email)
            formats = destination.get('formats')
            subject = destination.get('subject')
            self.gui.send_by_mail(
                email, formats, get_config('delete_from_library'),
                subject=subject, send_ids=ids,
                specific_format=preferred_format)
        self.ebooks.clear()
        self.done(0)
