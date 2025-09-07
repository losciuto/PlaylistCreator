import sqlite3
import os
import sys
import subprocess
import platform

# Import PyQt5

from PyQt5.QtGui import QPixmap, QColor, QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                             QFileDialog, QTabWidget, QProgressDialog, QHBoxLayout,
                             QMessageBox, QCheckBox, QDialog, QGridLayout,
                             QScrollArea, QFrame, QInputDialog, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon

# Import di terze parti
import requests
import vlc
import platform

# Import locali con percorso assoluto
from database.video_db import VideoDatabase
from gui.scan_worker import ScanWorker
from gui.widgets import create_db_table_widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = VideoDatabase()
        self.scan_worker = None
        self.current_playlist = []
        self.vlc_player = None
        self.init_ui()
        self.refresh_db_view()

        # Debug: verifica i percorsi nel database
        self.check_database_paths()

        # Controlla se il database è popolato e spostati su Genera Playlist
        self.check_and_switch_to_playlist_tab()

    def check_database_paths(self):
        """Controlla e correggi i percorsi nel database all'avvio"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT path FROM videos LIMIT 5")
                paths = cursor.fetchall()

                for path_tuple in paths:
                    path = path_tuple[0]
                    if '/' in path and platform.system() == "Windows":
                        print(f"Percorso da correggere: {path}")
                        # Correggi il percorso
                        corrected_path = path.replace('/', '\\')
                        cursor.execute("UPDATE videos SET path = ? WHERE path = ?",
                                       (corrected_path, path))

                conn.commit()
        except:
            pass

    def init_ui(self):
        self.setWindowTitle("Creatore Playlist")
        self.setGeometry(100, 100, 1200, 800)  # Finestra più grande
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4CAF50;
                border-radius: 5px;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.tabs)

        # Tab Scansione - COMPLETAMENTE RINNOVATO
        scan_tab = QWidget()
        scan_tab.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 15px 25px;
                font-weight: bold;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                transform: scale(1.03);
                background-color: #45a049;
            }
            QPushButton:pressed {
                transform: scale(0.97);
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)

        scan_layout = QVBoxLayout(scan_tab)
        scan_layout.setSpacing(25)
        scan_layout.setContentsMargins(30, 30, 30, 30)

        # Titolo della sezione
        title_label = QLabel("SCANSIONE CARTELLE")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                padding: 15px;
                background-color: #3c3c3c;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        scan_layout.addWidget(title_label)

        # Descrizione
        description_label = QLabel(
            "Scansiona le cartelle per aggiornare il database con i metadati dei video.\n"
            "Verranno cercati automaticamente i file .nfo associati per estrarre informazioni come titolo, genere, anno, etc."
        )
        description_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #cccccc;
                padding: 15px;
                background-color: #3c3c3c;
                border-radius: 8px;
                text-align: center;
                line-height: 1.5;
            }
        """)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        scan_layout.addWidget(description_label)

        # Container per il bottone di scansione
        scan_button_frame = QFrame()
        scan_button_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        scan_button_layout = QVBoxLayout(scan_button_frame)

        # Bottone principale di scansione
        self.btn_select_folder = QPushButton("📁 Seleziona Cartella da Scansionare")
        self.btn_select_folder.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 20px 30px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_folder.setCursor(Qt.PointingHandCursor)
        scan_button_layout.addWidget(self.btn_select_folder)

        scan_layout.addWidget(scan_button_frame)

        # Container per le informazioni
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("📊 Informazioni Scansione")
        info_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 15px;
                text-align: center;
            }
        """)
        info_layout.addWidget(info_title)

        # Nel tab Scansione, modifica la label delle estensioni:
        extensions_label = QLabel(
            "Estensioni video supportate:\n"
            "📹 .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm\n"
            "🎬 .m4v, .mpg, .mpeg, .m2v, .ts, .mts, .m2ts\n"
            "🎥 .vob, .ogv, .ogg, .qt, .yuv, .rm, .rmvb\n"
            "📼 .asf, .amv, .divx, .3gp, .3g2, .mxf\n"
            "➕ E molte altre..."
        )
        extensions_label.setStyleSheet("""
            QLabel {
                font-size: 12px;  # Ridotto per far entrare tutto
                color: #cccccc;
                padding: 12px;
                background-color: #2b2b2b;
                border-radius: 6px;
                text-align: center;
                line-height: 1.4;
            }
        """)
        extensions_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(extensions_label)

        # Statistiche scansione
        self.scan_info_label = QLabel("Pronto per la scansione")
        self.scan_info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #4CAF50;
                padding: 15px;
                background-color: #2b2b2b;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
            }
        """)
        self.scan_info_label.setAlignment(Qt.AlignCenter)
        self.scan_info_label.setWordWrap(True)
        info_layout.addWidget(self.scan_info_label)

        scan_layout.addWidget(info_frame)

        # Spacer finale
        scan_layout.addStretch()

        self.tabs.addTab(scan_tab, "Scansione")

        self.init_db_tab()
        self.init_playlist_tab()

        self.tab_indices = {
            'scansione': 0,
            'gestione_db': 1,
            'genera_playlist': 2
        }

    def init_db_tab(self):
        db_tab = QWidget()
        db_tab.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                transform: scale(1.02);
            }
            QPushButton:pressed {
                transform: scale(0.98);
            }
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                gridline-color: #4CAF50;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #555555;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #4CAF50;
            }
        """)

        layout = QVBoxLayout(db_tab)
        layout.setSpacing(15)  # Ridotto lo spacing
        layout.setContentsMargins(15, 15, 15, 15)  # Margini ridotti

        # Titolo della sezione
        title_label = QLabel("GESTIONE DATABASE")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;  # Ridotto da 24px
                font-weight: bold;
                color: #4CAF50;
                padding: 8px;
                background-color: #3c3c3c;
                border-radius: 8px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Container per le statistiche (più compatto)
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)

        self.db_stats_label = QLabel("Caricamento...")
        self.db_stats_label.setStyleSheet("""
            QLabel {
                font-size: 16px;  # Ridotto da 16px
                font-weight: bold;
                color: #4CAF50;
                padding: 8px;
                background-color: #2b2b2b;
                border-radius: 5px;
                text-align: center;
            }
        """)
        self.db_stats_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.db_stats_label)

        layout.addWidget(stats_frame)

        # Container per la tabella (più grande)
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)  # Margini ridotti

        # Tabella con numeri di progressivo
        self.db_table = QTableWidget()
        self.db_table.setColumnCount(11)  # 10 colonne + 1 per il progressivo
        self.db_table.setHorizontalHeaderLabels([
            "#", "Percorso", "Data Modifica", "Titolo", "Generi", "Anno",
            "Registi", "Trama", "Attori", "Durata", "Rating"
        ])

        # Rendiamo la tabella non modificabile
        self.db_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.db_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.db_table.setSelectionMode(QTableWidget.SingleSelection)

        # Configurazione header
        header = self.db_table.horizontalHeader()

        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # Imposta dimensioni colonne più ampie
        self.db_table.setColumnWidth(0, 50)  # Progressivo (numero)
        self.db_table.setColumnWidth(1, 300)  # Percorso (allargato)
        self.db_table.setColumnWidth(2, 140)  # Data Modifica
        self.db_table.setColumnWidth(3, 250)  # Titolo (allargato)
        self.db_table.setColumnWidth(4, 180)  # Generi (allargato)
        self.db_table.setColumnWidth(5, 80)  # Anno
        self.db_table.setColumnWidth(6, 180)  # Registi (allargato)
        self.db_table.setColumnWidth(7, 350)  # Trama (molto allargato)
        self.db_table.setColumnWidth(8, 200)  # Attori (allargato)
        self.db_table.setColumnWidth(9, 80)  # Durata
        self.db_table.setColumnWidth(10, 80)  # Rating

        # Abilita sorting
        self.db_table.setSortingEnabled(True)

        # Imposta altezza righe
        self.db_table.verticalHeader().setDefaultSectionSize(30)
        self.db_table.verticalHeader().setVisible(False)  # Nascondi header verticale predefinito

        table_layout.addWidget(self.db_table)
        layout.addWidget(table_frame, 1)  # Il parametro 1 fa espandere la tabella

        # Container per i pulsanti (più compatto)
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(5, 5, 5, 5)

        self.btn_clear_db = QPushButton("🗑️ Pulisci Database")
        self.btn_clear_db.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.btn_clear_db.clicked.connect(self.clear_database)
        self.btn_clear_db.setCursor(Qt.PointingHandCursor)

        self.btn_export = QPushButton("📤 Esporta Dati")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.btn_export.clicked.connect(self.export_database)
        self.btn_export.setCursor(Qt.PointingHandCursor)

        buttons_layout.addWidget(self.btn_clear_db)
        buttons_layout.addWidget(self.btn_export)
        buttons_layout.addStretch()

        layout.addWidget(buttons_frame)

        self.tabs.addTab(db_tab, "Gestione DB")

    def init_playlist_tab(self):
        playlist_tab = QWidget()
        playlist_tab.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                transform: scale(1.02);
            }
            QPushButton:pressed {
                transform: scale(0.98);
            }
        """)

        layout = QVBoxLayout(playlist_tab)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Titolo della sezione
        title_label = QLabel("GENERA PLAYLIST")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                padding: 10px;
                background-color: #3c3c3c;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Container per i bottoni di generazione
        generation_frame = QFrame()
        generation_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        generation_layout = QVBoxLayout(generation_frame)

        generation_title = QLabel("Modalità di Generazione")
        generation_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 15px;
                text-align: center;
            }
        """)
        generation_layout.addWidget(generation_title)

        # Bottoni di generazione in grid
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(15)

        # Bottone Playlist Casuale
        self.btn_random = QPushButton("🎲 Playlist Casuale")
        self.btn_random.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #7a5c29;
                color: #cccccc;
            }
        """)
        self.btn_random.clicked.connect(self.generate_random_playlist)
        self.btn_random.setCursor(Qt.PointingHandCursor)

        # Bottone Più Recenti
        self.btn_recent = QPushButton("🕒 Più Recenti")
        self.btn_recent.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #2c5282;
                color: #cccccc;
            }
        """)
        self.btn_recent.clicked.connect(self.generate_recent_playlist)
        self.btn_recent.setCursor(Qt.PointingHandCursor)

        # Bottone Selezione Manuale
        self.btn_manual = QPushButton("✏️ Selezione Manuale")
        self.btn_manual.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #553c68;
                color: #cccccc;
            }
        """)
        self.btn_manual.clicked.connect(self.show_manual_selection)
        self.btn_manual.setCursor(Qt.PointingHandCursor)

        # Aggiungi bottoni alla grid
        buttons_grid.addWidget(self.btn_random, 0, 0)
        buttons_grid.addWidget(self.btn_recent, 0, 1)
        buttons_grid.addWidget(self.btn_manual, 0, 2)
        generation_layout.addLayout(buttons_grid)

        layout.addWidget(generation_frame)

        # Container per i bottoni di azione
        action_frame = QFrame()
        action_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        action_layout = QVBoxLayout(action_frame)

        action_title = QLabel("Azioni Playlist")
        action_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 15px;
                text-align: center;
            }
        """)
        action_layout.addWidget(action_title)

        # Bottoni di azione in grid
        action_grid = QGridLayout()
        action_grid.setSpacing(15)

        # Bottone Mostra Poster
        self.btn_show_posters = QPushButton("🎨 Mostra Poster")
        self.btn_show_posters.setStyleSheet("""
            QPushButton {
                background-color: #E91E63;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #C2185B;
            }
            QPushButton:disabled {
                background-color: #6d2c4c;
                color: #cccccc;
            }
        """)
        self.btn_show_posters.clicked.connect(self.show_playlist_posters)
        self.btn_show_posters.setEnabled(False)
        self.btn_show_posters.setCursor(Qt.PointingHandCursor)

        # Bottone Riproduci con VLC
        self.btn_play_vlc = QPushButton("▶️ Riproduci con VLC")
        self.btn_play_vlc.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #3d6e3f;
                color: #cccccc;
            }
        """)
        self.btn_play_vlc.clicked.connect(self.play_with_vlc)
        self.btn_play_vlc.setEnabled(False)
        self.btn_play_vlc.setCursor(Qt.PointingHandCursor)

        # Bottone Ferma VLC
        self.btn_stop_vlc = QPushButton("⏹️ Ferma VLC")
        self.btn_stop_vlc.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.btn_stop_vlc.clicked.connect(self.cleanup_vlc)
        self.btn_stop_vlc.setCursor(Qt.PointingHandCursor)

        # Aggiungi bottoni alla grid
        action_grid.addWidget(self.btn_show_posters, 0, 0)
        action_grid.addWidget(self.btn_play_vlc, 0, 1)
        action_grid.addWidget(self.btn_stop_vlc, 0, 2)
        action_layout.addLayout(action_grid)

        layout.addWidget(action_frame)

        # Status della playlist
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)

        status_title = QLabel("Stato Attuale")
        status_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 10px;
                text-align: center;
            }
        """)
        status_layout.addWidget(status_title)

        # Label per lo stato
        self.playlist_status = QLabel("Nessuna playlist generata")
        self.playlist_status.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #cccccc;
                padding: 10px;
                background-color: #2b2b2b;
                border-radius: 5px;
                text-align: center;
            }
        """)
        self.playlist_status.setAlignment(Qt.AlignCenter)
        self.playlist_status.setWordWrap(True)
        status_layout.addWidget(self.playlist_status)

        layout.addWidget(status_frame)

        # Spacer finale
        layout.addStretch()

        self.tabs.addTab(playlist_tab, "Genera Playlist")

    def check_and_switch_to_playlist_tab(self):
        """Se il database è popolato, spostati sul tab Genera Playlist"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM videos")
                count = cursor.fetchone()[0]

                if count > 0:
                    # Piccolo delay per permettere all'UI di caricare completamente
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self.switch_to_playlist_tab(show_message=True))

        except sqlite3.Error as e:
            print(f"Errore controllo database: {e}")

    def switch_to_playlist_tab(self, show_message=False):
        """Cambia al tab Genera Playlist"""
        try:
            # Cerca il tab Genera Playlist
            tab_index = -1
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "Genera Playlist":
                    tab_index = i
                    break

            if tab_index >= 0:
                self.tabs.setCurrentIndex(tab_index)
                self.highlight_playlist_tab()

                # Aggiorna lo status della playlist
                self.update_playlist_status()

                if show_message:
                    QMessageBox.information(self, "Database Pronto",
                                            f"Il database contiene {self.db_table.rowCount()} video.\n"
                                            "Ora puoi generare le tue playlist!"
                                            )

        except Exception as e:
            print(f"Errore cambio tab: {e}")

    def highlight_playlist_tab(self):
        """Evidenzia temporaneamente il tab Genera Playlist"""
        try:
            # Trova l'indice del tab Genera Playlist
            tab_index = -1
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "Genera Playlist":
                    tab_index = i
                    break

            if tab_index >= 0:
                # Salva lo stile originale
                original_color = self.tabs.tabBar().tabTextColor(tab_index)

                # Evidenzia il tab con colore giallo
                self.tabs.tabBar().setTabTextColor(tab_index, QColor(255, 255, 0))

                # Ripristina dopo 3 secondi
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(3000, lambda: self.tabs.tabBar().setTabTextColor(tab_index, original_color))

        except Exception as e:
            print(f"Errore evidenziazione tab: {e}")

    def refresh_db_view(self):
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM videos")
                count = cursor.fetchone()[0]
                self.db_stats_label.setText(f"🎬 Video nel database: {count}")

                # Esegui query senza la colonna ID
                cursor.execute("""
                    SELECT path, mtime, title, genres, year, directors, 
                           plot, actors, duration, rating 
                    FROM videos
                """)
                data = cursor.fetchall()

                self.db_table.setRowCount(len(data))
                for row_idx, row_data in enumerate(data):
                    # Aggiungi numero di progressivo nella prima colonna
                    progressivo_item = QTableWidgetItem(str(row_idx + 1))
                    progressivo_item.setFlags(progressivo_item.flags() & ~Qt.ItemIsEditable)
                    progressivo_item.setTextAlignment(Qt.AlignCenter)
                    progressivo_item.setBackground(QColor(60, 60, 60))
                    progressivo_item.setForeground(QColor(76, 175, 80))
                    self.db_table.setItem(row_idx, 0, progressivo_item)

                    # Aggiungi i dati nelle colonne successive
                    for col_idx, col_data in enumerate(row_data):
                        # Converti timestamp in data leggibile
                        if col_idx == 1 and col_data:  # Colonna mtime (ora è la seconda colonna dei dati)
                            try:
                                from datetime import datetime
                                dt = datetime.fromtimestamp(float(col_data))
                                display_data = dt.strftime("%d/%m/%Y %H:%M")
                            except:
                                display_data = str(col_data)
                        else:
                            display_data = str(col_data) if col_data else "N/A"

                        item = QTableWidgetItem(display_data)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                        # Trunca testo troppo lungo e aggiungi tooltip
                        if len(display_data) > 100:
                            item.setToolTip(display_data)
                            display_data = display_data[:100] + "..."
                            item.setText(display_data)

                        # Le colonne dei dati partono dalla 1 (la 0 è il progressivo)
                        self.db_table.setItem(row_idx, col_idx + 1, item)

                # Ridimensiona automaticamente le colonne al contenuto
                self.db_table.resizeColumnsToContents()
                # Mantieni dimensioni minime per alcune colonne
                self.db_table.setColumnWidth(0, 50)  # Progressivo
                self.db_table.setColumnWidth(5, 80)  # Anno
                self.db_table.setColumnWidth(9, 80)  # Durata
                self.db_table.setColumnWidth(10, 80)  # Rating

            # Se la tabella ha dati, evidenziala
            if count > 0:
                self.db_table.setStyleSheet("""
                    QTableWidget {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 2px solid #4CAF50;
                        border-radius: 5px;
                        gridline-color: #4CAF50;
                    }
                    /* ... [resto dello style] ... */
                """)
            else:
                self.db_table.setStyleSheet("""
                    QTableWidget {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 5px;
                        gridline-color: #555555;
                    }
                    /* ... [resto dello style] ... */
                """)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Errore DB", f"Errore accesso database: {str(e)}")

    def export_database(self):
        """Esporta il database in un file CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Esporta Database", "video_database.csv", "CSV Files (*.csv)"
            )

            if file_path:
                with sqlite3.connect(self.db.db_path) as conn:
                    import csv
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT path, mtime, title, genres, year, directors, 
                               plot, actors, duration, rating 
                        FROM videos
                    """)

                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Scrivi header
                        writer.writerow([
                            'Percorso', 'Data Modifica', 'Titolo', 'Generi', 'Anno',
                            'Registi', 'Trama', 'Attori', 'Durata', 'Rating'
                        ])

                        # Scrivi dati
                        for row in cursor.fetchall():
                            writer.writerow(row)

                    QMessageBox.information(self, "Esportazione Completata",
                                            f"Database esportato con successo in:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione: {str(e)}")

    def clear_database(self):
        reply = QMessageBox.question(self, "Conferma",
                                     "Vuoi cancellare TUTTI i dati dal database?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM videos")
                    conn.commit()
                self.refresh_db_view()
                QMessageBox.information(self, "Completato", "Database pulito!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Errore", f"Errore durante la pulizia: {str(e)}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella da Scansionare")
        if folder:
            self.scan_info_label.setText(f"Cartella selezionata: {folder}")
            # Piccolo delay per far vedere il messaggio
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.start_scan(folder))

    def start_scan(self, folder):
        self.btn_select_folder.setEnabled(False)
        self.scan_info_label.setText(f"Scansione in corso: {folder}")

        # Progress dialog senza bottone stop
        self.progress = QProgressDialog("Scansione in corso...", None, 0, 100, self)
        self.progress.setWindowTitle("Scansione Database")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)  # Rimuovi il bottone annulla
        self.progress.setStyleSheet("""
            QProgressDialog {
                background-color: #2b2b2b;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QProgressBar {
                border: 2px solid #4CAF50;
                border-radius: 5px;
                text-align: center;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        self.progress.show()

        self.scan_worker = ScanWorker(self.db, folder)
        self.scan_worker.progress_update.connect(self.update_progress)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def stop_scan(self):
        """Ferma la scansione"""
        if self.scan_worker:
            self.scan_worker.stop()
        self.progress.close()
        self.btn_select_folder.setEnabled(True)
        if hasattr(self, 'btn_stop_scan'):
            self.btn_stop_scan.deleteLater()

    def update_progress(self, current, total):
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        self.scan_info_label.setText(f"Scansione: {current}/{total} file processati")

    def on_scan_finished(self):
        self.progress.close()
        self.btn_select_folder.setEnabled(True)
        self.refresh_db_view()
        self.scan_info_label.setText("✅ Scansione completata con successo!")

        # Spostati automaticamente nel tab Genera Playlist
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(300, lambda: self.switch_to_playlist_tab(show_message=False))

        # Mostra messaggio di conferma
        QMessageBox.information(self, "Completato",
                                "Scansione terminata con successo!\n\n"
                                f"Trovati {self.db_table.rowCount()} video nel database.\n"
                                "Ora sei nella sezione Genera Playlist dove puoi creare le tue playlist."
                                )

    def switch_to_db_tab(self):
        """Cambia al tab Gestione DB"""
        try:
            # Cerca il tab Gestione DB
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "Gestione DB":
                    self.tabs.setCurrentIndex(i)

                    # Evidenzia il tab per attirare l'attenzione
                    self.highlight_db_tab()
                    break
        except:
            # Fallback
            self.tabs.setCurrentIndex(1)

        QMessageBox.information(self, "Completato",
                                "Scansione terminata con successo!\n\n"
                                "Ora sei nella sezione Gestione Database dove puoi visualizzare tutti i video caricati."
                                )

    def highlight_db_tab(self):
        """Evidenzia temporaneamente il tab Gestione DB"""
        try:
            # Salva lo stile originale
            original_style = self.tabs.tabBar().tabTextColor(1)

            # Evidenzia il tab
            self.tabs.tabBar().setTabTextColor(1, QColor(255, 255, 0))

            # Ripristina dopo 2 secondi
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.tabs.tabBar().setTabTextColor(1, original_style))

        except:
            pass

    def on_scan_error(self, error_msg):
        self.progress.close()
        self.btn_select_folder.setEnabled(True)
        self.scan_info_label.setText("❌ Errore durante la scansione")
        QMessageBox.critical(self, "Errore", f"Errore durante la scansione: {error_msg}")

    def generate_random_playlist(self, checked=False):
        """Genera playlist casuale chiedendo all'utente il numero di video"""
        limit, ok = QInputDialog.getInt(
            self, "Numero di video", "Quanti video vuoi includere?",
            value=20, min=1, max=1000, step=1
        )

        if not ok:
            return

        self.cleanup_vlc()

        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT path FROM videos ORDER BY RANDOM() LIMIT ?", (limit,))
                results = cursor.fetchall()
                self.current_playlist = [row[0] for row in results]

            if self.current_playlist:
                self.save_playlist_m3u("playlist.m3u")
               # QMessageBox.information(self, "Completato",
               #                        f"Playlist casuale generata con {len(self.current_playlist)} video!")
                self.btn_show_posters.setEnabled(True)
                self.btn_play_vlc.setEnabled(True)

                self.show_playlist_posters()
                self.play_with_vlc()
            else:
                QMessageBox.warning(self, "Attenzione", "Nessun video trovato!")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la generazione: {str(e)}")

        # Aggiorna lo status
        self.update_playlist_status()

    def generate_recent_playlist(self, checked=False):
        """Genera playlist con video recenti"""
        limit, ok = QInputDialog.getInt(
            self, "Numero di video", "Quanti video recenti vuoi includere?",
            value=20, min=1, max=1000, step=1
        )

        if not ok:
            return

        self.cleanup_vlc()

        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT path FROM videos ORDER BY mtime DESC LIMIT ?", (limit,))
                results = cursor.fetchall()
                self.current_playlist = [row[0] for row in results]

            if self.current_playlist:
                self.save_playlist_m3u("playlist.m3u")
                #QMessageBox.information(self, "Completato",
                #                        f"Playlist recenti generata con {len(self.current_playlist)} video!")
                # ABILITA i bottoni dopo la generazione
                self.btn_show_posters.setEnabled(True)
                self.btn_play_vlc.setEnabled(True)
                self.show_playlist_posters()
                self.play_with_vlc()
            else:
                QMessageBox.warning(self, "Attenzione", "Nessun video trovato!")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la generazione: {str(e)}")

        # Aggiorna lo status
        self.update_playlist_status()

    def show_manual_selection(self):
        """Mostra finestra per selezione manuale video con ricerca"""
        if not self.is_database_populated():
            QMessageBox.warning(self, "Attenzione", "Nessun video nel database!")
            return

        self.manual_dialog = QDialog(self)
        self.manual_dialog.setWindowTitle("Selezione Manuale Video - Ricerca")
        self.manual_dialog.resize(1000, 700)
        self.manual_dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                selection-background-color: #4CAF50;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)

        layout = QVBoxLayout(self.manual_dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Campo di ricerca
        search_layout = QHBoxLayout()

        search_label = QLabel("🔍 Cerca:")
        search_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca per titolo, anno, regista, genere...")
        self.search_input.textChanged.connect(self.filter_videos)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Contatore risultati
        self.result_count_label = QLabel("Caricamento...")
        self.result_count_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        layout.addWidget(self.result_count_label)

        # Tabella video
        self.manual_table = QTableWidget()
        self.manual_table.setColumnCount(4)
        self.manual_table.setHorizontalHeaderLabels(["Seleziona", "Titolo", "Anno", "Regista"])
        self.manual_table.setStyleSheet("""
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #555555;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        # Configurazione tabella
        self.manual_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.manual_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.manual_table.horizontalHeader().setStretchLastSection(True)
        self.manual_table.setColumnWidth(0, 80)  # Checkbox
        self.manual_table.setColumnWidth(1, 300)  # Titolo
        self.manual_table.setColumnWidth(2, 80)  # Anno
        self.manual_table.setColumnWidth(3, 200)  # Regista

        layout.addWidget(self.manual_table)

        # Pulsanti
        button_layout = QHBoxLayout()

        btn_select_all = QPushButton("Seleziona Tutti")
        btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_select_all.clicked.connect(self.select_all_videos)

        btn_deselect_all = QPushButton("Deseleziona Tutti")
        btn_deselect_all.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        btn_deselect_all.clicked.connect(self.deselect_all_videos)

        btn_confirm = QPushButton("Crea Playlist")
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_confirm.clicked.connect(lambda: self.create_manual_playlist(self.manual_table, self.all_videos))

        button_layout.addWidget(btn_select_all)
        button_layout.addWidget(btn_deselect_all)
        button_layout.addStretch()
        button_layout.addWidget(btn_confirm)

        layout.addLayout(button_layout)

        # Carica i video
        self.load_videos_for_selection()
        self.manual_dialog.exec_()

    def load_videos_for_selection(self):
        """Carica tutti i video per la selezione"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT path, title, year, directors, genres, plot 
                    FROM videos 
                    ORDER BY title
                """)
                self.all_videos = cursor.fetchall()

            self.filter_videos()  # Mostra tutti i video inizialmente

        except Exception as e:
            QMessageBox.critical(self.manual_dialog, "Errore", f"Errore nel caricamento video: {str(e)}")

    def filter_videos(self):
        """Filtra i video in base alla ricerca"""
        search_text = self.search_input.text().lower()

        if not hasattr(self, 'all_videos'):
            return

        filtered_videos = []
        for video in self.all_videos:
            path, title, year, directors, genres, plot = video
            searchable_text = f"{title or ''} {year or ''} {directors or ''} {genres or ''} {plot or ''}".lower()

            if search_text in searchable_text:
                filtered_videos.append(video)

        # Aggiorna la tabella
        self.manual_table.setRowCount(len(filtered_videos))

        for row, (path, title, year, directors, genres, plot) in enumerate(filtered_videos):
            # Checkbox
            checkbox = QCheckBox()
            self.manual_table.setCellWidget(row, 0, checkbox)

            # Titolo
            title_item = QTableWidgetItem(title or os.path.basename(path))
            title_item.setToolTip(title or os.path.basename(path))
            self.manual_table.setItem(row, 1, title_item)

            # Anno
            year_item = QTableWidgetItem(year or "N/A")
            year_item.setTextAlignment(Qt.AlignCenter)
            self.manual_table.setItem(row, 2, year_item)

            # Regista
            director_item = QTableWidgetItem(directors or "N/A")
            director_item.setToolTip(directors or "N/A")
            self.manual_table.setItem(row, 3, director_item)

        # Aggiorna contatore
        self.result_count_label.setText(f"Trovati {len(filtered_videos)} video su {len(self.all_videos)} totali")

    def select_all_videos(self):
        """Seleziona tutti i video visibili"""
        for row in range(self.manual_table.rowCount()):
            checkbox = self.manual_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def deselect_all_videos(self):
        """Deseleziona tutti i video visibili"""
        for row in range(self.manual_table.rowCount()):
            checkbox = self.manual_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def create_manual_playlist(self, table, videos):
        selected_paths = []
        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Trova il video corrispondente nella lista originale
                title_item = table.item(row, 1)
                if title_item:
                    # Cerca il video per titolo (approccio semplificato)
                    for video in videos:
                        if video[1] == title_item.text() or os.path.basename(video[0]) == title_item.text():
                            selected_paths.append(video[0])
                            break

        self.current_playlist = selected_paths
        if self.current_playlist:
            self.cleanup_vlc()
            self.save_playlist_m3u("playlist.m3u")
            QMessageBox.information(self, "Completato",
                                    f"Playlist manuale generata con {len(self.current_playlist)} video!")
            self.show_playlist_posters()
            self.play_with_vlc()
        else:
            QMessageBox.warning(self, "Attenzione", "Nessun video selezionato!")
        self.manual_dialog.close()

    def save_playlist_m3u(self, filename="playlist.m3u"):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for path in self.current_playlist:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT title FROM videos WHERE path=?", (path,))
                    title = cursor.fetchone()
                    display_title = title[0] if title and title[0] else os.path.basename(path)

                # Assicurati che il percorso sia in formato Windows corretto
                windows_path = path.replace('/', '\\')

                f.write(f"#EXTINF:-1,{display_title}\n")
                f.write(f"{windows_path}\n")

    def normalize_path_for_display(self, path):
        """Normalizza il percorso per la visualizzazione"""
        if platform.system() == "Windows":
            return path.replace('/', '\\')
        else:
            return path.replace('\\', '/')

    def play_with_vlc(self):
        if not self.current_playlist:
            QMessageBox.warning(self, "Attenzione", "Nessuna playlist generata!")
            return

        try:
            # PRIMA chiudi qualsiasi istanza VLC esistente
            self.cleanup_vlc()

            # Aspetta un momento per assicurarsi che VLC sia chiuso
            import time
            time.sleep(1)

            # Poi salva la playlist
            self.save_playlist_m3u("playlist.m3u")
            playlist_path = os.path.abspath("playlist.m3u")

            # Verifica se VLC è installato
            vlc_path = self.find_vlc_path()

            if vlc_path and os.path.exists(vlc_path):
                try:
                    # Avvia VLC con opzioni per evitare multiple istanze
                    subprocess.Popen([
                        vlc_path,
                        playlist_path,
                        '--playlist-autostart',
                        '--one-instance',  # Una sola istanza
                        '--playlist-enqueue',  # Aggiungi alla playlist esistente
                        '--qt-minimal-view'
                    ])

                    """
                    QMessageBox.information(self, "VLC Avviato",
                                            "VLC è stato avviato con la playlist.\n"
                                            "Se VLC era già aperto, la playlist è stata aggiunta."
                                            )
                    """

                except Exception as e:
                    print(f"Errore avvio VLC: {e}")
                    # Fallback: apri con programma predefinito
                    os.startfile(playlist_path)
            else:
                # Se VLC non è trovato, apri con programma predefinito
                os.startfile(playlist_path)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile avviare la riproduzione: {str(e)}")

    def show_playlist_ready_message(self, playlist_path):
        """Mostra messaggio con istruzioni"""
        message = (
            f"Playlist generata con {len(self.current_playlist)} video!\n"
            f"File salvato come: {playlist_path}\n\n"
            "Apri manualmente il file con VLC o altro player."
        )

        QMessageBox.information(self, "Playlist Pronta", message)

        # Apri la cartella contenente la playlist
        try:
            folder_path = os.path.dirname(playlist_path)
            os.startfile(folder_path)
        except:
            pass

    def find_vlc_path(self):
        """Trova il percorso di VLC su Windows in modo completo"""
        possible_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            r"D:\Program Files\VideoLAN\VLC\vlc.exe",
            r"E:\Program Files\VideoLAN\VLC\vlc.exe",
            r"vlc.exe",
        ]

        # Cerca nei percorsi di sistema
        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Cerca nel registro di Windows
        try:
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VideoLAN\VLC")
                install_dir = winreg.QueryValueEx(key, "InstallDir")[0]
                vlc_path = os.path.join(install_dir, "vlc.exe")
                if os.path.exists(vlc_path):
                    return vlc_path
            except:
                pass

            # Prova anche in HKEY_CURRENT_USER
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\VideoLAN\VLC")
                install_dir = winreg.QueryValueEx(key, "InstallDir")[0]
                vlc_path = os.path.join(install_dir, "vlc.exe")
                if os.path.exists(vlc_path):
                    return vlc_path
            except:
                pass
        except ImportError:
            pass

        # Ultimo tentativo: cerca nel PATH
        try:
            result = subprocess.run(["where", "vlc.exe"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        return None

    def show_playlist_ready_message(self):
        """Mostra messaggio con istruzioni per aprire la playlist"""
        playlist_path = os.path.abspath("playlist.m3u")

        message = (
            f"Playlist generata con {len(self.current_playlist)} video!\n"
            f"File salvato come: {playlist_path}\n\n"
        )

        if not self.check_vlc_installed():
            message += (
                "VLC non è installato o non trovato.\n"
                "Scarica VLC da: https://www.videolan.org/vlc/\n"
                "Dopo l'installazione, apri manualmente il file con VLC."
            )
        else:
            message += "Apri manualmente il file con VLC o altro player."

        QMessageBox.information(self, "Playlist Pronta", message)

        # Apri la cartella contenente la playlist
        try:
            if platform.system() == "Windows":
                os.startfile(os.path.dirname(playlist_path))
            else:
                subprocess.Popen(['open', os.path.dirname(playlist_path)])
        except:
            pass

    def show_playlist_posters(self):
        if not self.current_playlist:
            QMessageBox.warning(self, "Attenzione", "Nessuna playlist generata!")
            return

        self.poster_dialog = QDialog(self)
        self.poster_dialog.setWindowTitle("Poster Playlist")
        self.poster_dialog.resize(1000, 800)
        self.poster_dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #3c3c3c;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        scroll = QScrollArea()
        widget = QWidget()
        layout = QGridLayout(widget)

        row, col = 0, 0
        for path in self.current_playlist:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT title, poster FROM videos WHERE path=?", (path,))
                result = cursor.fetchone()
                title = result[0] if result else None
                poster_url = result[1] if result and len(result) > 1 else None

            # DEBUG: stampa l'URL del poster
            print(f"Video: {title}, Poster URL: {poster_url}")

            # Usa QPushButton invece di QLabel per il click
            poster_button = QPushButton()
            poster_button.setFixedSize(150, 200)
            poster_button.setStyleSheet("""
                QPushButton {
                    border: 1px solid gray; 
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)

            poster_button.clicked.connect(lambda checked, p=path: self.show_video_details(p))

            if poster_url:
                try:
                    # Verifica se l'URL è valido
                    if not poster_url.startswith(('http://', 'https://')):
                        print(f"URL non valido: {poster_url}")
                        poster_button.setText("URL\nnon valido")
                    else:
                        response = requests.get(poster_url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })

                        if response.status_code == 200:
                            pixmap = QPixmap()
                            success = pixmap.loadFromData(response.content)
                            if success:
                                icon = QIcon(pixmap.scaled(140, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                                poster_button.setIcon(icon)
                                poster_button.setIconSize(pixmap.rect().size())
                                print(f"Caricamento riuscito: {poster_url}")
                            else:
                                poster_button.setText("Formato\nnon supportato")
                                print(f"Formato immagine non supportato: {poster_url}")
                        else:
                            poster_button.setText(f"Errore\n{response.status_code}")
                            print(f"Errore HTTP {response.status_code}: {poster_url}")
                except Exception as e:
                    poster_button.setText("Errore\ncaricamento")
                    print(f"Errore durante il caricamento di {poster_url}: {e}")
            else:
                poster_button.setText("Nessuna\nimmagine")
                print(f"Nessun poster per: {title}")

            # Titolo
            title_label = QLabel(title or os.path.basename(path))
            title_label.setWordWrap(True)
            title_label.setFixedWidth(150)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("""
                QLabel {
                    color: #000000;  /* Cambiato da #ffffff a #000000 (nero) */
                    font-weight: bold;
                    background-color: #f0f0f0;
                    padding: 3px;
                    border-radius: 3px;
                    margin-top: 5px;
                }
            """)

            # Crea un container per bottone e titolo
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.addWidget(poster_button)
            container_layout.addWidget(title_label)
            container_layout.setAlignment(Qt.AlignCenter)

            layout.addWidget(container, row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1

        scroll.setWidget(widget)
        dialog_layout = QVBoxLayout(self.poster_dialog)
        dialog_layout.addWidget(scroll)
        self.poster_dialog.exec_()

    def load_poster_image(self, poster_url, poster_button, title):
        """Carica un'immagine del poster con vari fallback"""
        try:
            if not poster_url:
                poster_button.setText("Nessuna\nimmagine")
                return False

            # Se l'URL è un percorso locale
            if poster_url.startswith(('/', '\\')) or ':' in poster_url and not poster_url.startswith('http'):
                if os.path.exists(poster_url):
                    pixmap = QPixmap(poster_url)
                    if not pixmap.isNull():
                        icon = QIcon(pixmap.scaled(140, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        poster_button.setIcon(icon)
                        poster_button.setIconSize(pixmap.rect().size())
                        return True
                    else:
                        poster_button.setText("Formato\nnon supportato")
                        return False
                else:
                    poster_button.setText("File\nnon trovato")
                    return False

            # Se è un URL web
            elif poster_url.startswith(('http://', 'https://')):
                response = requests.get(poster_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code == 200:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(response.content):
                        icon = QIcon(pixmap.scaled(140, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        poster_button.setIcon(icon)
                        poster_button.setIconSize(pixmap.rect().size())
                        return True
                    else:
                        poster_button.setText("Formato\nnon supportato")
                        return False
                else:
                    poster_button.setText(f"Errore\n{response.status_code}")
                    return False
            else:
                poster_button.setText("URL\nnon valido")
                return False

        except Exception as e:
            poster_button.setText("Errore\ncaricamento")
            print(f"Errore caricamento poster {poster_url}: {e}")
            return False

    def on_poster_clicked(self, event):
        """Gestisce il click sui poster in modo sicuro"""
        try:
            # Ottieni il widget che ha generato l'evento
            clicked_widget = event.widget()

            # Cerca il frame padre che contiene il percorso del video
            parent_frame = clicked_widget.parent()
            while parent_frame and not hasattr(parent_frame, 'video_path'):
                parent_frame = parent_frame.parent()

            if parent_frame and hasattr(parent_frame, 'video_path'):
                self.show_video_details(parent_frame.video_path)
            else:
                # Fallback: cerca nella gerarchia dei widget
                current = clicked_widget
                while current:
                    if hasattr(current, 'video_path'):
                        self.show_video_details(current.video_path)
                        return
                    current = current.parent()

                QMessageBox.warning(self, "Errore", "Impossibile trovare il video selezionato")

        except Exception as e:
            print(f"Errore durante il click sul poster: {e}")
            QMessageBox.warning(self, "Errore", "Impossibile visualizzare i dettagli del video")

    def is_database_populated(self):
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM videos")
                count = cursor.fetchone()[0]
                return count > 0
        except sqlite3.Error:
            return False

    def cleanup_vlc(self):
        """Chiude qualsiasi istanza VLC attiva in modo completo"""
        try:
            # Prima chiudi gentilmente l'istanza python-vlc
            if self.vlc_player:
                try:
                    self.vlc_player.stop()
                    self.vlc_player.release()
                except:
                    pass
                finally:
                    self.vlc_player = None

            # Poi killa tutti i processi VLC
            self.kill_vlc_process()
            # Aggiorna lo status
            self.update_playlist_status()

        except Exception as e:
            print(f"Errore durante cleanup VLC: {e}")

    def _release_vlc(self):
        """Rilascia le risorse VLC"""
        try:
            if self.vlc_player:
                self.vlc_player.release()
        except:
            pass
        finally:
            self.vlc_player = None

        # Kill processo solo se necessario
        self.kill_vlc_process()

    def kill_vlc_process(self):
        """Termina forzatamente tutti i processi VLC"""
        try:
            system = platform.system()
            if system == "Windows":
                # Taskkill più aggressivo
                subprocess.run(["taskkill", "/f", "/im", "vlc.exe", "/t"],
                               capture_output=True, timeout=10)
                # Doppio kill per sicurezza
                subprocess.run(["taskkill", "/f", "/im", "vlc.exe", "/t"],
                               capture_output=True, timeout=5)
            else:
                subprocess.run(["pkill", "-9", "-f", "vlc"],
                               capture_output=True, timeout=10)
                subprocess.run(["pkill", "-9", "-f", "vlc"],
                               capture_output=True, timeout=5)
        except:
            pass

    def show_video_details(self, video_path):
        """Mostra i dettagli del video in una finestra accattivante"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM videos WHERE path=?", (video_path,))
                video_data = cursor.fetchone()

            if not video_data:
                QMessageBox.warning(self, "Errore", "Dettagli video non trovati")
                return

            details_dialog = QDialog(self)
            details_dialog.setWindowTitle("Dettagli Video")
            details_dialog.resize(650, 750)
            details_dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QLabel {
                    color: #ffffff;
                    padding: 2px;
                }
                QScrollArea {
                    border: none;
                    background-color: #3c3c3c;
                    border-radius: 5px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QScrollBar:vertical {
                    background: #3c3c3c;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #4CAF50;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #45a049;
                }
            """)

            main_layout = QVBoxLayout(details_dialog)
            main_layout.setSpacing(12)
            main_layout.setContentsMargins(20, 15, 20, 15)

            # Header con titolo
            title = video_data[3] or os.path.basename(video_path)
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: #4CAF50;
                    padding: 8px;
                    background-color: #3c3c3c;
                    border-radius: 5px;
                    text-align: center;
                    margin-bottom: 5px;
                }
            """)
            title_label.setWordWrap(True)
            title_label.setMaximumHeight(60)
            main_layout.addWidget(title_label)

            # Container principale
            content_widget = QWidget()
            content_layout = QHBoxLayout(content_widget)
            content_layout.setSpacing(20)

            # Colonna sinistra - Poster
            left_column = QVBoxLayout()
            left_column.setAlignment(Qt.AlignTop)
            left_column.setSpacing(10)

            poster_label = QLabel()
            poster_label.setAlignment(Qt.AlignCenter)
            poster_label.setFixedSize(270, 480)
            poster_label.setStyleSheet("""
                QLabel {
                    background-color: #3c3c3c;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)

            if len(video_data) > 11 and video_data[11]:
                try:
                    response = requests.get(video_data[11], timeout=10)
                    if response.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(response.content)
                        scaled_pixmap = pixmap.scaled(250, 460, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        poster_label.setPixmap(scaled_pixmap)
                    else:
                        poster_label.setText("🎬 Immagine\nnon disponibile")
                        poster_label.setAlignment(Qt.AlignCenter)
                except:
                    poster_label.setText("🎬 Errore\ncaricamento")
                    poster_label.setAlignment(Qt.AlignCenter)
            else:
                poster_label.setText("🎬 Nessuna\nimmagine")
                poster_label.setAlignment(Qt.AlignCenter)

            left_column.addWidget(poster_label)
            content_layout.addLayout(left_column)

            # Colonna destra - Dettagli
            right_column = QVBoxLayout()
            right_column.setSpacing(8)

            # Info principali in una griglia
            info_grid = QGridLayout()
            info_grid.setSpacing(6)

            details = [
                ("📅 Anno", video_data[5] or "N/A"),
                ("🎬 Regista", video_data[6] or "N/A"),
                ("🎭 Genere", video_data[4] or "N/A"),
                ("⏱️ Durata", f"{video_data[9] or 'N/A'} min"),
                ("⭐ Rating IMDb", video_data[10] or "N/A"),
            ]

            for i, (icon, value) in enumerate(details):
                icon_label = QLabel(icon)
                icon_label.setStyleSheet("font-size: 14px;")
                value_label = QLabel(value)
                value_label.setStyleSheet("font-weight: bold; font-size: 13px;")
                info_grid.addWidget(icon_label, i, 0)
                info_grid.addWidget(value_label, i, 1)

            right_column.addLayout(info_grid)

            # Percorso del file - CARATTERE 16px
            path_label = QLabel("📁 Percorso:")
            path_label.setStyleSheet("font-weight: bold; margin-top: 8px; font-size: 16px;")  # Aumentato a 16px
            right_column.addWidget(path_label)

            path_value = QLabel(video_path)
            path_value.setStyleSheet("""
                QLabel {
                    background-color: #3c3c3c;
                    padding: 6px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-size: 16px;  /* Aumentato da 10px a 16px */
                    margin-top: 2px;
                }
            """)
            path_value.setWordWrap(True)
            path_value.setMaximumHeight(50)
            right_column.addWidget(path_value)

            # Trama - con SCROLLBAR funzionante
            plot_label = QLabel("📖 Trama:")
            plot_label.setStyleSheet("font-weight: bold; margin-top: 8px; font-size: 16px;")  # Aumentato a 16px
            right_column.addWidget(plot_label)

            plot_text = video_data[7] or "Nessuna trama disponibile"

            # Crea un QTextEdit invece di QLabel per lo scrolling
            plot_textedit = QTextEdit()
            plot_textedit.setPlainText(plot_text)
            plot_textedit.setStyleSheet("""
                QTextEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #4CAF50;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 14px;
                    font-style: italic;
                    line-height: 1.4;
                }
                QTextEdit:focus {
                    border: 2px solid #4CAF50;
                }
            """)
            plot_textedit.setReadOnly(True)  # Solo lettura
            plot_textedit.setMaximumHeight(150)
            right_column.addWidget(plot_textedit)

            content_layout.addLayout(right_column)
            main_layout.addWidget(content_widget)

            # Bottoni in fondo
            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)

            btn_close = QPushButton("Chiudi")
            btn_close.clicked.connect(details_dialog.accept)
            btn_close.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    padding: 8px 18px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)

            btn_play = QPushButton("Riproduci Video")
            btn_play.clicked.connect(lambda: self.play_single_video(video_path))
            btn_play.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    padding: 8px 18px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)

            button_layout.addWidget(btn_play)
            button_layout.addStretch()
            button_layout.addWidget(btn_close)

            main_layout.addLayout(button_layout)

            details_dialog.exec_()

        except Exception as e:
            print(f"Errore nei dettagli video: {e}")
            QMessageBox.critical(self, "Errore", f"Impossibile visualizzare i dettagli: {str(e)}")

    def play_single_video(self, video_path):
        """Riproduce un singolo video"""
        try:
            self.cleanup_vlc()

            # Normalizza il percorso per Windows
            if platform.system() == "Windows":
                video_path = video_path.replace('/', '\\')

            # Crea una playlist temporanea con solo questo video
            temp_playlist = "temp_playlist.m3u"
            with open(temp_playlist, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"#EXTINF:-1,{os.path.basename(video_path)}\n")
                f.write(f"{video_path}\n")

            # Avvia VLC
            vlc_path = self.find_vlc_path()
            if vlc_path and os.path.exists(vlc_path):
                subprocess.Popen([vlc_path, temp_playlist, '--playlist-autostart'])
            else:
                os.startfile(video_path)  # Apri con programma predefinito

        except Exception as e:
            QMessageBox.warning(self, "Errore", f"Impossibile riprodurre il video: {str(e)}")

    def update_playlist_status(self):
        """Aggiorna lo status della playlist"""
        if self.current_playlist:
            status_text = f"🎵 Playlist attiva: {len(self.current_playlist)} video\n"
            status_text += f"📁 File: playlist.m3u"
            self.playlist_status.setText(status_text)

            # Cambia colore per stato attivo
            self.playlist_status.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #4CAF50;
                    padding: 10px;
                    background-color: #2b2b2b;
                    border-radius: 5px;
                    text-align: center;
                    border: 2px solid #4CAF50;
                }
            """)
        else:
            self.playlist_status.setText("Nessuna playlist generata")
            self.playlist_status.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #cccccc;
                    padding: 10px;
                    background-color: #2b2b2b;
                    border-radius: 5px;
                    text-align: center;
                }
            """)

    def closeEvent(self, event):
        """Chiudi VLC quando l'applicazione viene chiusa"""
        self.cleanup_vlc()
        event.accept()