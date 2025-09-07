from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, QScrollArea,
                             QLabel, QLineEdit, QSlider, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIntValidator
import sqlite3


class BaseFilterWidget(QWidget):
    """Widget base per tutti i filtri"""

    def __init__(self, title, db_path):
        super().__init__()from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, QScrollArea,
                             QLabel, QLineEdit, QSlider, QHBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIntValidator
import sqlite3


class BaseFilterWidget(QWidget):
    """Widget base per tutti i filtri"""

    def __init__(self, title, db_path):
        super().__init__()
        self.db_path = db_path
        self.setup_ui(title)

    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        layout.addWidget(title_label)

        self.setup_content(layout)

    def setup_content(self, layout):
        """Metodo astratto da implementare nelle classi figlie"""
        pass

    def get_selected_values(self):
        """Restituisce i valori selezionati"""
        return []


class MultiSelectFilterWidget(BaseFilterWidget):
    """Widget per selezione multipla (generi, attori, registi, anni)"""

    def __init__(self, title, db_path, column_name):
        self.column_name = column_name
        self.list_widget = None
        super().__init__(title, db_path)

    def setup_content(self, layout):
        # Campo di ricerca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca...")
        self.search_input.textChanged.connect(self.filter_items)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.search_input)

        # ListWidget per selezione multipla
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.list_widget.setMaximumHeight(150)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #2b2b2b;
                color: #cccccc;
                font-size: 11px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        layout.addWidget(self.list_widget)

        # Carica i valori
        self.load_values()

    def load_values(self):
        """Carica i valori dal database"""
        try:
            # Verifica se la tabella esiste
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
                if not cursor.fetchone():
                    print("Tabella 'videos' non trovata nel database")
                    self.all_values = []
                    self.display_values([])
                    return

                if self.column_name == 'actors':
                    # APPROCCIO SICURO per attori
                    cursor.execute("""
                                   WITH RECURSIVE split(value, rest) AS (SELECT '',
                                                                                actors || ','
                                                                         FROM videos
                                                                         WHERE actors IS NOT NULL
                                                                           AND actors != ''

                                   UNION ALL

                                   SELECT TRIM(SUBSTR(rest, 1, INSTR(rest, ',') - 1)),
                                          SUBSTR(rest, INSTR(rest, ',') + 1)
                                   FROM split
                                   WHERE rest != ''
                        )
                                   SELECT DISTINCT value
                                   FROM split
                                   WHERE value != '' AND value IS NOT NULL
                                   ORDER BY value
                                   """)
                elif self.column_name in ['genres', 'directors']:
                    # Usa json_each per generi e registi
                    cursor.execute(f"""
                        SELECT DISTINCT TRIM(value) 
                        FROM videos, 
                        json_each('["' || REPLACE({self.column_name}, ',', '","') || '"]') 
                        WHERE {self.column_name} IS NOT NULL AND {self.column_name} != ''
                        ORDER BY value
                    """)
                else:
                    cursor.execute(f"""
                        SELECT DISTINCT {self.column_name} 
                        FROM videos 
                        WHERE {self.column_name} IS NOT NULL AND {self.column_name} != ''
                        ORDER BY {self.column_name}
                    """)

                self.all_values = [str(row[0]) for row in cursor.fetchall() if row[0]]
                self.display_values(self.all_values)

        except Exception as e:
            print(f"Errore caricamento {self.column_name}: {e}")
            self.all_values = []
            self.display_values([])

    def display_values(self, values):
        """Mostra i valori nella lista"""
        self.list_widget.clear()

        for value in sorted(values):
            item = QListWidgetItem(value)
            self.list_widget.addItem(item)

    def filter_items(self, text):
        """Filtra gli elementi in base al testo di ricerca"""
        search_text = text.lower()
        if not search_text:
            self.display_values(self.all_values)
        else:
            filtered = [v for v in self.all_values if search_text in v.lower()]
            self.display_values(filtered)

    def get_selected_values(self):
        """Restituisce i valori selezionati"""
        selected_items = self.list_widget.selectedItems()
        return [item.text() for item in selected_items]


