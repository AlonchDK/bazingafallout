from flask import Flask, render_template, request, send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, green
import textwrap

app = Flask(__name__)

RACES = ["Human", "Ghoul", "Gen-2 Synth", "Robot", "Super Mutant"]
BACKGROUNDS = [
    "Custom Background", "Doctor", "Guard", "Mechanic", "Mercenary",
    "Scientist", "Soldier", "Trader", "Vault Dweller", "Wastelander"
]

BACKGROUND_SKILLS = {
    "Custom Background": [],
    "Doctor": ["Breach", "Medicine", "Science"],
    "Guard": ["Guns", "Speech", "Melee Weapons"],
    "Mechanic": ["Crafting", "Guns", "Science"],
    "Mercenary": ["Guns", "Melee Weapons", "Survival"],
    "Scientist": ["Energy Weapons", "Breach", "Science"],
    "Soldier": ["Explosives", "Guns", "Medicine"],
    "Trader": ["Barter", "Speech", "Intimidation"],
    "Vault Dweller": ["Medicine", "Speech", "Science"],
    "Wastelander": ["Guns", "Survival", "Unarmed"],
}

BACKGROUND_TRAITS = {
    "Doctor": "Do No Harm",
    "Guard": "Vigilant Watch",
    "Mechanic": "Proper Maintenance",
    "Mercenary": "Sweeten the Deal",
    "Scientist": "Field Research",
    "Soldier": "Efficient Combatant",
    "Trader": "Bargaining Chip",
    "Vault Dweller": "Talented",
    "Wastelander": "Adventurer's Instinct",
}

