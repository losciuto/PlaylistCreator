import sys
import threading
import os
from PyQt5.QtWidgets import QApplication
import traceback


def excepthook(exctype, value, traceback_obj):
    """Gestisce le eccezioni non catturate"""
    error_msg = ''.join(traceback.format_exception(exctype, value, traceback_obj))
    print(f"Errore non catturato: {error_msg}")

    # Mostra messaggio all'utente invece di crashare
    from PyQt5.QtWidgets import QMessageBox, QApplication
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "Errore", f"Si è verificato un errore:\n{str(value)}")

# Aggiungi la cartella principale al path di Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.excepthook = excepthook

from gui.main_window import MainWindow

# Aumenta lo stack size per prevenire overflow
if hasattr(sys, 'setrecursionlimit'):
    sys.setrecursionlimit(10000)

if hasattr(threading, 'stack_size'):
    threading.stack_size(2 * 1024 * 1024)  # 2MB stack size

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

