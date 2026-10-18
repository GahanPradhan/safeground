"""National emergency numbers by country (ISO 3166-1 alpha-2). Countries not listed get no guessed number."""
from __future__ import annotations

SOURCE = "https://en.wikipedia.org/wiki/List_of_emergency_telephone_numbers"
_EU112 = [{"number": "112", "for": "Emergency (police, fire, ambulance)"}]
NUMBERS: dict[str, list[dict]] = {
    "IN": [{"number": "112", "for": "National emergency number"}, {"number": "108", "for": "Ambulance"},
           {"number": "101", "for": "Fire and rescue"}],
    "US": [{"number": "911", "for": "Emergency (police, fire, ambulance)"}],
    "CA": [{"number": "911", "for": "Emergency (police, fire, ambulance)"}],
    "MX": [{"number": "911", "for": "Emergency (police, fire, ambulance)"}],
    "PH": [{"number": "911", "for": "Emergency (police, fire, ambulance)"}],
    "GB": [{"number": "999", "for": "Emergency (police, fire, ambulance)"}, {"number": "112", "for": "Emergency (also works)"}],
    "JP": [{"number": "110", "for": "Police"}, {"number": "119", "for": "Fire and ambulance"}],
    "KR": [{"number": "112", "for": "Police"}, {"number": "119", "for": "Fire and ambulance"}],
    "CN": [{"number": "110", "for": "Police"}, {"number": "119", "for": "Fire"}, {"number": "120", "for": "Ambulance"}],
    "TW": [{"number": "110", "for": "Police"}, {"number": "119", "for": "Fire and ambulance"}],
    "HK": [{"number": "999", "for": "Emergency (police, fire, ambulance)"}],
    "SG": [{"number": "999", "for": "Police"}, {"number": "995", "for": "Fire and ambulance"}],
    "MY": [{"number": "999", "for": "Emergency (police, fire, ambulance)"}],
    "ID": [{"number": "112", "for": "Emergency"}],
    "TH": [{"number": "191", "for": "Police"}, {"number": "199", "for": "Fire"}, {"number": "1669", "for": "Ambulance"}],
    "VN": [{"number": "113", "for": "Police"}, {"number": "114", "for": "Fire"}, {"number": "115", "for": "Ambulance"}],
    "AU": [{"number": "000", "for": "Emergency (police, fire, ambulance)"}, {"number": "112", "for": "Emergency from mobiles"}],
    "NZ": [{"number": "111", "for": "Emergency (police, fire, ambulance)"}],
    "BR": [{"number": "190", "for": "Police"}, {"number": "192", "for": "Ambulance"}, {"number": "193", "for": "Fire"}],
    "ZA": [{"number": "10111", "for": "Police"}, {"number": "10177", "for": "Ambulance"}, {"number": "112", "for": "Emergency from mobiles"}],
    "NG": [{"number": "112", "for": "Emergency"}],
    "KE": [{"number": "999", "for": "Emergency"}, {"number": "112", "for": "Emergency"}],
    "EG": [{"number": "122", "for": "Police"}, {"number": "123", "for": "Ambulance"}, {"number": "180", "for": "Fire"}],
    "IL": [{"number": "100", "for": "Police"}, {"number": "101", "for": "Ambulance"}, {"number": "102", "for": "Fire"}],
    "LB": [{"number": "112", "for": "Police"}, {"number": "140", "for": "Ambulance (Lebanese Red Cross)"},
           {"number": "175", "for": "Civil defence and fire"}],
    "AE": [{"number": "999", "for": "Police"}, {"number": "998", "for": "Ambulance"}, {"number": "997", "for": "Fire"}],
    "PK": [{"number": "15", "for": "Police"}, {"number": "1122", "for": "Rescue and ambulance"}],
    "BD": [{"number": "999", "for": "Emergency (police, fire, ambulance)"}],
    "NP": [{"number": "100", "for": "Police"}, {"number": "101", "for": "Fire"}, {"number": "102", "for": "Ambulance"}],
    "RU": [{"number": "112", "for": "Emergency"}],
    "TR": [{"number": "112", "for": "Emergency"}],
    "UA": [{"number": "112", "for": "Emergency"}],
    "NO": [{"number": "112", "for": "Police"}, {"number": "113", "for": "Ambulance"}, {"number": "110", "for": "Fire"}],
    "CH": [{"number": "112", "for": "Emergency"}, {"number": "144", "for": "Ambulance"}, {"number": "118", "for": "Fire"}],
}
for cc in ("AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
           "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS"):
    NUMBERS.setdefault(cc, _EU112)


def numbers(country_code: str | None) -> dict:
    cc = (country_code or "").upper()
    if cc in NUMBERS:
        return {"call": NUMBERS[cc], "source": SOURCE, "known": True}
    return {"call": [], "source": SOURCE, "known": False,
            "note": "SafeGround does not have a checked emergency number for this country; find the local number now."}