EQUIPMENT = {
    ("Doctor", "Human"): ("Cloth Armor", "Syringer", "Cloth armor, knife (4 decay), syringer, first aid kit, 2 diluted stimpaks, Rad-X, diluted RadAway, healing powder, sleeping bag, tent, 2 purified water, 50 caps."),
    ("Doctor", "Ghoul"): ("Cloth Armor", "Syringer", "Cloth armor, knife (4 decay), syringer, first aid kit, 2 diluted stimpaks, Rad-X, diluted RadAway, healing powder, sleeping bag, tent, 2 purified water, 50 caps."),
    ("Doctor", "Super Mutant"): ("Cloth Armor", "Syringer", "Cloth armor, knife (4 decay), syringer, first aid kit, 2 diluted stimpaks, Rad-X, diluted RadAway, healing powder, sleeping bag, tent, 2 purified water, 50 caps."),
    ("Doctor", "Gen-2 Synth"): ("Cloth Armor", "Syringer", "Cloth armor, knife (4 decay), syringer, first aid kit, 2 RobCo Quick Fix-it 1.0, 2 RobCo Quick Fix-it 2.0, Rad-X, diluted RadAway, 2 healing powder, 50 caps."),
    ("Doctor", "Robot"): ("Cloth Armor", "Syringer", "Cloth armor, knife (4 decay), syringer, first aid kit, 2 RobCo Quick Fix-it 1.0, 2 RobCo Quick Fix-it 2.0, Rad-X, diluted RadAway, 2 healing powder, 50 caps."),
    ("Guard", "Human"): ("Metal Armor", "9mm Pistol", "Metal armor (1 decay), police baton (2 decay), 9mm pistol, ammo, backpack, binoculars, food, water, diluted stimpak, 50 caps."),
    ("Guard", "Ghoul"): ("Metal Armor", "9mm Pistol", "Metal armor (1 decay), police baton (2 decay), 9mm pistol, ammo, backpack, binoculars, food, water, diluted stimpak, 50 caps."),
    ("Guard", "Super Mutant"): ("Metal Armor", "9mm Pistol", "Metal armor (1 decay), police baton (2 decay), 9mm pistol, ammo, backpack, binoculars, food, water, diluted stimpak, 50 caps."),
    ("Guard", "Gen-2 Synth"): ("Metal Armor", "9mm Pistol", "Metal armor (1 decay), police baton (2 decay), 9mm pistol, ammo, backpack, binoculars, 2 RobCo Quick Fix-it, cache clearer, 50 caps."),
    ("Guard", "Robot"): ("Metal Armor", "9mm Pistol", "Metal armor (1 decay), police baton (2 decay), 9mm pistol, ammo, backpack, binoculars, 2 RobCo Quick Fix-it, cache clearer, 50 caps."),
    ("Mechanic", "Human"): ("Cloth Armor", "Pipe Revolver", "Cloth armor, wrench, pipe revolver, .44 bullets, backpack, bandolier, canteen, rope, weapon repair kit, 50 caps."),
    ("Mechanic", "Ghoul"): ("Cloth Armor", "Pipe Revolver", "Cloth armor, wrench, pipe revolver, .44 bullets, backpack, bandolier, canteen, rope, weapon repair kit, 50 caps."),
    ("Mechanic", "Super Mutant"): ("Cloth Armor", "Pipe Revolver", "Cloth armor, wrench, pipe revolver, .44 bullets, backpack, bandolier, canteen, rope, weapon repair kit, 50 caps."),
    ("Mechanic", "Gen-2 Synth"): ("Cloth Armor", "Pipe Revolver", "Cloth armor, wrench, pipe revolver, .44 bullets, backpack, bandolier, rope, RobCo Quick Fix-it, 2 weapon repair kits, 50 caps."),
    ("Mechanic", "Robot"): ("Cloth Armor", "Pipe Revolver", "Cloth armor, wrench, pipe revolver, .44 bullets, backpack, bandolier, rope, RobCo Quick Fix-it, 2 weapon repair kits, 50 caps."),
    ("Mercenary", "Human"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Mercenary", "Ghoul"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Mercenary", "Super Mutant"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Mercenary", "Gen-2 Synth"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, RobCo Quick Fix-it 1.0 and 2.0, 50 caps."),
    ("Mercenary", "Robot"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, RobCo Quick Fix-it 1.0 and 2.0, 50 caps."),
    ("Scientist", "Human"): ("Cloth Armor", "Laser Pistol", "Cloth armor, laser pistol, 2 energy cells, backpack, sleeping bag, tent, cram, purified water, diluted RadAway, Rad-X, stimpak, 50 caps."),
    ("Scientist", "Ghoul"): ("Cloth Armor", "Laser Pistol", "Cloth armor, laser pistol, 2 energy cells, backpack, sleeping bag, tent, cram, purified water, diluted RadAway, Rad-X, stimpak, 50 caps."),
    ("Scientist", "Super Mutant"): ("Cloth Armor", "Laser Pistol", "Cloth armor, laser pistol, 2 energy cells, backpack, sleeping bag, tent, cram, purified water, diluted RadAway, Rad-X, stimpak, 50 caps."),
    ("Scientist", "Gen-2 Synth"): ("Cloth Armor", "Laser Pistol", "Cloth armor, laser pistol, 2 energy cells, backpack, 2 RobCo Quick Fix-it 2.0, Programmer's Digest, data scrubber, 50 caps."),
    ("Scientist", "Robot"): ("Cloth Armor", "Laser Pistol", "Cloth armor, laser pistol, 2 energy cells, backpack, 2 RobCo Quick Fix-it 2.0, Programmer's Digest, data scrubber, 50 caps."),
    ("Soldier", "Human"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Soldier", "Ghoul"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Soldier", "Super Mutant"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, cram, sleeping bag, tent, diluted stimpak, purified water, 50 caps."),
    ("Soldier", "Gen-2 Synth"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, RobCo Quick Fix-it 1.0 and 2.0, 50 caps."),
    ("Soldier", "Robot"): ("Leather Armor", "Trail Carbine", "Leather armor, combat knife (2 decay), trail carbine (2 decay), .44 bullets, backpack, RobCo Quick Fix-it 1.0 and 2.0, 50 caps."),
    ("Trader", "Human"): ("Cloth Armor", "Pipe Pistol", "Cloth armor, shiv, pipe pistol (2 decay), 9mm bullets, backpack, food, dirty water, purified water, lockpicks, sleeping bag, tent, whiskey, fixer, jet, psycho, coffee, 50 caps."),
    ("Trader", "Ghoul"): ("Cloth Armor", "Pipe Pistol", "Cloth armor, shiv, pipe pistol (2 decay), 9mm bullets, backpack, food, dirty water, purified water, lockpicks, sleeping bag, tent, whiskey, fixer, jet, psycho, coffee, 50 caps."),
    ("Trader", "Super Mutant"): ("Cloth Armor", "Pipe Pistol", "Cloth armor, shiv, pipe pistol (2 decay), 9mm bullets, backpack, food, dirty water, purified water, lockpicks, sleeping bag, tent, whiskey, fixer, jet, psycho, coffee, 50 caps."),
    ("Trader", "Gen-2 Synth"): ("Cloth Armor", "Pipe Pistol", "Cloth armor, shiv, pipe pistol (2 decay), 9mm bullets, backpack, lockpicks, RobCo Quick Fix-it, overclock hardware, cache clearer, AI upload, flashlight, energy cell, skill magazine, 50 caps."),
    ("Trader", "Robot"): ("Cloth Armor", "Pipe Pistol", "Cloth armor, shiv, pipe pistol (2 decay), 9mm bullets, backpack, lockpicks, RobCo Quick Fix-it, overclock hardware, cache clearer, AI upload, flashlight, energy cell, skill magazine, 50 caps."),
    ("Vault Dweller", "Human"): ("Vault Suit", "10mm Pistol", "Vault suit, 10mm pistol, 10mm ammo, backpack, sleeping bag, tent, canteen, weapon repair kit, Pip-Boy, packaged food, coffee, purified water, stimpak."),
    ("Vault Dweller", "Ghoul"): ("Vault Suit", "10mm Pistol", "Vault suit, 10mm pistol, 10mm ammo, backpack, sleeping bag, tent, canteen, weapon repair kit, Pip-Boy, packaged food, coffee, purified water, stimpak."),
    ("Vault Dweller", "Super Mutant"): ("Vault Suit", "10mm Pistol", "Vault suit, 10mm pistol, 10mm ammo, backpack, sleeping bag, tent, canteen, weapon repair kit, Pip-Boy, packaged food, coffee, purified water, stimpak."),
    ("Vault Dweller", "Gen-2 Synth"): ("Vault Suit", "Laser Pistol", "Vault suit, laser pistol, 2 energy cells, backpack, Pip-Boy, 2 RobCo Quick Fix-it 2.0, Programmer's Digest, data scrubber, 50 caps."),
    ("Vault Dweller", "Robot"): ("Vault Suit", "Laser Pistol", "Vault suit, laser pistol, 2 energy cells, backpack, Pip-Boy, 2 RobCo Quick Fix-it 2.0, Programmer's Digest, data scrubber, 50 caps."),
    ("Wastelander", "Human"): ("Leather Armor", "10mm Pistol", "Leather armor, sharpened pole, 10mm pistol, ammo, backpack, sleeping bag, tent, mutfruit, apples, vegetable soup, purified water, healing powder, 50 caps."),
    ("Wastelander", "Ghoul"): ("Leather Armor", "10mm Pistol", "Leather armor, sharpened pole, 10mm pistol, ammo, backpack, sleeping bag, tent, mutfruit, apples, vegetable soup, dirty water, nuka-cola, diluted stimpak, 50 caps."),
    ("Wastelander", "Super Mutant"): ("Leather Armor", "10mm Pistol", "Leather armor, sharpened pole, 10mm pistol, ammo, backpack, sleeping bag, tent, mutfruit, apples, vegetable soup, dirty water, nuka-cola, diluted stimpak, 50 caps."),
    ("Wastelander", "Gen-2 Synth"): ("Leather Armor", "10mm Pistol", "Leather armor, sharpened pole, 10mm pistol, ammo, backpack, bandolier, binoculars, grappling hook, rope, RobCo Quick Fix-it, 50 caps."),
    ("Wastelander", "Robot"): ("Leather Armor", "10mm Pistol", "Leather armor, sharpened pole, 10mm pistol, ammo, backpack, bandolier, binoculars, grappling hook, rope, RobCo Quick Fix-it, 50 caps."),
}

def mod(score):
    return score - 5

def luck_bonus(luk):
    m = mod(luk)
    return -1 if m < 0 else m // 2

def get_equipment(background, race):
    if background == "Custom Background":
        return ("Custom", "Custom", "Choose any background equipment or take 850 caps.")
    return EQUIPMENT.get((background, race), ("See package", "See package", "Equipment package not yet filled for this combination."))

def calculate(data):
    race = data["race"]
    background = data["background"]
    strength = int(data["str"])
    if race == "Super Mutant":
        strength = max(6, min(10, strength))
    per = int(data["per"]); end = int(data["end"]); cha = int(data["cha"])
    intel = int(data["int"]); agi = int(data["agi"]); luk = int(data["luk"]); level = int(data["level"])
    lb = luck_bonus(luk)

    def skill(base, name):
        return base + lb + (2 if name in BACKGROUND_SKILLS.get(background, []) else 0)

    skills = {
        "Barter": skill(mod(cha), "Barter"),
        "Breach": skill(max(mod(per), mod(intel)), "Breach"),
        "Crafting": skill(mod(intel), "Crafting"),
        "Energy Weapons": skill(mod(per), "Energy Weapons"),
        "Explosives": skill(mod(per), "Explosives"),
        "Guns": skill(mod(agi), "Guns"),
        "Intimidation": skill(max(mod(strength), mod(cha)), "Intimidation"),
        "Medicine": skill(max(mod(per), mod(intel)), "Medicine"),
        "Melee Weapons": skill(mod(strength), "Melee Weapons"),
        "Science": skill(mod(intel), "Science"),
        "Sneak": skill(mod(agi), "Sneak"),
        "Speech": skill(mod(cha), "Speech"),
        "Survival": skill(mod(end), "Survival"),
        "Unarmed": skill(mod(strength), "Unarmed"),
    }

    armor, weapon, equipment = get_equipment(background, race)
    return {
        **data,
        "str": strength,
        "skills": skills,
        "hp": 10 + mod(end),
        "sp": 10 + mod(agi),
        "ap": min(15, 10 + mod(agi)),
        "healing_rate": (level + end) // 2,
        "carry_load": strength * 10 + (40 if race == "Super Mutant" else 0),
        "passive_sense": 12 + mod(per),
        "ac": 10,
        "dt": 0,
        "rad_dc": str(12 - mod(end)) if race == "Human" else "IMMUNE / N.A.",
        "armor": armor,
        "weapon": weapon,
        "equipment": equipment,
        "trait": BACKGROUND_TRAITS.get(background, ""),
        "race_note": {
            "Human": "Tenacity. Radiation DC applies.",
            "Ghoul": "Immune to radiation damage and radiation levels.",
            "Gen-2 Synth": "Inorganic body. Immune to radiation and poison.",
            "Robot": "Inorganic body. Immune to radiation, poison, and bleeding.",
            "Super Mutant": "Strength floor 6 and carry load +40."
        }.get(race, ""),
        "luck_skill_bonus": lb,
    }

@app.route("/", methods=["GET"])
def index():
    defaults = {"name":"","race":"Human","background":"Custom Background","level":1,"job":"","caps":50,
                "personality":"","ideal":"","bond":"","flaw":"","traits":"",
                "str":5,"per":5,"end":5,"cha":5,"int":5,"agi":5,"luk":5}
    return render_template("index.html", races=RACES, backgrounds=BACKGROUNDS, defaults=defaults, result=None)

@app.route("/build", methods=["POST"])
def build():
    keys = ["name","race","background","level","job","caps","personality","ideal","bond","flaw","traits",
            "str","per","end","cha","int","agi","luk"]
    data = {k: request.form.get(k, "") for k in keys}
    return render_template("index.html", races=RACES, backgrounds=BACKGROUNDS, defaults=data, result=calculate(data))

@app.route("/pdf", methods=["POST"])
def pdf():
    keys = ["name","race","background","level","job","caps","personality","ideal","bond","flaw","traits",
            "str","per","end","cha","int","agi","luk"]
    data = {k: request.form.get(k, "") for k in keys}
    result = calculate(data)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFillColor(black)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(green)
    y = height - 40

    def line(text, size=10, step=15):
        nonlocal y
        c.setFont("Courier-Bold" if size >= 14 else "Courier", size)
        c.drawString(30, y, str(text)[:110])
        y -= step

    line("FALLOUT TTRPG CHARACTER SHEET", 16, 24)
    line(f"Name: {result['name']}    Race: {result['race']}    Level: {result['level']}")
    line(f"Background: {result['background']}    Job: {result['job']}    Caps: {result['caps']}")
    line(f"Traits & Perks: {result['traits'] or result['trait']}")
    y -= 6
    line(f"S {result['str']} ({mod(result['str']):+d})   P {result['per']} ({mod(int(result['per'])):+d})   E {result['end']} ({mod(int(result['end'])):+d})")
    line(f"C {result['cha']} ({mod(int(result['cha'])):+d})   I {result['int']} ({mod(int(result['int'])):+d})   A {result['agi']} ({mod(int(result['agi'])):+d})   L {result['luk']} ({mod(int(result['luk'])):+d})")
    y -= 6
    line(f"HP: {result['hp']}   SP: {result['sp']}   AP: {result['ap']}   Healing Rate: {result['healing_rate']}")
    line(f"Carry Load: {result['carry_load']}   Passive Sense: {result['passive_sense']}   AC: {result['ac']}   DT: {result['dt']}")
    line(f"Radiation DC: {result['rad_dc']}   Armor: {result['armor']}   Weapon: {result['weapon']}")
    y -= 6
    line("SKILLS", 12, 18)
    for k, v in result["skills"].items():
        line(f"{k}: {v:+d}", 10, 14)
    y -= 4
    line("EQUIPMENT", 12, 18)
    for chunk in textwrap.wrap(result["equipment"], 90):
        line(chunk, 10, 14)
    y -= 4
    line("NOTES", 12, 18)
    line(f"Race: {result['race_note']}", 10, 14)
    line(f"Background trait: {result['trait']}", 10, 14)
    line(f"Luck skill bonus: {result['luck_skill_bonus']:+d}", 10, 14)
    line(f"Personality: {result['personality']}", 10, 14)
    line(f"Ideal: {result['ideal']}", 10, 14)
    line(f"Bond: {result['bond']}", 10, 14)
    line(f"Flaw: {result['flaw']}", 10, 14)

    c.showPage()
    c.save()
    buffer.seek(0)
    filename = (result["name"].strip() or "fallout-character").replace(" ", "_").lower() + ".pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
