from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QCheckBox, QDialog, QGridLayout,
                             QScrollArea, QFrame, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import requests
import sqlite3
import os

def create_db_table_widget():
    """Crea e configura la tabella per il database"""
    table = QTableWidget()
    table.setColumnCount(12)
    table.setHorizontalHeaderLabels([
        "ID", "Path", "mtime", "Title", "Genres", "Year", "Directors",
        "Plot", "Actors", "Duration", "Rating", "Poster"
    ])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    return table

