import sys
import time
import libtorrent as lt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplitter, QMenuBar, QMenu,
    QDialog, QLabel, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer

from crawler import Crawler
from db.database import create_connection, create_table, search_seeds

class CrawlerWorker(QObject):
    new_torrent = Signal(str, int, int, str)
    log_message = Signal(str)

    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file
        self.crawler = None
        self._running = False

    def run(self):
        self._running = True
        self.log_message.emit("Crawler starting...")
        conn = create_connection(self.db_file)
        create_table(conn)
        self.crawler = Crawler(conn)

        while self._running:
            try:
                alerts = self.crawler.session.pop_alerts()
                for alert in alerts:
                    if isinstance(alert, lt.dht_announce_alert):
                        info_hash = alert.info_hash
                        params = {
                            'save_path': '.',
                            'storage_mode': lt.storage_mode_t(2),
                            'paused': False,
                            'auto_managed': True,
                            'duplicate_is_error': True,
                            'info_hash': info_hash
                        }
                        self.crawler.metadata_session.add_torrent(params)

                metadata_alerts = self.crawler.metadata_session.pop_alerts()
                for alert in metadata_alerts:
                    if isinstance(alert, lt.metadata_received_alert):
                        info = alert.get_torrent_info()
                        size = info.total_size()
                        files = info.num_files()
                        name = info.name()
                        info_hash_str = str(info.info_hash())
                        self.crawler.insert_seed(name, size, files, info_hash_str)
                        self.new_torrent.emit(name, size, files, info_hash_str)
                time.sleep(1)
            except Exception as e:
                self.log_message.emit(f"Crawler error: {e}")

        self.crawler.conn.close()
        self.log_message.emit("Crawler stopped.")


    def stop(self):
        self._running = False


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings placeholder"))
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BTSeedAggregator")
        self.setGeometry(100, 100, 1024, 768)
        self.db_file = "seeds.db"
        self.conn = create_connection(self.db_file)

        self._create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_sidebar = QWidget()
        left_sidebar.setFixedWidth(150)
        sidebar_layout = QVBoxLayout(left_sidebar)
        sidebar_layout.addWidget(QTextEdit("Filters (placeholder)"))

        right_content = QSplitter(Qt.Vertical)
        self.torrent_table = QTableWidget()
        self.torrent_table.setColumnCount(4)
        self.torrent_table.setHorizontalHeaderLabels(["Name", "Size", "Files", "Info Hash"])
        self.torrent_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.torrent_table.customContextMenuRequested.connect(self.open_context_menu)
        right_content.addWidget(self.torrent_table)

        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        right_content.addWidget(self.log_panel)
        right_content.setSizes([500, 200])

        main_layout.addWidget(left_sidebar)
        main_layout.addWidget(right_content)

        QTimer.singleShot(5000, self.start_crawler)

    def start_crawler(self):
        self.crawler_thread = QThread()
        self.crawler_worker = CrawlerWorker(self.db_file)
        self.crawler_worker.moveToThread(self.crawler_thread)
        self.crawler_thread.started.connect(self.crawler_worker.run)
        self.crawler_worker.new_torrent.connect(self.add_torrent_to_table)
        self.crawler_worker.log_message.connect(self.update_log)
        self.crawler_thread.start()

    def add_torrent_to_table(self, name, size, files, info_hash):
        row_position = self.torrent_table.rowCount()
        self.torrent_table.insertRow(row_position)
        self.torrent_table.setItem(row_position, 0, QTableWidgetItem(name))
        self.torrent_table.setItem(row_position, 1, QTableWidgetItem(str(size)))
        self.torrent_table.setItem(row_position, 2, QTableWidgetItem(str(files)))
        self.torrent_table.setItem(row_position, 3, QTableWidgetItem(info_hash))

    def update_log(self, message):
        self.log_panel.append(message)

    def open_context_menu(self, position):
        menu = QMenu()
        find_related_action = menu.addAction("Find Related Seeds")
        action = menu.exec(self.torrent_table.mapToGlobal(position))
        if action == find_related_action:
            selected_items = self.torrent_table.selectedItems()
            if selected_items:
                name = selected_items[0].text()
                self.update_log(f"Finding related seeds for: {name}")
                self.torrent_table.setRowCount(0) # Clear the table
                results = search_seeds(self.conn, name)
                for row in results:
                    #  (id, info_hash, name, size, files)
                    self.add_torrent_to_table(row[2], row[3], row[4], row[1])

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Exit", self.close)
        tools_menu = menu_bar.addMenu("Tools")
        tools_menu.addAction("Settings", self.open_settings)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        if hasattr(self, 'crawler_worker'):
            self.crawler_worker.stop()
            self.crawler_thread.quit()
            self.crawler_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
