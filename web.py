import sys
import os
from PySide6.QtCore import QUrl, Qt, QSize, Signal, QSettings, QByteArray
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                              QToolBar, QLineEdit, QPushButton, QMenu, 
                              QStatusBar, QProgressBar, QDialog, QVBoxLayout, 
                              QHBoxLayout, QLabel, QListWidget, QWidget, 
                              QTabBar, QFrame, QCheckBox, QColorDialog, QFileDialog)
from PySide6.QtGui import QIcon, QAction, QFont, QColor, QPalette, QCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (QWebEngineProfile, QWebEngineDownloadRequest, 
                                    QWebEnginePage, QWebEngineUrlRequestInterceptor,
                                    QWebEngineSettings)


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_hosts = set()
        self.load_filters()
        
    def load_filters(self):
        # Common ad domains - in a real implementation, this would load from a more comprehensive filter list
        ad_domains = [
            "ads.", "ad.", "banner.", "banners.", "adserv.", "adserver.",
            "advert.", "popup.", "pop-up.", "track.", "tracker.", "tracking.",
            "stats.", "stat.", "analytics.", "metric.", "googleadservices.",
            "googlesyndication.", "doubleclick.", "amazon-adsystem.",
            "facebook.net", "facebook.com/tr", "analytics.google.com",
            "pagead2.", "2mdn.net", "serving-sys.com", "scdn.cxense.com", 
            "scorecardresearch.com", "adnxs.com", "taboola.com", "outbrain.com"
        ]
        
        for domain in ad_domains:
            self.blocked_hosts.add(domain)
    
    def interceptRequest(self, info):
        url = info.requestUrl().toString().lower()
        
        # Check if the URL contains any of the blocked hosts
        for blocked_host in self.blocked_hosts:
            if blocked_host in url:
                info.block(True)
                return
                
        # Let the request through
        info.block(False)


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        
        # Configure page settings using QWebEngineSettings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        
    def acceptNavigationRequest(self, url, type, isMainFrame):
        # Always accept navigation request
        return True
        
    def javaScriptConsoleMessage(self, level, message, line, source):
        # Optionally log JavaScript console messages for debugging
        # print(f"JS [{level}] {message} (Line {line} in {source})")
        pass


class DownloadManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.setMinimumSize(500, 300)
        
        # Apply dark theme
        self.set_dark_theme()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Downloads list
        self.downloads_list = QListWidget()
        layout.addWidget(self.downloads_list)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Completed")
        self.clear_btn.clicked.connect(self.clear_completed)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Downloads tracking
        self.downloads = {}
        
    def add_download(self, download):
        download_id = id(download)
        self.downloads[download_id] = download
        
        # Add to list
        filename = os.path.basename(download.downloadDirectory() + "/" + download.downloadFileName())
        item_text = f"Downloading: {filename}"
        item = self.downloads_list.addItem(item_text)
        download_item = self.downloads_list.item(self.downloads_list.count() - 1)
        
        # Connect signals
        download.downloadProgress.connect(lambda received, total, d_id=download_id, idx=self.downloads_list.count() - 1: 
                                         self.update_progress(d_id, idx, received, total))
        download.finished.connect(lambda d_id=download_id, idx=self.downloads_list.count() - 1: 
                                 self.download_finished(d_id, idx))
        
        # Show the dialog to make downloads visible to user
        self.show()
        return download_item
    
    def update_progress(self, download_id, index, received, total):
        if download_id in self.downloads and total > 0 and index < self.downloads_list.count():
            progress = int(received * 100 / total)
            filename = os.path.basename(self.downloads[download_id].downloadDirectory() + "/" + self.downloads[download_id].downloadFileName())
            self.downloads_list.item(index).setText(f"Downloading: {filename} - {progress}%")
    
    def download_finished(self, download_id, index):
        if download_id in self.downloads and index < self.downloads_list.count():
            filename = os.path.basename(self.downloads[download_id].downloadDirectory() + "/" + self.downloads[download_id].downloadFileName())
            self.downloads_list.item(index).setText(f"Completed: {filename}")
            # Show notification
            self.show()
            self.raise_()
            
            # Optional: Display a status message
            if self.parent():
                self.parent().status_bar.showMessage(f"Download complete: {filename}", 3000)
    
    def clear_completed(self):
        for i in range(self.downloads_list.count() - 1, -1, -1):
            item = self.downloads_list.item(i)
            if item and "Completed: " in item.text():
                self.downloads_list.takeItem(i)
    
    def set_dark_theme(self):
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)


