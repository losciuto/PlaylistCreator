import sqlite3
import os
from .nfo_parser import parse_nfo_file

class VideoDatabase:
    def __init__(self, db_path="video_cache.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE,
                    mtime REAL,
                    title TEXT,
                    genres TEXT,
                    year TEXT,
                    directors TEXT,
                    plot TEXT,
                    actors TEXT,
                    duration TEXT,
                    rating TEXT,
                    poster TEXT
                )
            """)
            conn.commit()

    def upsert_video(self, path, mtime, title=None, genres=None, year=None,
                     directors=None, plot=None, actors=None, duration=None,
                     rating=None, poster=None):
        # Assicurati che il percorso sia normalizzato
        path = self.normalize_windows_path(path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO videos 
                (path, mtime, title, genres, year, directors, plot, actors, duration, rating, poster)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (path, mtime, title, genres, year, directors, plot, actors, duration, rating, poster))
            conn.commit()

    def scan_and_update(self, video_path):
        if not os.path.exists(video_path):
            return False

        # Converti il percorso in formato Windows corretto
        video_path = self.normalize_windows_path(video_path)

        # Gestisci casi particolari di file corrotti o molto grandi
        try:
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                print(f"File vuoto saltato: {video_path}")
                return False
            if file_size > 50 * 1024 * 1024 * 1024:  # 50GB
                print(f"File troppo grande saltato: {video_path}")
                return False

        except OSError:
            return False

        mtime = os.path.getmtime(video_path)
        nfo_path = os.path.splitext(video_path)[0] + '.nfo'
        metadata = parse_nfo_file(nfo_path) if os.path.exists(nfo_path) else {}

        self.upsert_video(
            path=video_path,
            mtime=mtime,
            title=metadata.get('title'),
            genres=",".join(metadata.get('genres', [])),
            year=metadata.get('year'),
            directors=",".join(metadata.get('directors', [])),
            plot=metadata.get('plot'),
            actors=",".join(metadata.get('actors', [])),
            duration=metadata.get('duration'),
            rating=metadata.get('rating'),
            poster=metadata.get('poster')
        )
        return True

    def normalize_windows_path(self, path):
        """Normalizza il percorso per Windows"""
        # Converti slash in backslash
        normalized = path.replace('/', '\\')

        # Gestisci il caso di doppi backslash all'inizio
        if normalized.startswith('\\\\'):
            # Percorso di rete, mantieni così
            return normalized
        elif ':' in normalized:
            # Percorso assoluto con unità (es: C:\ o D:\)
            parts = normalized.split(':', 1)
            if len(parts) == 2:
                drive = parts[0] + ':'
                rest = parts[1].replace('/', '\\').lstrip('\\')
                return drive + '\\' + rest if rest else drive + '\\'

        return normalized

    def scan_directory(self, directory_path):
        # Estensioni video supportate - AGGIORNATE
        video_extensions = (
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.mpg', '.mpeg', '.m2v', '.m4v', '.ts', '.mts', '.m2ts',
            '.vob', '.ogv', '.ogg', '.drc', '.gif', '.gifv', '.mng',
            '.qt', '.yuv', '.rm', '.rmvb', '.asf', '.amv', '.divx',
            '.3gp', '.3g2', '.mxf', '.roq', '.nsv', '.f4v', '.f4p',
            '.f4a', '.f4b'
        )
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(video_extensions):
                    video_path = os.path.join(root, file)
                    self.scan_and_update(video_path)