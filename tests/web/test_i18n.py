"""Umschalten Deutsch → Englisch → Deutsch auf Guides, Layouts und Setups."""

from __future__ import annotations

import pytest
from conftest import collect_errors, set_language, wait_for_auth

PAGES = ["guides.html", "layouts.html", "setups.html"]

# Wörter und Zeichen, die im englischen Text nicht vorkommen sollten.
GERMAN = (
    r"[äöüÄÖÜß]|\b(und|der|die|das|den|dem|mit|für|nicht|ist|eine?|dein|deine|du|oder|auf|zu"
    r"|von|bei|wie|noch|auch|kein|keine|sind|wird|werden|hier|jetzt|schon|nur|sich|dich|dir)\b"
)

# Eigennamen, die absichtlich Deutsch bleiben (Beispiel-Streamer aus js/setups-data.js).
PROPER_NAMES = {"KonsolenKönigin"}

# Layout-Baukasten: Die Platzhalter dieser Felder zeigen absichtlich den Standardtext
# in der „Sprache der Szenen“ (#lang), nicht in der Sprache der Website.
SCENE_LANGUAGE_FIELDS = ["#start", "#pause", "#end"]

# Sichtbarer Text, Optionen von Auswahllisten und die Attribute, die i18n.js übersetzt.
SNAPSHOT_JS = """
([attributes, skip]) => {
  const main = document.querySelector("main");
  const texts = [];
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (["SCRIPT", "STYLE"].includes(node.parentElement.tagName)) continue;
    if (node.nodeValue.trim()) texts.push(node.nodeValue);
  }
  for (const el of main.querySelectorAll("*")) {
    if (skip.some((selector) => el.matches(selector))) continue;
    for (const name of attributes) {
      const value = el.getAttribute(name);
      if (value) texts.push(`@${name}=${value}`);
    }
  }
  return texts;
}
"""
TRANSLATED_ATTRIBUTES = ["placeholder", "aria-label"]


def open_german(context, base_url, path):
    set_language(context, "de")
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/{path}", wait_until="load")
    wait_for_auth(page)
    page.wait_for_timeout(300)
    assert page.evaluate("SGE_I18N.getLanguage()") == "de"
    return page, errors


def switch(page, language):
    page.select_option("[data-sge-language] >> nth=0", language)
    page.wait_for_function("lang => document.documentElement.lang === lang", arg=language)
    page.wait_for_timeout(300)  # Neu-Rendern nach sge:language und MutationObserver


def german_leftovers(page, attributes):
    texts = page.evaluate(SNAPSHOT_JS, [attributes, SCENE_LANGUAGE_FIELDS])
    return page.evaluate(
        """([texts, pattern, names]) => {
          const re = new RegExp(pattern, "i");
          return texts.filter((t) => {
            const value = t.trim().replace(/^@[a-z-]+=/, "");
            return !names.includes(value) && re.test(value);
          });
        }""",
        [texts, GERMAN, sorted(PROPER_NAMES)],
    )


@pytest.mark.parametrize("path", PAGES)
def test_english_has_no_german_leftovers(context, base_url, path):
    page, errors = open_german(context, base_url, path)
    switch(page, "en")
    assert german_leftovers(page, TRANSLATED_ATTRIBUTES) == []
    assert errors == []


@pytest.mark.parametrize("path", PAGES)
def test_switching_back_restores_exact_german_text(context, base_url, path):
    page, errors = open_german(context, base_url, path)
    german = page.evaluate(SNAPSHOT_JS, [TRANSLATED_ATTRIBUTES, SCENE_LANGUAGE_FIELDS])
    switch(page, "en")
    english = page.evaluate(SNAPSHOT_JS, [TRANSLATED_ATTRIBUTES, SCENE_LANGUAGE_FIELDS])
    assert english != german, "Umschalten auf Englisch hat nichts geändert"
    switch(page, "de")
    assert page.evaluate(SNAPSHOT_JS, [TRANSLATED_ATTRIBUTES, SCENE_LANGUAGE_FIELDS]) == german
    assert errors == []


def test_layouts_title_attribute_is_translated(context, base_url):
    page, _ = open_german(context, base_url, "layouts.html")
    assert page.get_attribute("#preview", "title") == "Vorschau der Szene"
    switch(page, "en")
    assert german_leftovers(page, ["title"]) == []
    assert page.get_attribute("#preview", "title") == "Scene preview"
    switch(page, "de")
    assert page.get_attribute("#preview", "title") == "Vorschau der Szene"