class BookmarksManager(QDialog):
    bookmarkSelected = Signal(str)
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Bookmarks")
        self.setMinimumSize(500, 300)
        
        # Apply dark theme
        self.set_dark_theme()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Bookmarks list
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemDoubleClicked.connect(self.open_bookmark)
        layout.addWidget(self.bookmarks_list)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_bookmark)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Load bookmarks
        self.load_bookmarks()
    
    def load_bookmarks(self):
        self.bookmarks_list.clear()
        size = self.settings.beginReadArray("bookmarks")
        
        for i in range(size):
            self.settings.setArrayIndex(i)
            title = self.settings.value("title")
            url = self.settings.value("url")
            self.bookmarks_list.addItem(f"{title} - {url}")
        
        self.settings.endArray()
    
    def add_bookmark(self, title, url):
        # Add to settings
        size = self.settings.beginReadArray("bookmarks")
        self.settings.endArray()
        
        self.settings.beginWriteArray("bookmarks", size + 1)
        self.settings.setArrayIndex(size)
        self.settings.setValue("title", title)
        self.settings.setValue("url", url)
        self.settings.endArray()
        
        # Add to list
        self.bookmarks_list.addItem(f"{title} - {url}")
    
    def delete_bookmark(self):
        current_row = self.bookmarks_list.currentRow()
        if current_row >= 0:
            # Remove from list
            self.bookmarks_list.takeItem(current_row)
            
            # Rebuild settings
            bookmarks = []
            size = self.settings.beginReadArray("bookmarks")
            
            for i in range(size):
                if i != current_row:
                    self.settings.setArrayIndex(i)
                    title = self.settings.value("title")
                    url = self.settings.value("url")
                    bookmarks.append((title, url))
            
            self.settings.endArray()
            
            # Write back
            self.settings.beginWriteArray("bookmarks", len(bookmarks))
            for i, (title, url) in enumerate(bookmarks):
                self.settings.setArrayIndex(i)
                self.settings.setValue("title", title)
                self.settings.setValue("url", url)
            self.settings.endArray()
    
    def open_bookmark(self, item):
        # Extract URL from item text
        url = item.text().split(" - ")[1]
        self.bookmarkSelected.emit(url)
        self.close()
    
    def set_dark_theme(self):
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)


