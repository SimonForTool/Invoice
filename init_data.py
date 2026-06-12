"""
Inicializace dat pro rok 2026.
Vytvoří data/2026.json s předvyplněnými pracovními dny.
"""
import json
from datetime import date, timedelta
from pathlib import Path

HOLIDAYS = {
    date(2026, 1, 1):  "Nový rok",
    date(2026, 4, 3):  "Velký pátek",
    date(2026, 4, 6):  "Velikonoční pondělí",
    date(2026, 5, 1):  "Svátek práce",
    date(2026, 5, 8):  "Den vítězství",
    date(2026, 7, 5):  "Cyril a Metoděj",
    date(2026, 7, 6):  "Jan Hus",
    date(2026, 9, 28): "Den české státnosti",
    date(2026, 10, 28): "Den vzniku ČSR",
    date(2026, 11, 17): "Den boje za svobodu",
    date(2026, 12, 24): "Štědrý den",
    date(2026, 12, 25): "1. svátek vánoční",
    date(2026, 12, 26): "2. svátek vánoční",
}

DEFAULT_START = "12:00"
DEFAULT_END   = "20:00"

def build_year(year: int) -> dict:
    months = {}
    d = date(year, 1, 1)
    while d.year == year:
        if d.weekday() < 5:  # Po–Pá
            m = str(d.month)
            if m not in months:
                months[m] = {"days": []}
            if d in HOLIDAYS:
                months[m]["days"].append({
                    "date": d.isoformat(),
                    "type": "holiday",
                    "holiday_name": HOLIDAYS[d],
                    "start": None,
                    "end": None,
                })
            else:
                months[m]["days"].append({
                    "date": d.isoformat(),
                    "type": "work",
                    "start": DEFAULT_START,
                    "end": DEFAULT_END,
                })
        d += timedelta(days=1)
    return {
        "year": year,
        "rate": 400,
        "months": months,
    }

if __name__ == "__main__":
    data = build_year(2026)
    path = Path("data/2026.json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Vytvořeno: {path}")
