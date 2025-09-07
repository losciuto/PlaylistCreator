import sqlite3
from typing import List, Tuple, Any

# Import assoluto
try:
    from filters.filter_manager import FilterSettings
except ImportError:
    # Fallback per quando si esegue il file direttamente
    from filter_manager import FilterSettings


class FilterQueryBuilder:
    """Costruisce query SQL con filtri applicati"""

    @staticmethod
    def build_filtered_query(filters: FilterSettings) -> Tuple[str, List[Any]]:
        """
        Costruisce query SQL e parametri basati sui filtri

        Returns:
            Tuple[str, List]: (query_sql, lista_parametri)
        """
        base_query = "SELECT path FROM videos WHERE 1=1"
        params = []

        # Filtro Generi
        if filters.genres:
            genre_conditions = []
            for genre in filters.genres:
                genre_conditions.append("genres LIKE ?")
                params.append(f"%{genre}%")
            base_query += f" AND ({' OR '.join(genre_conditions)})"

        # Filtro Anni
        if filters.years:
            year_conditions = []
            for year in filters.years:
                year_conditions.append("year = ?")
                params.append(str(year))
            base_query += f" AND ({' OR '.join(year_conditions)})"

        # Filtro Rating Minimo
        if filters.rating_min > 0:
            base_query += " AND CAST(rating AS REAL) >= ?"
            params.append(filters.rating_min)

        # Filtro Attori
        if filters.actors:
            actor_conditions = []
            for actor in filters.actors:
                actor_conditions.append("actors LIKE ?")
                params.append(f"%{actor}%")
            base_query += f" AND ({' OR '.join(actor_conditions)})"

        # Filtro Registi
        if filters.directors:
            director_conditions = []
            for director in filters.directors:
                director_conditions.append("directors LIKE ?")
                params.append(f"%{director}%")
            base_query += f" AND ({' OR '.join(director_conditions)})"

        # Aggiungi ordinamento randomico
        base_query += " ORDER BY RANDOM()"

        return base_query, params

    @staticmethod
    def get_available_values(column_name: str, db_path: str) -> List[str]:
        """
        Restituisce valori unici disponibili per una colonna

        Args:
            column_name: Nome colonna (genres, year, actors, directors)
            db_path: Percorso database SQLite

        Returns:
            List[str]: Lista di valori unici
        """
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                if column_name == 'genres':
                    # Special handling per generi separati da virgola
                    cursor.execute("""
                        SELECT DISTINCT TRIM(genre) 
                        FROM videos, 
                        json_each('["' || REPLACE(genres, ',', '","') || '"]') AS genre 
                        WHERE genres IS NOT NULL AND genres != ''
                        ORDER BY genre
                    """)
                elif column_name == 'actors':
                    # Special handling per attori separati da virgola
                    cursor.execute("""
                        SELECT DISTINCT TRIM(actor) 
                        FROM videos, 
                        json_each('["' || REPLACE(actors, ',', '","') || '"]') AS actor 
                        WHERE actors IS NOT NULL AND actors != ''
                        ORDER BY actor
                    """)
                elif column_name == 'directors':
                    # Special handling per registi separati da virgola
                    cursor.execute("""
                        SELECT DISTINCT TRIM(director) 
                        FROM videos, 
                        json_each('["' || REPLACE(directors, ',', '","') || '"]') AS director 
                        WHERE directors IS NOT NULL AND directors != ''
                        ORDER BY director
                    """)
                else:
                    # Per colonne normali (year, rating)
                    cursor.execute(f"""
                        SELECT DISTINCT {column_name} 
                        FROM videos 
                        WHERE {column_name} IS NOT NULL AND {column_name} != ''
                        ORDER BY {column_name}
                    """)

                results = [row[0] for row in cursor.fetchall() if row[0]]
                return results

        except Exception as e:
            print(f"Errore recupero valori per {column_name}: {e}")
            return []


# Test del modulo
if __name__ == "__main__":
    print("=" * 50)
    print("TEST FILTER QUERY BUILDER")
    print("=" * 50)

    # Test query building
    test_filters = FilterSettings(
        genres=["Azione", "Commedia"],
        years=[2010, 2020],
        rating_min=7.5,
        actors=["Robert De Niro"],
        directors=["Christopher Nolan"],
        enabled=True
    )

    query, params = FilterQueryBuilder.build_filtered_query(test_filters)
    print("Query generata:")
    print(query)
    print("\nParametri:")
    print(params)

    print("\n" + "=" * 50)
    print("TEST COMPLETATO")
    print("=" * 50)