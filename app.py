"""
Flask webový editor výkazů práce.
Spuštění: python3 app.py
"""
import json
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file, abort
from generate_pdf import generate
import pickup_data

app = Flask(__name__)

DATA_DIR = Path("data")

MESICE = [
    "Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
    "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec",
]

def load_data(year: int) -> dict:
    p = DATA_DIR / f"{year}.json"
    if not p.exists():
        abort(404, f"Data pro rok {year} nenalezena.")
    return json.loads(p.read_text())

def save_data(year: int, data: dict):
    p = DATA_DIR / f"{year}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ── HTML editor ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("editor.html", mesice=MESICE)

# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/data/<int:year>")
def api_get(year):
    return jsonify(load_data(year))

@app.post("/api/data/<int:year>")
def api_save(year):
    data = request.get_json(force=True)
    save_data(year, data)
    return jsonify({"status": "ok"})

@app.post("/api/generate/<int:year>/<int:month>")
def api_generate(year, month):
    try:
        out = generate(year, month)
        return jsonify({"status": "ok", "file": str(out)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.get("/api/pdf/<int:year>/<int:month>")
def api_pdf(year, month):
    path = Path(f"output/vykaz_{year}_{month:02d}.pdf")
    if not path.exists():
        abort(404, "PDF ještě nebylo vygenerováno.")
    return send_file(path, mimetype="application/pdf",
                     download_name=path.name, as_attachment=False)

# ── Pickup Report (Parkhotel TYCHO) ──────────────────────────────────────────

@app.route("/pickup")
def pickup_index():
    return render_template("pickup.html", mesice=pickup_data.MESICE)

@app.get("/api/pickup/<int:year>")
def api_pickup_get(year):
    return jsonify(pickup_data.load_year(year))

@app.post("/api/pickup/<int:year>")
def api_pickup_save(year):
    data = request.get_json(force=True)
    pickup_data.save_year(year, data)
    return jsonify({"status": "ok"})

@app.get("/api/pickup/<int:year>/export")
def api_pickup_export(year):
    data = pickup_data.load_year(year)
    out = Path("output") / f"pickup_report_{year}.xlsx"
    pickup_data.export_xlsx(year, data, out)
    return send_file(out, as_attachment=True, download_name=out.name)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
