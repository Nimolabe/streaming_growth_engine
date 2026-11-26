"""Messungen über die Twitch-API (Helix) – nur öffentliche Live-Daten, App-Token genügt.

Pro Kategorie: Alias (z. B. „CS2“ → „Counter-Strike“) → Get Games (exakter Name, Groß-/
Kleinschreibung egal) → sonst Search Categories für Vorschläge →
Get Streams nach Spiel-ID und Sprache, seitenweise (je 100, nach Zuschauern sortiert).
Gespeichert werden ausschließlich Zuschauerzahlen.

Glücksspiel-Kategorien werden nie gemessen (Entscheidung des Nutzers vom 26.11.2026):
``resolve_category`` und ``measure`` lehnen sie mit ``GamblingNotSupported`` ab,
``suggestion_categories`` lässt sie weg.
"""
import time
from collections.abc import Callable
from dataclasses import dataclass

from ..clip_hunter.twitch_api import HelixClient, TwitchApiError
from .aliases import alias_target
from .gambling import GamblingNotSupported, is_gambling, is_gambling_name
from .models import MAX_VIEWERS_PER_SNAPSHOT, CategorySnapshot

PAGE_SIZE = 100
DEFAULT_PAGES = 10
MAX_PAGES = MAX_VIEWERS_PER_SNAPSHOT // PAGE_SIZE


class CategoryNotFound(ValueError):
    """Kategorie unbekannt; die Meldung enthält Vorschläge, falls Twitch welche kennt."""


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    alias: str | None = None  # Eingabe des Nutzers, wenn ein Alias gegriffen hat (z. B. „CS2“)

    @property
    def gambling(self) -> bool:
        return is_gambling(self.id, self.name)


def _clean_name(value: str) -> str:
    name = " ".join(str(value).split())
    if not name or len(name) > 120:
        raise CategoryNotFound("Kategorienamen müssen 1 bis 120 Zeichen lang sein.")
    return name


def resolve_category(client: HelixClient, name: str) -> Category:
    """Findet die Kategorie über Alias oder exakten Namen; sonst mit Vorschlägen abbrechen.

    Glücksspiel wird abgelehnt (``GamblingNotSupported``): schon am Namen bzw. an der Kurzform,
    ohne Anfrage an Twitch, und sonst an der gefundenen Kategorie (ID oder Name).
    """
    name = _clean_name(name)
    if is_gambling_name(name):
        raise GamblingNotSupported(name)
    return _refuse_gambling(_lookup(client, name), name)


def _refuse_gambling(category: Category, typed: str) -> Category:
    if category.gambling:
        raise GamblingNotSupported(typed if typed.casefold() == category.name.casefold()
                                   else f"{typed} → {category.name}")
    return category


def _lookup(client: HelixClient, name: str) -> Category:
    target = alias_target(name)
    if target:
        for item in client.get("games", [("name", target)]).get("data") or []:
            if item.get("id"):
                return Category(id=str(item["id"]), name=str(item.get("name") or target),
                                alias=name)
        # Ziel gibt es nicht (mehr): normal mit dem eingegebenen Namen weitersuchen.
    for item in client.get("games", [("name", name)]).get("data") or []:
        if item.get("id"):
            return Category(id=str(item["id"]), name=str(item.get("name") or name))
    found = client.get("search/categories", [("query", name), ("first", "5")]).get("data") or []
    # Ein eindeutiger Treffer ohne Groß-/Kleinschreibung zählt als gefunden.
    exact = [item for item in found if str(item.get("name", "")).casefold() == name.casefold()]
    if len(exact) == 1 and exact[0].get("id"):
        return Category(id=str(exact[0]["id"]), name=str(exact[0]["name"]))
    ideas = [str(item.get("name")) for item in found if item.get("name")][:5]
    hint = f" Meintest du: {', '.join(ideas)}?" if ideas else ""
    raise CategoryNotFound(f"Kategorie „{name}“ nicht gefunden.{hint}")


def top_categories(client: HelixClient, count: int = 30) -> list[Category]:
    """Die meistgesehenen Kategorien auf Twitch gerade jetzt (weltweit)."""
    count = max(1, min(count, 100))
    data = client.get("games/top", [("first", str(count))]).get("data") or []
    return [Category(id=str(item["id"]), name=str(item.get("name") or item["id"]))
            for item in data if item.get("id")][:count]


