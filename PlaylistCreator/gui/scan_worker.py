import os
from PyQt5.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    progress_update = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, db, folder_path):
        super().__init__()
        self.db = db
        self.folder_path = folder_path
        self._is_running = True

    def run(self):
        try:
            # Estensioni video supportate - AGGIORNATE
            video_extensions = (
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                '.m4v', '.mpg', '.mpeg', '.m2v', '.m4v', '.ts', '.mts', '.m2ts',
                '.vob', '.ogv', '.ogg', '.drc', '.gif', '.gifv', '.mng',
                '.qt', '.yuv', '.rm', '.rmvb', '.asf', '.amv', '.divx',
                '.3gp', '.3g2', '.mxf', '.roq', '.nsv', '.f4v', '.f4p',
                '.f4a', '.f4b'
            )
            video_files = []

            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith(video_extensions):
                        video_files.append(os.path.join(root, file))

            total = len(video_files)
            for i, video_path in enumerate(video_files):
                self.db.scan_and_update(video_path)
                self.progress_update.emit(i + 1, total)

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Ferma il thread sicuramente"""
        self._is_running = False
        self.wait(5000)  # Aspetta max 5 secondi