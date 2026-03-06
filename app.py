
from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
from pathlib import Path
import json, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import landscape, letter
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)
DATA = json.loads(Path(__file__).with_name("data.json").read_text(encoding="utf-8"))
TEMPLATE_PDF = Path(__file__).with_name("template_sheet.pdf")

SKILL_DEFS = [
    ("Guns", ("agi",)),
    ("Energy Weapons", ("per","agi")),
    ("Explosives", ("per",)),
    ("Melee Weapons", ("str",)),
    ("Unarmed", ("str","agi")),
    ("Medicine", ("per","int")),
    ("Lockpick", ("per",)),
    ("Crafting", ("int",)),
    ("Science", ("int",)),
    ("Sneak", ("agi",)),
    ("Survival", ("int","end")),
    ("Barter", ("cha",)),
    ("Persuasion", ("cha",)),
    ("Deception", ("cha",)),
    ("Intimidation", ("cha","str")),
]

DEFAULTS = {
    "name": "", "race": "Human", "background": "Custom Background", "level": 1, "job": "", "caps": 850,
    "personality": "", "ideal": "", "bond": "", "flaw": "", "traits": "",
    "str": 5, "per": 5, "end": 5, "cha": 5, "int": 5, "agi": 5, "luk": 5
}

def to_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def mod(score):
    return score - 5

def luck_bonus(luk):
    m = mod(luk)
    return -1 if m < 0 else m // 2

def get_equipment(background, race):
    bg = DATA["backgrounds"][background]
    if "equipment" in bg:
        return bg["equipment"]
    return bg["equipmentByRace"].get(race, "")

def guess_armor_weapon(equipment):
    lower = equipment.lower()
    armor_terms = ["vault suit","cloth armor","leather armor","metal armor","multilayered armor"]
    weapon_terms = ["laser rifle","laser pistol","10mm pistol","9mm pistol","pipe pistol","pipe revolver",
                    "trail carbine","single shotgun","combat knife","knife","switchblade","sharpened pole",
                    "lead pipe","pitchfork","shiv","crowbar","wrench","police baton","bolt-action pipe pistol","syringer"]
    armor = next((a.title() for a in armor_terms if a in lower), "")
    weapon = next((w.title() for w in weapon_terms if w in lower), "")
    return armor, weapon

def normalize(form):
    d = DEFAULTS.copy()
    for k in d:
        if k in form:
            d[k] = form.get(k)
    for k in ["level","caps","str","per","end","cha","int","agi","luk"]:
        d[k] = to_int(d[k], DEFAULTS[k])
    return d

def calculate(d):
    d = normalize(d)
    race = d["race"]
    bg_name = d["background"]
    bg = DATA["backgrounds"][bg_name]
    if race == "Super Mutant":
        d["str"] = max(6, min(10, d["str"] + 1))
    for k in ["str","per","end","cha","int","agi","luk"]:
        d[k] = max(1, min(10, d[k]))

    remaining = 3 - sum(d[k] - 5 for k in ["str","per","end","cha","int","agi","luk"])
    lb = luck_bonus(d["luk"])
    skills = {}
    for name, attrs in SKILL_DEFS:
        base = max(mod(d[a]) for a in attrs)
        bonus = 2 if name in bg["skillBonuses"] else 0
        skills[name] = base + bonus + lb

    d["point_remaining"] = remaining
    d["mods"] = {k: mod(d[k]) for k in ["str","per","end","cha","int","agi","luk"]}
    d["hp"] = 10 + d["mods"]["end"]
    d["sp"] = 10 + d["mods"]["agi"]
    d["ap"] = 10 + d["mods"]["agi"]
    d["healing_rate"] = (d["level"] + d["end"]) // 2
    d["carry_load"] = d["str"] * 10 + (40 if race == "Super Mutant" else 0)
    d["passive_perception"] = 12 + d["mods"]["per"]
    d["ac"] = 10
    d["dt"] = 0
    d["rad_resistance"] = "Immune" if race != "Human" else f"DC {12 - d['mods']['end']}"
    d["skills"] = skills
    d["equipment"] = get_equipment(bg_name, race)
    d["armor"], d["weapon"] = guess_armor_weapon(d["equipment"])
    d["caps"] = bg.get("startingCaps", 50)
    if d["traits"] == "" and bg.get("trait"):
        d["traits"] = bg["trait"]
    d["race_note"] = DATA["races"][race]["notes"]
    d["background_trait"] = bg.get("trait", "")
    return d