class YearFilterWidget(MultiSelectFilterWidget):
    """Widget per selezione anni (eredita da MultiSelectFilterWidget)"""

    def __init__(self, title, db_path):
        super().__init__(title, db_path, "year")


class RatingFilterWidget(BaseFilterWidget):
    """Widget per filtro rating minimo"""

    def setup_content(self, layout):
        slider_layout = QHBoxLayout()

        self.rating_slider = QSlider(Qt.Horizontal)
        self.rating_slider.setRange(0, 100)  # 0-10 con step 0.1
        self.rating_slider.setValue(0)
        self.rating_slider.valueChanged.connect(self.update_label)

        self.rating_label = QLabel("0.0")
        self.rating_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.rating_label.setFixedWidth(30)

        slider_layout.addWidget(QLabel("Rating min:"))
        slider_layout.addWidget(self.rating_slider)
        slider_layout.addWidget(self.rating_label)

        layout.addLayout(slider_layout)

    def update_label(self, value):
        """Aggiorna label con valore slider"""
        self.rating_label.setText(f"{value / 10:.1f}")

    def get_selected_values(self):
        """Restituisce rating minimo"""
        return self.rating_slider.value() / 10.0


# Test del modulo MIGLIORATO
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

    app = QApplication(sys.argv)

    # Crea una finestra di test migliore
    window = QMainWindow()
    window.setWindowTitle("Test Filtri - Simulazione Database Popolato")
    window.resize(400, 600)

    tab_widget = QTabWidget()
    window.setCentralWidget(tab_widget)

    # Simula database popolato per test
    import tempfile
    import sqlite3

    # Crea database temporaneo di test
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name

        # Crea tabella con dati di esempio
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE videos
                           (
                               id        INTEGER PRIMARY KEY,
                               path      TEXT,
                               title     TEXT,
                               genres    TEXT,
                               year      TEXT,
                               directors TEXT,
                               actors    TEXT,
                               rating    TEXT
                           )
                           """)

            # Inserisci dati di esempio
            sample_data = [
                ("/path/to/movie1.mp4", "Matrix", "Azione,Fantascienza", "1999", "Lana Wachowski", "Keanu Reeves",
                 "8.7"),
                ("/path/to/movie2.mp4", "Forrest Gump", "Drammatico,Commedia", "1994", "Robert Zemeckis", "Tom Hanks",
                 "8.8"),
                ("/path/to/movie3.mp4", "Il Padrino", "Drammatico,Crime", "1972", "Francis Ford Coppola",
                 "Marlon Brando", "9.2"),
                ("/path/to/movie4.mp4", "Inception", "Azione,Fantascienza", "2010", "Christopher Nolan",
                 "Leonardo DiCaprio", "8.8"),
                ("/path/to/movie5.mp4", "Pulp Fiction", "Crime,Drammatico", "1994", "Quentin Tarantino",
                 "John Travolta", "8.9")
            ]

            for data in sample_data:
                cursor.execute(
                    "INSERT INTO videos (path, title, genres, year, directors, actors, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    data)

            conn.commit()

    # Test tutti i widget
    genres_widget = MultiSelectFilterWidget("🎬 Generi", db_path, "genres")
    actors_widget = MultiSelectFilterWidget("🎭 Attori", db_path, "actors")
    directors_widget = MultiSelectFilterWidget("🎥 Registi", db_path, "directors")
    years_widget = YearFilterWidget("📅 Anni", db_path)
    rating_widget = RatingFilterWidget("⭐ Rating Minimo", db_path)

    # Aggiungi tabs
    tab_widget.addTab(genres_widget, "Generi")
    tab_widget.addTab(actors_widget, "Attori")
    tab_widget.addTab(directors_widget, "Registi")
    tab_widget.addTab(years_widget, "Anni")
    tab_widget.addTab(rating_widget, "Rating")

    window.show()


    # Pulizia a fine test
    def cleanup():
        import os
        os.unlink(db_path)
        app.quit()


    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec_())
        self.db_path = db_path
        self.setup_ui(title)

    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        layout.addWidget(title_label)

        self.setup_content(layout)

    def setup_content(self, layout):
        """Metodo astratto da implementare nelle classi figlie"""
        pass

    def get_selected_values(self):
        """Restituisce i valori selezionati"""
        return []


class MultiSelectFilterWidget(BaseFilterWidget):
    """Widget per selezione multipla (generi, attori, registi)"""

    def __init__(self, title, db_path, column_name):
        self.column_name = column_name
        self.checkboxes = []
        super().__init__(title, db_path)

    def setup_content(self, layout):
        # Campo di ricerca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca...")
        self.search_input.textChanged.connect(self.filter_items)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.search_input)

        # Area scrollabile per i checkbox
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #2b2b2b;
            }
        """)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setSpacing(2)

        scroll_area.setWidget(self.container_widget)
        layout.addWidget(scroll_area)

        # Carica i valori
        self.load_values()

    def load_values(self):
        """Carica i valori dal database"""
        try:
            # Verifica se la tabella esiste
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
                if not cursor.fetchone():
                    print("Tabella 'videos' non trovata nel database")
                    self.all_values = []
                    self.display_values([])
                    return

                if self.column_name in ['genres', 'actors', 'directors']:
                    cursor.execute(f"""
                        SELECT DISTINCT TRIM(value) 
                        FROM videos, 
                        json_each('["' || REPLACE({self.column_name}, ',', '","') || '"]') 
                        WHERE {self.column_name} IS NOT NULL AND {self.column_name} != ''
                        ORDER BY value
                    """)
                else:
                    cursor.execute(f"""
                        SELECT DISTINCT {self.column_name} 
                        FROM videos 
                        WHERE {self.column_name} IS NOT NULL AND {self.column_name} != ''
                        ORDER BY {self.column_name}
                    """)

                self.all_values = [row[0] for row in cursor.fetchall() if row[0]]
                self.display_values(self.all_values)

        except Exception as e:
            print(f"Errore caricamento {self.column_name}: {e}")
            self.all_values = []
            self.display_values([])

    def display_values(self, values):
        """Mostra i valori nella lista"""
        # Pulisci layout esistente
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.checkboxes = []

        for value in sorted(values):
            checkbox = QCheckBox(value)
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #cccccc;
                    font-size: 11px;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border: 1px solid #45a049;
                }
            """)
            self.container_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

    def filter_items(self, text):
        """Filtra gli elementi in base al testo di ricerca"""
        search_text = text.lower()
        if not search_text:
            self.display_values(self.all_values)
        else:
            filtered = [v for v in self.all_values if search_text in v.lower()]
            self.display_values(filtered)

    def get_selected_values(self):
        """Restituisce i valori selezionati"""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


class YearFilterWidget(BaseFilterWidget):
    """Widget per selezione anni"""

    def setup_content(self, layout):
        min_year, max_year = 1900, 2024

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
                if cursor.fetchone():
                    cursor.execute("""
                                   SELECT MIN(CAST(year AS INTEGER)), MAX(CAST(year AS INTEGER))
                                   FROM videos
                                   WHERE year IS NOT NULL AND year != ''
                                   """)
                    result = cursor.fetchone()
                    if result and result[0] and result[1]:
                        min_year, max_year = result

        except:
            pass

        years_layout = QHBoxLayout()

        self.year_from = QLineEdit(str(min_year))
        self.year_to = QLineEdit(str(max_year))

        for input_field in [self.year_from, self.year_to]:
            input_field.setPlaceholderText("Anno")
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 4px;
                    font-size: 11px;
                    max-width: 60px;
                }
            """)
            input_field.setValidator(QIntValidator(1900, 2100))

        years_layout.addWidget(QLabel("Da:"))
        years_layout.addWidget(self.year_from)
        years_layout.addWidget(QLabel("A:"))
        years_layout.addWidget(self.year_to)
        years_layout.addStretch()

        layout.addLayout(years_layout)

    def get_selected_values(self):
        """Restituisce range anni selezionati"""
        try:
            year_from = int(self.year_from.text()) if self.year_from.text() else None
            year_to = int(self.year_to.text()) if self.year_to.text() else None

            if year_from and year_to:
                return list(range(year_from, year_to + 1))
            elif year_from:
                return [year_from]
            elif year_to:
                return [year_to]
        except:
            pass
        return []


