
const form = document.getElementById("builderForm");
const raceSel = document.getElementById("race");
const bgSel = document.getElementById("background");

function populate() {
  Object.keys(APP_DATA.races).forEach(name => raceSel.add(new Option(name, name)));
  Object.keys(APP_DATA.backgrounds).forEach(name => bgSel.add(new Option(name, name)));
  raceSel.value = "Human";
  bgSel.value = "Custom Background";
}

function sign(n){ return n >= 0 ? `+${n}` : `${n}`; }

function currentData() {
  const fd = new FormData(form);
  const obj = {};
  for (const [k,v] of fd.entries()) obj[k] = v;
  return obj;
}

async function recalc() {
  const res = await fetch("/api/calc", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(currentData())
  });
  const d = await res.json();

  ["str","per","end","cha","int","agi","luk"].forEach(k => {
    document.getElementById(k).value = d[k];
    document.getElementById("val_"+k).textContent = d[k];
    document.getElementById("mod_"+k).textContent = "MOD " + sign(d.mods[k]);
  });

  const pb = document.getElementById("pointBuy");
  pb.textContent = `POINT BUY STATUS // Remaining: ${d.point_remaining}`;
  pb.className = "points" + (d.point_remaining < 0 ? " warn" : "");

  ["hp","sp","ap","healing_rate","carry_load","passive_perception","ac","dt","rad_resistance"].forEach(k => {
    document.getElementById(k).textContent = d[k];
  });

  document.getElementById("caps").value = d.caps;
  document.getElementById("armor").value = d.armor || "";
  document.getElementById("weapon").value = d.weapon || "";
  document.getElementById("equipment").textContent = d.equipment;
  document.getElementById("notes").textContent =
    `Race // ${d.race_note}\n\nBackground trait // ${d.background_trait || "None"}\n\nLuck skill bonus // ${sign(d.luck_skill_bonus)} to all skills.\n\nBackground bonus mapping // This builder follows the fillable sheet skill list. Where the book uses Speech or Breach, it maps them to Persuasion and Lockpick so the bonuses still land on the sheet.`;

  if (!document.getElementById("traits").value && d.background_trait) {
    document.getElementById("traits").value = d.background_trait;
  }

  const skillsEl = document.getElementById("skills");
  skillsEl.innerHTML = "";
  SKILL_ORDER.forEach(name => {
    const row = document.createElement("div");
    row.className = "skill";
    row.innerHTML = `<span>${name}</span><span class="val">${sign(d.skills[name])}</span>`;
    skillsEl.appendChild(row);
  });
}

function changeStat(key, delta) {
  const input = document.getElementById(key);
  let value = parseInt(input.value || "5", 10) + delta;
  const race = raceSel.value;
  const minimum = (race === "Super Mutant" && key === "str") ? 5 : 1; // server adds +1 after; user-facing pre-racial min 5
  value = Math.max(minimum, Math.min(10, value));

  if (delta > 0) {
    const temp = currentData();
    temp[key] = value;
    let spent = 0;
    ["str","per","end","cha","int","agi","luk"].forEach(s => {
      const n = parseInt((s === key ? value : temp[s]) || "5", 10);
      spent += (n - 5);
    });
    if (spent > 3) return;
  }
  input.value = value;
  recalc();
}

function resetBuild() {
  ["name","job","personality","ideal","bond","flaw","traits"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("level").value = 1;
  raceSel.value = "Human";
  bgSel.value = "Custom Background";
  ["str","per","end","cha","int","agi","luk"].forEach(k => document.getElementById(k).value = 5);
  recalc();
}

populate();
recalc();
["race","background","level","name","job","personality","ideal","bond","flaw","traits"].forEach(id => {
  document.getElementById(id).addEventListener("input", recalc);
  document.getElementById(id).addEventListener("change", recalc);
});