@app.route("/")
def index():
    result = calculate(DEFAULTS)
    return render_template("index.html", data=DATA, defaults=DEFAULTS, result=result)

@app.post("/api/calc")
def api_calc():
    return jsonify(calculate(request.json or {}))

def overlay_text(c, x, y, txt, size=10, align="left"):
    if txt is None or txt == "":
        return
    c.setFont("Helvetica", size)
    if align == "center":
        c.drawCentredString(x, y, str(txt))
    elif align == "right":
        c.drawRightString(x, y, str(txt))
    else:
        c.drawString(x, y, str(txt))

def multiline(c, x, y, text, width_chars=38, line_h=10, size=8):
    if not text:
        return
    c.setFont("Helvetica", size)
    for line in textwrap.wrap(str(text), width=width_chars):
        c.drawString(x, y, line)
        y -= line_h

@app.post("/download-sheet.pdf")
def download_sheet():
    result = calculate(request.form)
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=landscape(letter))
    c.setFillColor(black)

    # Top identity
    overlay_text(c, 108, 545, result["name"], 10)
    overlay_text(c, 260, 545, result["race"], 9)
    overlay_text(c, 430, 545, result["background"], 9)
    overlay_text(c, 708, 545, result["level"], 10, "center")

    multiline(c, 30, 485, result["traits"], 44, 10, 8)
    overlay_text(c, 260, 485, result["job"], 9)
    overlay_text(c, 428, 485, result["personality"], 8)
    overlay_text(c, 260, 444, result["ideal"], 8)
    overlay_text(c, 260, 404, result["bond"], 8)
    overlay_text(c, 260, 364, result["flaw"], 8)

    # SPECIAL
    special_x = [64, 118, 171, 225, 279, 333, 386]
    keys = ["str","per","end","cha","int","agi","luk"]
    for x,k in zip(special_x, keys):
        overlay_text(c, x, 302, result[k], 10, "center")

    # Skills
    skill_positions = {
      "Guns": (455, 301), "Energy Weapons": (455, 278), "Explosives": (455, 255),
      "Melee Weapons": (455, 232), "Unarmed": (455, 209), "Medicine": (455, 186),
      "Lockpick": (455, 163), "Crafting": (455, 140), "Science": (455, 117),
      "Sneak": (455, 94), "Survival": (455, 71), "Barter": (651, 301),
      "Persuasion": (651, 278), "Deception": (651, 255), "Intimidation": (651, 232)
    }
    for k,(x,y) in skill_positions.items():
        overlay_text(c, x, y, f"{result['skills'][k]:+d}", 9, "center")

    # Derived / lower center
    overlay_text(c, 455, 170, result["hp"], 10, "center")
    overlay_text(c, 519, 170, result["sp"], 10, "center")
    overlay_text(c, 585, 170, result["ac"], 10, "center")
    overlay_text(c, 650, 170, result["dt"], 10, "center")
    overlay_text(c, 715, 170, result["passive_perception"], 10, "center")
    overlay_text(c, 520, 132, result["healing_rate"], 10, "center")
    overlay_text(c, 715, 132, result["ap"], 10, "center")
    overlay_text(c, 585, 95, result["caps"], 10, "center")
    overlay_text(c, 454, 95, result["armor"], 8)
    overlay_text(c, 518, 95, result["rad_resistance"], 8)
    overlay_text(c, 715, 38, result["carry_load"], 10, "center")

    # Equipment / notes / weapon line
    multiline(c, 30, 62, result["equipment"], 66, 9, 7)
    overlay_text(c, 427, 38, result["weapon"], 8)
    multiline(c, 510, 58, f"Race: {result['race_note']}\nTrait: {result['background_trait']}", 32, 9, 7)

    c.save()
    packet.seek(0)

    # merge with template
    tpl = PdfReader(str(TEMPLATE_PDF))
    overlay = PdfReader(packet)
    writer = PdfWriter()
    page = tpl.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    filename = (result["name"].strip() or "fallout-character").replace(" ", "_").lower() + "_sheet.pdf"
    return send_file(out, as_attachment=True, download_name=filename, mimetype="application/pdf")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