class RatingFilterWidget(BaseFilterWidget):
    """Widget per filtro rating minimo"""

    def setup_content(self, layout):
        slider_layout = QHBoxLayout()

        self.rating_slider = QSlider(Qt.Horizontal)
        self.rating_slider.setRange(0, 100)  # 0-10 con step 0.1
        self.rating_slider.setValue(0)
        self.rating_slider.valueChanged.connect(self.update_label)

        self.rating_label = QLabel("0.0")
        self.rating_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.rating_label.setFixedWidth(30)

        slider_layout.addWidget(QLabel("Rating min:"))
        slider_layout.addWidget(self.rating_slider)
        slider_layout.addWidget(self.rating_label)

        layout.addLayout(slider_layout)

    def update_label(self, value):
        """Aggiorna label con valore slider"""
        self.rating_label.setText(f"{value / 10:.1f}")

    def get_selected_values(self):
        """Restituisce rating minimo"""
        return self.rating_slider.value() / 10.0


# Test del modulo MIGLIORATO
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

    app = QApplication(sys.argv)

    # Crea una finestra di test migliore
    window = QMainWindow()
    window.setWindowTitle("Test Filtri - Simulazione Database Popolato")
    window.resize(400, 600)

    tab_widget = QTabWidget()
    window.setCentralWidget(tab_widget)

    # Simula database popolato per test
    import tempfile
    import sqlite3

    # Crea database temporaneo di test
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_db:
        db_path = tmp_db.name

        # Crea tabella con dati di esempio
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE videos
                           (
                               id        INTEGER PRIMARY KEY,
                               path      TEXT,
                               title     TEXT,
                               genres    TEXT,
                               year      TEXT,
                               directors TEXT,
                               actors    TEXT,
                               rating    TEXT
                           )
                           """)

            # Inserisci dati di esempio
            sample_data = [
                ("/path/to/movie1.mp4", "Matrix", "Azione,Fantascienza", "1999", "Lana Wachowski", "Keanu Reeves",
                 "8.7"),
                ("/path/to/movie2.mp4", "Forrest Gump", "Drammatico,Commedia", "1994", "Robert Zemeckis", "Tom Hanks",
                 "8.8"),
                ("/path/to/movie3.mp4", "Il Padrino", "Drammatico,Crime", "1972", "Francis Ford Coppola",
                 "Marlon Brando", "9.2"),
                ("/path/to/movie4.mp4", "Inception", "Azione,Fantascienza", "2010", "Christopher Nolan",
                 "Leonardo DiCaprio", "8.8"),
                ("/path/to/movie5.mp4", "Pulp Fiction", "Crime,Drammatico", "1994", "Quentin Tarantino",
                 "John Travolta", "8.9")
            ]

            for data in sample_data:
                cursor.execute(
                    "INSERT INTO videos (path, title, genres, year, directors, actors, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    data)

            conn.commit()

    # Test tutti i widget
    genres_widget = MultiSelectFilterWidget("🎬 Generi", db_path, "genres")
    actors_widget = MultiSelectFilterWidget("🎭 Attori", db_path, "actors")
    directors_widget = MultiSelectFilterWidget("🎥 Registi", db_path, "directors")
    years_widget = YearFilterWidget("📅 Anni", db_path)
    rating_widget = RatingFilterWidget("⭐ Rating Minimo", db_path)

    # Aggiungi tabs
    tab_widget.addTab(genres_widget, "Generi")
    tab_widget.addTab(actors_widget, "Attori")
    tab_widget.addTab(directors_widget, "Registi")
    tab_widget.addTab(years_widget, "Anni")
    tab_widget.addTab(rating_widget, "Rating")

    window.show()


    # Pulizia a fine test
    def cleanup():
        import os
        os.unlink(db_path)
        app.quit()


    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec_())
