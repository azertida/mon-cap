#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_abris.py — Mon cap
Récolte les abris candidats d'une commune depuis OpenStreetMap (via Overpass)
et produit un fichier statique `abris.json` que la PWA met en cache.

Pensé pour le pattern Radar (GitHub Pages + Actions) :
  - aucune clé d'API
  - aucune dépendance externe (bibliothèque standard uniquement)
  - horodatage inclus (le « à jour à … » de l'app)

Usage :
    python build_abris.py            # lit abris.overpassql, écrit abris.json
    python build_abris.py --pretty   # JSON indenté (lecture humaine)

Données © les contributeurs d'OpenStreetMap, sous licence ODbL.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# --- Réglages ---------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY_FILE = Path(__file__).with_name("abris.overpassql")
OUTPUT_FILE = Path(__file__).with_name("abris.json")
AREA_LABEL = "Woluwe-Saint-Lambert"
USER_AGENT = "MonCap/0.1 (abris; contact: ana@connectes.be)"

# Catégories qu'on garde, avec leur étiquette française et un éventuel drapeau.
# dynamic_offhours = True : hors des horaires réguliers, renvoyer vers la
# source vivante (ex. pharmacie de garde) plutôt que d'affirmer « ouvert ».
CATEGORIES = {
    "amenity=pharmacy":          {"key": "pharmacy",         "label": "Pharmacie",            "dynamic_offhours": True},
    "amenity=library":           {"key": "library",          "label": "Bibliothèque",         "dynamic_offhours": False},
    "amenity=townhall":          {"key": "townhall",         "label": "Bâtiment communal",    "dynamic_offhours": False},
    "amenity=community_centre":  {"key": "community_centre", "label": "Centre communautaire", "dynamic_offhours": False},
    "shop=mall":                 {"key": "mall",             "label": "Galerie commerçante",  "dynamic_offhours": False},
    "shop=department_store":     {"key": "mall",             "label": "Galerie commerçante",  "dynamic_offhours": False},
    "amenity=place_of_worship":  {"key": "place_of_worship", "label": "Lieu de culte",        "dynamic_offhours": False},
}

# Le métro se reconnaît à une combinaison de tags (railway=station + type métro),
# donc il est traité à part plutôt que dans le dictionnaire simple ci-dessus.
METRO = {"key": "metro", "label": "Station de métro", "dynamic_offhours": False}

# --- Outils -----------------------------------------------------------------

def load_query() -> str:
    if not QUERY_FILE.exists():
        sys.exit(f"Requête introuvable : {QUERY_FILE}")
    return QUERY_FILE.read_text(encoding="utf-8")


def run_overpass(query: str, attempts: int = 3) -> dict:
    """Interroge Overpass en POST. Réessaie si le serveur est surchargé."""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    for i in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                OVERPASS_URL, data=data,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — on veut réessayer largement
            print(f"  tentative {i}/{attempts} échouée : {e}")
            if i < attempts:
                time.sleep(10 * i)  # backoff : 10s, 20s…
    sys.exit("Overpass injoignable après plusieurs tentatives.")


def category_of(tags: dict):
    """Retrouve la catégorie d'un élément à partir de ses tags."""
    # cas spécial : station de métro (railway=station + type métro)
    if tags.get("railway") == "station" and (
        tags.get("station") == "subway" or tags.get("subway") == "yes"
    ):
        return METRO
    for combo, meta in CATEGORIES.items():
        k, v = combo.split("=")
        if tags.get(k) == v:
            return meta
    return None


def tri_state(value):
    """wheelchair : yes / limited / no, sinon 'inconnu'."""
    if value in ("yes", "limited", "no"):
        return value
    return "inconnu"


def yes_or_none(value):
    """Pour toilets/bench/… : True si 'yes', None si absent/inconnu."""
    if value == "yes":
        return True
    if value in ("no",):
        return False
    return None


def address_of(tags: dict):
    """Adresse lisible, convention belge : rue puis numéro (« Tomberg 229 »).

    Utile surtout HORS-LIGNE : quand le bouton « M'y emmener » ne peut pas
    joindre OpenStreetMap, l'adresse écrite reste lisible et montrable.
    None si OSM ne renseigne pas la rue — on n'invente pas.
    """
    street = tags.get("addr:street")
    if not street:
        return None
    number = tags.get("addr:housenumber")
    return f"{street} {number}" if number else street


def coords(el: dict):
    """Point unique, y compris pour ways/relations (grâce à 'out center')."""
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    center = el.get("center")
    if center:
        return center.get("lat"), center.get("lon")
    return None, None


# --- Transformation ---------------------------------------------------------

def build(elements: list) -> list:
    abris = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # un abri sans nom n'aide personne

        meta = category_of(tags)
        if not meta:
            continue

        lat, lon = coords(el)
        if lat is None:
            continue

        osm_id = f"{el.get('type')}/{el.get('id')}"
        if osm_id in seen:
            continue
        seen.add(osm_id)

        abris.append({
            "id": osm_id,
            "name": name,
            "category": meta["key"],
            "label_fr": meta["label"],
            "lat": lat,
            "lon": lon,
            # adresse écrite : le repli hors-ligne du bouton « M'y emmener »
            "address": address_of(tags),
            # horaires RÉGULIERS au format OSM ; à interpréter sur l'appareil
            # avec opening_hours.js (gère jours fériés, saisons…).
            "opening_hours": tags.get("opening_hours"),
            # nos filtres décisifs
            "wheelchair": tri_state(tags.get("wheelchair")),
            "toilets": yes_or_none(tags.get("toilets")),
            "bench": yes_or_none(tags.get("bench")),
            "drinking_water": yes_or_none(tags.get("drinking_water")),
            "air_conditioning": yes_or_none(tags.get("air_conditioning")),
            # contact
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "website": tags.get("website") or tags.get("contact:website"),
            # hors horaires réguliers : renvoyer vers la source vivante
            "dynamic_offhours": meta["dynamic_offhours"],
        })

    abris.sort(key=lambda a: (a["category"], a["name"]))
    return abris


def main() -> None:
    pretty = "--pretty" in sys.argv
    print(f"Mon cap — récolte des abris ({AREA_LABEL})")

    query = load_query()
    print("Interrogation d'Overpass…")
    raw = run_overpass(query)
    elements = raw.get("elements", [])
    print(f"  {len(elements)} éléments bruts reçus")

    abris = build(elements)
    print(f"  {len(abris)} abris récoltés dans OSM")

    # --- couche curée : le curé l'emporte, mais seulement là où il affirme ---
    import curation
    cures, ajouts, ecartes, warns = curation.load()
    if cures or ajouts or ecartes:
        avant = len(abris)
        abris = [a for a in abris if a["id"] not in ecartes]
        print(f"  − {avant - len(abris)} écartés (onglet « {curation.SHEET_INACTIVE} »)")
        n = 0
        for a in abris:
            if a["id"] in cures:
                curation.overlay(a, cures[a["id"]])
                n += 1
        print(f"  ✎ {n} abris corrigés par la couche curée")
        for cur in ajouts:
            abris.append(curation.to_abri(cur))
        print(f"  + {len(ajouts)} ajouts absents d'OSM")
        abris.sort(key=lambda a: (a["category"], a["name"]))
    for w in warns:
        print(f"  ⚠ {w}")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "© les contributeurs d'OpenStreetMap (ODbL)",
        "area": AREA_LABEL,
        "count": len(abris),
        "abris": abris,
    }

    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )

    # petit récap pour les logs de l'Action
    par_cat = {}
    for a in abris:
        par_cat[a["label_fr"]] = par_cat.get(a["label_fr"], 0) + 1
    print(f"  {len(abris)} abris retenus → {OUTPUT_FILE.name}")
    for label, n in sorted(par_cat.items()):
        print(f"    · {label} : {n}")
    sans_horaire = sum(1 for a in abris if not a["opening_hours"])
    if sans_horaire:
        print(f"  ⚠ {sans_horaire} abris sans horaires renseignés "
              f"(à afficher sans promettre l'ouverture, ou à compléter sur OSM)")
    sans_adresse = sum(1 for a in abris if not a["address"])
    if sans_adresse:
        print(f"  ⚠ {sans_adresse} abris sans adresse "
              f"(à compléter par la couche curée : c'est le repli hors-ligne)")


if __name__ == "__main__":
    main()
