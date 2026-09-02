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
import reklamace_data

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

# ── Reklamace Škoda ──────────────────────────────────────────────────────────

@app.route("/reklamace")
def reklamace_list_page():
    return render_template("reklamace_list.html")

@app.route("/reklamace/<cislo>")
def reklamace_detail_page(cislo):
    if not reklamace_data.get_reklamace(cislo):
        abort(404, f"Reklamace {cislo} nenalezena.")
    return render_template("reklamace_detail.html", cislo=cislo, faze_defs=reklamace_data.FAZE_DEFS)

@app.get("/api/reklamace")
def api_reklamace_list():
    return jsonify(reklamace_data.list_all())

@app.post("/api/reklamace")
def api_reklamace_create():
    body = request.get_json(force=True)
    servisni_partner = (body.get("servisni_partner") or "").strip()
    kontaktni_osoba = (body.get("kontaktni_osoba") or "").strip()
    datum_prijeti = body.get("datum_prijeti") or ""
    if not servisni_partner or not datum_prijeti:
        return jsonify({"status": "error", "message": "Servisní partner a datum přijetí jsou povinné."}), 400
    item = reklamace_data.new_reklamace(servisni_partner, kontaktni_osoba, datum_prijeti)
    return jsonify(item)

@app.get("/api/reklamace/<cislo>")
def api_reklamace_get(cislo):
    item = reklamace_data.get_reklamace(cislo)
    if not item:
        abort(404, f"Reklamace {cislo} nenalezena.")
    return jsonify(item)

@app.post("/api/reklamace/<cislo>")
def api_reklamace_update(cislo):
    body = request.get_json(force=True)
    item = reklamace_data.update_header(cislo, body)
    if not item:
        abort(404, f"Reklamace {cislo} nenalezena.")
    return jsonify(item)

@app.post("/api/reklamace/<cislo>/<faze_key>")
def api_reklamace_faze_update(cislo, faze_key):
    body = request.get_json(force=True)
    item = reklamace_data.update_faze(cislo, faze_key, body)
    if not item:
        abort(404, "Reklamace nebo fáze nenalezena.")
    return jsonify(item)

@app.post("/api/reklamace/<cislo>/<faze_key>/priloha")
def api_reklamace_priloha_upload(cislo, faze_key):
    file_storage = request.files.get("file")
    if not file_storage or not file_storage.filename:
        return jsonify({"status": "error", "message": "Žádný soubor nebyl vybrán."}), 400
    item = reklamace_data.add_priloha(cislo, faze_key, file_storage)
    if not item:
        abort(404, "Reklamace nebo fáze nenalezena.")
    return jsonify(item)

@app.delete("/api/reklamace/<cislo>/<faze_key>/priloha/<filename>")
def api_reklamace_priloha_delete(cislo, faze_key, filename):
    item = reklamace_data.remove_priloha(cislo, faze_key, filename)
    if not item:
        abort(404, "Reklamace nebo fáze nenalezena.")
    return jsonify(item)

@app.get("/api/reklamace/<cislo>/<faze_key>/priloha/<filename>")
def api_reklamace_priloha_download(cislo, faze_key, filename):
    path = reklamace_data.priloha_path(cislo, faze_key, filename)
    if not path.exists():
        abort(404, "Příloha nenalezena.")
    return send_file(path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
