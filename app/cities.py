"""
app/cities.py — City lookup by country, used for the cascading
country -> city selector on the edit profile page.

Data source: dr5hn/countries-states-cities-database (MIT license),
filtered to the countries already listed in app/countries.py and
matched by ISO 3166-1 alpha-2 code.
"""
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "cities.json")

with open(_DATA_PATH, encoding="utf-8") as f:
    _CITIES_BY_COUNTRY = json.load(f)


def cities_for_country(code):
    """Return sorted list of city names for an ISO alpha-2 country code."""
    return _CITIES_BY_COUNTRY.get((code or "").upper(), [])
