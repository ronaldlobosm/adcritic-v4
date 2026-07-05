"""
app/cities.py — State and city lookup for the cascading
country -> state -> city selector on the edit profile page.

Data source: dr5hn/countries-states-cities-database (MIT license),
filtered to the countries already listed in app/countries.py and
matched by ISO 3166-1 alpha-2 code.
"""
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(_DATA_DIR, "states.json"), encoding="utf-8") as f:
    _STATES_BY_COUNTRY = json.load(f)

with open(os.path.join(_DATA_DIR, "cities_by_state.json"), encoding="utf-8") as f:
    _CITIES_BY_STATE = json.load(f)


def states_for_country(code):
    """Return sorted list of state/province names for an ISO alpha-2 country code."""
    return _STATES_BY_COUNTRY.get((code or "").upper(), [])


def cities_for_state(country_code, state_name):
    """Return sorted list of city names for a state/province within a country."""
    return _CITIES_BY_STATE.get((country_code or "").upper(), {}).get(state_name or "", [])
