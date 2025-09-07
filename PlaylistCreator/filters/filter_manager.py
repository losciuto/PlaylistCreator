import json
import os
from dataclasses import dataclass, asdict, field
from typing import List
from pathlib import Path


@dataclass
class FilterSettings:
    """Configurazione persistente dei filtri"""
    genres: List[str] = field(default_factory=list)
    years: List[int] = field(default_factory=list)
    rating_min: float = 0.0
    actors: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    enabled: bool = False


class FilterManager:
    """Gestisce lo stato persistente dei filtri"""
    _instance = None
    _config_path = Path("filters_config.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FilterManager, cls).__new__(cls)
            cls._instance._filters = FilterSettings()
            cls._instance.load_filters()
        return cls._instance

    def save_filters(self, filters: FilterSettings) -> None:
        """Salva i filtri su file JSON"""
        try:
            self._filters = filters
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(filters), f, indent=2, ensure_ascii=False)
            print("✅ Filtri salvati correttamente")
        except Exception as e:
            print(f"❌ Errore salvataggio filtri: {e}")

    def load_filters(self) -> FilterSettings:
        """Carica i filtri dal file JSON"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._filters = FilterSettings(**data)
                print("✅ Filtri caricati correttamente")
            else:
                print("ℹ️ Nessun file di configurazione trovato, uso defaults")
            return self._filters
        except Exception as e:
            print(f"❌ Errore caricamento filtri: {e}")
            return FilterSettings()

    def get_current_filters(self) -> FilterSettings:
        """Restituisce i filtri correnti"""
        return self._filters

    def reset_filters(self) -> None:
        """Resetta tutti i filtri"""
        self._filters = FilterSettings()
        try:
            if self._config_path.exists():
                os.remove(self._config_path)
                print("✅ Filtri resettati e file rimosso")
            else:
                print("✅ Filtri resettati")
        except Exception as e:
            print(f"❌ Errore reset filtri: {e}")

    def are_filters_active(self) -> bool:
        """Verifica se ci sono filtri attivi"""
        return (self._filters.enabled and
                (len(self._filters.genres) > 0 or
                 len(self._filters.years) > 0 or
                 self._filters.rating_min > 0 or
                 len(self._filters.actors) > 0 or
                 len(self._filters.directors) > 0))


# Test del modulo CORRETTO
if __name__ == "__main__":
    print("=" * 50)
    print("TEST FILTER MANAGER")
    print("=" * 50)

    # Reset completo per test pulito
    if Path("filters_config.json").exists():
        os.remove("filters_config.json")

    # Test 1: Istanza Singleton
    print("\n1. Test Singleton:")
    fm1 = FilterManager()
    fm2 = FilterManager()
    print(f"Istanza 1: {id(fm1)}")
    print(f"Istanza 2: {id(fm2)}")
    print("Singleton funziona:", fm1 is fm2)

    # Test 2: Salvataggio filtri
    print("\n2. Test Salvataggio:")
    test_filters = FilterSettings(
        genres=["Azione", "Commedia"],
        years=[2010, 2020],
        rating_min=7.5,
        actors=["Robert De Niro"],
        directors=["Christopher Nolan"],
        enabled=True
    )

    fm1.save_filters(test_filters)
    current = fm1.get_current_filters()
    print("Filtri correnti:", current)

    # Test 3: Caricamento filtri
    print("\n3. Test Caricamento:")
    fm3 = FilterManager()  # Nuova istanza dovrebbe caricare da file
    loaded = fm3.get_current_filters()
    print("Filtri caricati:", loaded)
    print("Filtri attivi?", fm3.are_filters_active())

    # Test 4: Reset filtri
    print("\n4. Test Reset:")
    fm3.reset_filters()
    reset = fm3.get_current_filters()
    print("Dopo reset:", reset)
    print("Filtri attivi?", fm3.are_filters_active())

    print("\n" + "=" * 50)
    print("TEST COMPLETATO")
    print("=" * 50)