class SettingsDialog(QDialog):
    settingsChanged = Signal()
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)
        
        # Apply dark theme
        self.set_dark_theme()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Dark mode setting
        self.dark_mode = QCheckBox("Dark Mode")
        self.dark_mode.setChecked(self.settings.value("darkMode", True, type=bool))
        layout.addWidget(self.dark_mode)
        
        # Ad blocker setting
        self.ad_blocker = QCheckBox("Enable Ad Blocker")
        self.ad_blocker.setChecked(self.settings.value("adBlocker", True, type=bool))
        layout.addWidget(self.ad_blocker)
        
        # Cursor lock setting
        self.cursor_lock = QCheckBox("Enable Cursor Lock for Games")
        self.cursor_lock.setChecked(self.settings.value("cursorLock", True, type=bool))
        layout.addWidget(self.cursor_lock)
        
        # Home page setting
        home_layout = QHBoxLayout()
        home_layout.addWidget(QLabel("Home Page:"))
        self.home_page = QLineEdit()
        self.home_page.setText(self.settings.value("homePage", "https://www.google.com"))
        home_layout.addWidget(self.home_page)
        layout.addLayout(home_layout)
        
        # Download directory
        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel("Download Directory:"))
        self.download_dir = QLineEdit()
        self.download_dir.setText(self.settings.value("downloadDir", os.path.expanduser("~/Downloads")))
        download_layout.addWidget(self.download_dir)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        download_layout.addWidget(browse_btn)
        layout.addLayout(download_layout)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addStretch()
        layout.addLayout(btn_layout)
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir.setText(directory)
    
    def save_settings(self):
        self.settings.setValue("darkMode", self.dark_mode.isChecked())
        self.settings.setValue("adBlocker", self.ad_blocker.isChecked())
        self.settings.setValue("cursorLock", self.cursor_lock.isChecked())
        self.settings.setValue("homePage", self.home_page.text())
        self.settings.setValue("downloadDir", self.download_dir.text())
        self.settingsChanged.emit()
        self.close()
    
    def set_dark_theme(self):
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("ModernBrowser", "WebBrowser")
        
        # Set window properties
        self.setWindowTitle("arkbrowser")
        self.setMinimumSize(1024, 768)
        
        # Set up ad blocker
        self.ad_blocker = AdBlocker(self)
        
        # Create a central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        # Initialize tab widget with custom styling
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        
        # Style the tab bar
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setDrawBase(False)
        tab_bar.setElideMode(Qt.ElideRight)
        
        # Add tab widget to layout
        self.layout.addWidget(self.tabs)
        
        # Create navigation bar
        self.create_navigation_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Initialize download manager
        self.download_manager = DownloadManager(self)
        
        # Initialize bookmarks manager
        self.bookmarks_manager = BookmarksManager(self.settings, self)
        self.bookmarks_manager.bookmarkSelected.connect(self.navigate_to_url)
        
        # Apply theme based on settings - after all UI elements are created
        self.apply_theme()
        
        # Enable ad blocker if set in settings
        if self.settings.value("adBlocker", True, type=bool):
            QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.ad_blocker)
        
        # Create first tab
        self.add_new_tab()
    
    def create_navigation_bar(self):
        # Create toolbar
        self.navbar = QToolBar("Navigation")
        self.navbar.setIconSize(QSize(16, 16))
        self.navbar.setMovable(False)
        self.navbar.setStyleSheet("QToolBar { border: 0px; border-radius: 8px; padding: 5px; }")
        
        # Add toolbar to main window
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self.navbar)
        self.layout.insertWidget(0, nav_frame)
        
        # Back button
        self.back_btn = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.back_btn.setShortcut("Alt+Left")
        self.back_btn.triggered.connect(lambda: self.current_browser().back())
        self.navbar.addAction(self.back_btn)
        
        # Forward button
        self.forward_btn = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        self.forward_btn.setShortcut("Alt+Right")
        self.forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.navbar.addAction(self.forward_btn)
        
        # Reload button
        self.reload_btn = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        self.reload_btn.setShortcut("F5")
        self.reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.navbar.addAction(self.reload_btn)
        
        # Home button
        self.home_btn = QAction(QIcon.fromTheme("go-home"), "Home", self)
        self.home_btn.setShortcut("Alt+Home")
        self.home_btn.triggered.connect(self.navigate_home)
        self.navbar.addAction(self.home_btn)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search term...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setStyleSheet("QLineEdit { border-radius: 15px; padding: 5px 10px; }")
        self.navbar.addSeparator()
        self.navbar.addWidget(self.url_bar)
        
        # Bookmarks button
        self.bookmark_btn = QAction(QIcon.fromTheme("bookmark-new"), "Bookmark", self)
        self.bookmark_btn.triggered.connect(self.add_bookmark)
        self.navbar.addAction(self.bookmark_btn)
        
        # Bookmarks menu
        self.bookmarks_btn = QAction(QIcon.fromTheme("bookmarks"), "Bookmarks", self)
        self.bookmarks_btn.triggered.connect(self.show_bookmarks)
        self.navbar.addAction(self.bookmarks_btn)
        
        # Downloads button
        self.downloads_btn = QAction(QIcon.fromTheme("document-save"), "Downloads", self)
        self.downloads_btn.triggered.connect(self.show_downloads)
        self.navbar.addAction(self.downloads_btn)
        
        # Ad blocker toggle
        self.ad_block_btn = QAction(QIcon.fromTheme("security-high"), "Ad Blocker", self)
        self.ad_block_btn.setCheckable(True)
        self.ad_block_btn.setChecked(self.settings.value("adBlocker", True, type=bool))
        self.ad_block_btn.triggered.connect(self.toggle_ad_blocker)
        self.navbar.addAction(self.ad_block_btn)
        
        # Settings button
        self.settings_btn = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
        self.settings_btn.triggered.connect(self.show_settings)
        self.navbar.addAction(self.settings_btn)
        
        # New tab button
        self.new_tab_btn = QAction(QIcon.fromTheme("tab-new"), "New Tab", self)
        self.new_tab_btn.setShortcut("Ctrl+T")
        self.new_tab_btn.triggered.connect(self.add_new_tab)
        self.navbar.addAction(self.new_tab_btn)
        
    def toggle_ad_blocker(self):
        is_enabled = self.ad_block_btn.isChecked()
        self.settings.setValue("adBlocker", is_enabled)
        
        if is_enabled:
            QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.ad_blocker)
            self.status_bar.showMessage("Ad blocker enabled", 3000)
        else:
            QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(None)
            self.status_bar.showMessage("Ad blocker disabled", 3000)
        
        # Reload current page to apply changes
        self.current_browser().reload()
    
    def add_new_tab(self, url=None):
        if not url:
            url = self.settings.value("homePage", "https://www.google.com")
        
        # Create web view
        browser = QWebEngineView()
        
        # Create custom page with enhanced settings
        custom_page = CustomWebEnginePage(QWebEngineProfile.defaultProfile(), browser)
        browser.setPage(custom_page)
        
        # Enable cursor lock for games
        if self.settings.value("cursorLock", True, type=bool):
            browser.page().featurePermissionRequested.connect(self.handle_permission_request)
        
        # Connect signals
        browser.page().titleChanged.connect(lambda title, browser=browser: 
                                           self.update_tab_title(browser, title))
        browser.page().urlChanged.connect(lambda url, browser=browser: 
                                         self.update_url_bar(url, browser))
        browser.page().loadProgress.connect(self.update_progress)
        browser.page().loadFinished.connect(lambda: self.progress_bar.setVisible(False))
        
        # Handle downloads
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.handle_download)
        
        # Load the URL
        browser.load(QUrl(url))
        
        # Add browser to tabs
        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)
        
        # Update URL bar when tab is switched
        browser.urlChanged.connect(lambda url, browser=browser: 
                                  self.update_url_bar(url, browser))
        
        # Focus URL bar when new tab is added
        self.url_bar.setFocus()
        
        return browser
        
    def handle_permission_request(self, url, feature):
        # Always grant cursor lock permission for compatible websites
        self.sender().setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
    
    def tab_changed(self, index):
        if index >= 0:
            browser = self.tabs.widget(index)
            self.update_url_bar(browser.url(), browser)
            self.update_navigation_buttons()
    
    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            # Truncate title if too long
            if len(title) > 20:
                title = title[:17] + "..."
            self.tabs.setTabText(index, title)
    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.tabs.widget(0).load(QUrl(self.settings.value("homePage", "https://www.google.com")))
    
    def current_browser(self):
        return self.tabs.currentWidget()
    
    def navigate_to_url(self, url=None):
        if not url:
            url = self.url_bar.text()
        
        if not url.startswith(("http://", "https://", "file://")):
            # Check if it's a valid URL without scheme
            if "." in url and " " not in url:
                url = "https://" + url
            else:
                # Treat as search query
                url = "https://www.google.com/search?q=" + url
        
        self.current_browser().load(QUrl(url))
    
    def update_url_bar(self, url, browser=None):
        if browser != self.current_browser():
            return
        
        self.url_bar.setText(url.toString())
        self.url_bar.setCursorPosition(0)
        self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        browser = self.current_browser()
        if browser:
            self.back_btn.setEnabled(browser.history().canGoBack())
            self.forward_btn.setEnabled(browser.history().canGoForward())
    
    def navigate_home(self):
        self.current_browser().load(QUrl(self.settings.value("homePage", "https://www.google.com")))
    
    def update_progress(self, progress):
        self.progress_bar.setValue(progress)
        self.progress_bar.setVisible(progress < 100)
    
    def add_bookmark(self):
        # Get current page
        url = self.current_browser().url().toString()
        title = self.tabs.tabText(self.tabs.currentIndex())
        
        # Add to bookmarks
        self.bookmarks_manager.add_bookmark(title, url)
    
    def show_bookmarks(self):
        self.bookmarks_manager.load_bookmarks()
        self.bookmarks_manager.show()
    
    def show_downloads(self):
        self.download_manager.show()
    
    def handle_download(self, download):
        # Set download directory
        download_dir = self.settings.value("downloadDir", os.path.expanduser("~/Downloads"))
        download.setDownloadDirectory(download_dir)
        
        # Make sure directory exists
        os.makedirs(download_dir, exist_ok=True)
        
        # Set up download to show notifications on completion
        download.isFinishedChanged.connect(lambda: self.notify_download_finished(download))
        
        # Accept download
        download.accept()
        
        # Add to download manager
        self.download_manager.add_download(download)
        
        # Show download manager
        self.download_manager.show()
        
        # Update status bar
        self.status_bar.showMessage(f"Downloading: {download.downloadFileName()}", 3000)
        
    def notify_download_finished(self, download):
        if download.isFinished():
            filename = download.downloadFileName()
            self.status_bar.showMessage(f"Download complete: {filename}", 5000)
            # Force update in download manager
            self.download_manager.show()
    
    def show_settings(self):
        settings_dialog = SettingsDialog(self.settings, self)
        settings_dialog.settingsChanged.connect(self.apply_theme)
        settings_dialog.exec()
    
    def apply_theme(self):
        if self.settings.value("darkMode", True, type=bool):
            self.set_dark_theme()
        else:
            self.set_light_theme()
            
        # Update ad blocker based on settings
        if self.settings.value("adBlocker", True, type=bool):
            QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.ad_blocker)
        else:
            QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(None)
            
        # Update cursor lock permissions on existing tabs if tabs are already created
        if hasattr(self, 'tabs'):
            for i in range(self.tabs.count()):
                browser = self.tabs.widget(i)
                if browser and isinstance(browser, QWebEngineView):
                    # Re-create the page with proper settings
                    url = browser.url()
                    # Remember the history
                    history = browser.history()
                    
                    # Create new page with proper settings
                    custom_page = CustomWebEnginePage(QWebEngineProfile.defaultProfile(), browser)
                    browser.setPage(custom_page)
                    
                    # Reload the current URL
                    browser.load(url)
    
    def set_dark_theme(self):
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Apply palette
        QApplication.setPalette(palette)
        
        # Style sheets for rounded corners
        self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #353535;
            }
            QTabWidget::pane {
                border: 1px solid #6c6c6c;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #6c6c6c;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                border-bottom: none;
            }
            QLineEdit, QPushButton, QListWidget {
                border: 1px solid #6c6c6c;
                border-radius: 6px;
                padding: 3px;
                background-color: #2a2a2a;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QToolBar {
                background-color: #2a2a2a;
                border-radius: 8px;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: white;
            }
        """)
    
    def set_light_theme(self):
        # Reset to default palette
        QApplication.setPalette(QApplication.style().standardPalette())
        
        # Style sheets for rounded corners
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #b5b5b5;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #e6e6e6;
                border: 1px solid #b5b5b5;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: none;
            }
            QLineEdit, QPushButton, QListWidget {
                border: 1px solid #b5b5b5;
                border-radius: 6px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QToolBar {
                border-radius: 8px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show browser
    browser = Browser()
    browser.show()
    
    # Run application
    sys.exit(app.exec())