// Erste Quests auf der Startseite: Nur wer eine Quest selbst abhakt, bekommt XP.
// Nichts wird beim Scrollen oder automatisch abgehakt (Fallstrick: dekorative
// Fortschrittsanzeigen nie automatisch füllen).
// Der Stand liegt im localStorage ("sge-quests"). Ist der Speicher gesperrt
// (privates Fenster, Datenschutz-Einstellungen), gilt er nur bis zum Neuladen.
// Animationen (Level-Sprung) macht js/motion.js über das Ereignis "sge:quests".
(() => {
  "use strict";
  const KEY = "sge-quests";
  const MAX_LEVEL_XP = 1100;
  const items = [...document.querySelectorAll(".quests li[data-quest]")];
  if (!items.length) return;
  const xpEl = document.querySelector("[data-xp]");
  const lvlEl = document.querySelector("[data-level]");
  const bar = document.querySelector(".xp-bar span");
  const reset = document.querySelector("[data-quest-reset]");
  const ids = items.map((li) => li.dataset.quest);
  const xpOf = (li) => parseInt(li.querySelector(".xp").textContent.replace(/\D/g, ""), 10) || 0;

  let memory = []; // Rückfall, wenn localStorage nicht geht
  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw === null) return memory;
      const list = JSON.parse(raw);
      return Array.isArray(list) ? list.filter((id) => ids.includes(id)) : [];
    } catch {
      return memory;
    }
  }
  function save(list) {
    memory = list;
    try {
      if (list.length) localStorage.setItem(KEY, JSON.stringify(list));
      else localStorage.removeItem(KEY);
    } catch {
      /* Kein Speicher: Stand bleibt nur im Arbeitsspeicher */
    }
  }

  let done = new Set(load());
  let level = 1;

  function render() {
    let xp = 0;
    items.forEach((li) => {
      const on = done.has(li.dataset.quest);
      li.classList.toggle("is-done", on);
      li.querySelector(".quest-check").setAttribute("aria-checked", on ? "true" : "false");
      if (on) xp += xpOf(li);
    });
    const previous = level;
    level = done.size === items.length ? 2 : 1;
    if (xpEl) xpEl.textContent = String(xp);
    if (lvlEl) lvlEl.textContent = String(level);
    if (bar) bar.style.setProperty("--xp", String(Math.min(1, xp / MAX_LEVEL_XP)));
    if (reset) reset.hidden = done.size === 0;
    document.dispatchEvent(new CustomEvent("sge:quests", {
      detail: { xp, level, done: [...done], levelChanged: level !== previous },
    }));
  }

  function toggle(li) {
    const id = li.dataset.quest;
    if (done.has(id)) done.delete(id);
    else done.add(id);
    save(ids.filter((q) => done.has(q)));
    render();
  }

  items.forEach((li) => {
    // <button role="checkbox">: Klick, Leertaste und Enter funktionieren von selbst.
    li.querySelector(".quest-check").addEventListener("click", () => toggle(li));
  });
  if (reset) {
    reset.addEventListener("click", () => {
      done = new Set();
      save([]);
      render();
      items[0].querySelector(".quest-check").focus();
    });
  }
  render();
  window.SGE_QUESTS = { get done() { return [...done]; } }; // für Tests
})();