@dataclass
class Suggestions:
    categories: list[Category]
    skipped_gambling: int  # nur die Zahl, keine Namen


def suggestion_categories(client: HelixClient, count: int = 30) -> Suggestions:
    """Meistgesehene Kategorien für ``suggest`` – Glücksspiel immer ausgefiltert.

    Ausgefilterte Plätze werden mit den nächsten Kategorien aufgefüllt, damit trotzdem ``count``
    Kategorien gemessen werden. ``skipped_gambling`` zählt die Glücksspiel-Kategorien, die
    sonst unter den ersten ``count`` gewesen wären.
    """
    count = max(1, min(count, 100))
    kept: list[Category] = []
    skipped = 0
    for category in top_categories(client, min(100, count + 20)):
        if len(kept) >= count:
            break
        if category.gambling:
            skipped += 1
        else:
            kept.append(category)
    return Suggestions(kept, skipped)


def measure(client: HelixClient, category: Category, language: str = "de", *,
            max_pages: int = DEFAULT_PAGES, pause: float = 0.1,
            clock: Callable[[], float] | None = None,
            sleep: Callable[[float], None] | None = None) -> CategorySnapshot:
    """Zuschauerzahlen aller Live-Kanäle (bis max_pages × 100) einer Kategorie."""
    if category.gambling:
        raise GamblingNotSupported(category.name)
    if not 1 <= max_pages <= MAX_PAGES:
        raise ValueError(f"max_pages muss zwischen 1 und {MAX_PAGES} liegen.")
    language = language.strip().casefold()
    sleep = sleep or time.sleep
    taken_at = (clock or time.time)()
    params = [("game_id", category.id), ("type", "live"), ("first", str(PAGE_SIZE))]
    if language != "any":
        params.append(("language", language))
    seen: dict[str, int] = {}
    cursor = None
    complete = True
    for page_number in range(max_pages):
        if page_number:
            sleep(pause)
        page = client.get("streams", params + ([("after", cursor)] if cursor else []))
        data = page.get("data") or []
        for item in data:
            key = str(item.get("id") or item.get("user_id") or "")
            try:
                viewers = int(item.get("viewer_count") or 0)
            except (TypeError, ValueError):
                continue
            if key and viewers >= 0:
                # Zwischen zwei Seiten kann ein Kanal verrutschen: nur einmal zählen.
                seen[key] = max(viewers, seen.get(key, 0))
        cursor = (page.get("pagination") or {}).get("cursor")
        if not data or not cursor:
            break
    else:
        complete = False  # Seitenlimit erreicht, es gibt wahrscheinlich noch mehr Kanäle
    return CategorySnapshot(taken_at=taken_at, category_id=category.id, category=category.name,
                            alias=category.alias, language=language, complete=complete,
                            viewers=list(seen.values()))


@dataclass
class MeasureRound:
    snapshots: list[CategorySnapshot]
    errors: list[str]


def measure_many(client: HelixClient, categories: list[Category], language: str, *,
                 max_pages: int = DEFAULT_PAGES, pause: float = 0.1,
                 sleep: Callable[[float], None] | None = None,
                 clock: Callable[[], float] | None = None) -> MeasureRound:
    """Misst mehrere Kategorien; ein Fehler bei einer Kategorie stoppt die anderen nicht.

    Bei einem Anmelde- oder Limit-Fehler wird abgebrochen, weil weitere Anfragen ebenso
    scheitern würden.
    """
    result = MeasureRound([], [])
    sleep = sleep or time.sleep
    for index, category in enumerate(categories):
        if index:
            sleep(pause)
        try:
            result.snapshots.append(measure(client, category, language, max_pages=max_pages,
                                            pause=pause, sleep=sleep, clock=clock))
        except GamblingNotSupported as exc:
            result.errors.append(str(exc))
        except TwitchApiError as exc:
            result.errors.append(f"{category.name}: {exc}")
            text = str(exc)
            if "Anmeldung" in text or "Anfragelimit" in text or "nicht erreichbar" in text:
                break
    return result
