"""
Generátor PDF výkazu práce.
Použití:
  python3 generate_pdf.py --month 6 --year 2026
  python3 generate_pdf.py  (automaticky předchozí měsíc)
"""
import argparse
import base64
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

MESICE = {
    1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben",
    5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen",
    9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec",
}

def last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)

def hours_from_times(start: str, end: str) -> int:
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return (eh * 60 + em - sh * 60 - sm) // 60

def load_data(year: int) -> dict:
    path = Path(f"data/{year}.json")
    if not path.exists():
        sys.exit(f"Data soubor {path} neexistuje. Spusťte nejprve init_data.py")
    return json.loads(path.read_text())

def get_signature_b64() -> str | None:
    for ext in ("png", "jpg", "jpeg"):
        p = Path(f"static/signature.{ext}")
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
    return None

def generate(year: int, month: int, output_dir: Path = Path("output")) -> Path:
    data = load_data(year)
    month_data = data["months"].get(str(month), {})
    rate = data.get("rate", 400)

    worked_days = []
    for d in month_data.get("days", []):
        if d["type"] != "work":
            continue
        h = hours_from_times(d["start"], d["end"])
        worked_days.append({
            "date":  date.fromisoformat(d["date"]).strftime("%d.%m.%Y"),
            "start": d["start"],
            "end":   d["end"],
            "hours": h,
        })

    total_hours = sum(d["hours"] for d in worked_days)
    last_day = last_day_of_month(year, month).strftime("%d.%m.%Y")

    env = Environment(loader=FileSystemLoader("templates"))
    tmpl = env.get_template("vykaz.html")
    html_str = tmpl.render(
        year=year,
        month_name=MESICE[month],
        rate=rate,
        total_hours=total_hours,
        worked_days=worked_days,
        last_day=last_day,
        signature_b64=get_signature_b64(),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"vykaz_{year}_{month:02d}.pdf"
    HTML(string=html_str, base_url=".").write_pdf(str(out_path))
    print(f"PDF vygenerováno: {out_path}")
    return out_path

def prev_month(today: date = None) -> tuple[int, int]:
    today = today or date.today()
    first = date(today.year, today.month, 1) - timedelta(days=1)
    return first.year, first.month

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    args = parser.parse_args()

    if args.year and args.month:
        y, m = args.year, args.month
    else:
        y, m = prev_month()
        print(f"Generuji předchozí měsíc: {MESICE[m]} {y}")

    generate(y, m)
