"""Simple VIN decoder with validation and model year parsing."""

from typing import Dict, Optional


TRANSLITERATION = {
    **{str(i): i for i in range(10)},
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "P": 7,
    "R": 9,
    "S": 2,
    "T": 3,
    "U": 4,
    "V": 5,
    "W": 6,
    "X": 7,
    "Y": 8,
    "Z": 9,
}

WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

YEAR_CODES = {
    # 1980-2009
    "A": 1980,
    "B": 1981,
    "C": 1982,
    "D": 1983,
    "E": 1984,
    "F": 1985,
    "G": 1986,
    "H": 1987,
    "J": 1988,
    "K": 1989,
    "L": 1990,
    "M": 1991,
    "N": 1992,
    "P": 1993,
    "R": 1994,
    "S": 1995,
    "T": 1996,
    "V": 1997,
    "W": 1998,
    "X": 1999,
    "Y": 2000,
    "1": 2001,
    "2": 2002,
    "3": 2003,
    "4": 2004,
    "5": 2005,
    "6": 2006,
    "7": 2007,
    "8": 2008,
    "9": 2009,
    # 2010-2039
    "A2": 2010,
    "B2": 2011,
    "C2": 2012,
    "D2": 2013,
    "E2": 2014,
    "F2": 2015,
    "G2": 2016,
    "H2": 2017,
    "J2": 2018,
    "K2": 2019,
    "L2": 2020,
    "M2": 2021,
    "N2": 2022,
    "P2": 2023,
    "R2": 2024,
    "S2": 2025,
    "T2": 2026,
    "V2": 2027,
    "W2": 2028,
    "X2": 2029,
    "Y2": 2030,
    "12": 2031,
    "22": 2032,
    "32": 2033,
    "42": 2034,
    "52": 2035,
    "62": 2036,
    "72": 2037,
    "82": 2038,
    "92": 2039,
}


def _check_digit(vin: str) -> Optional[bool]:
    try:
        total = 0
        for i, ch in enumerate(vin):
            value = TRANSLITERATION[ch]
            weight = WEIGHTS[i]
            total += value * weight
        remainder = total % 11
        expected = "X" if remainder == 10 else str(remainder)
        return vin[8] == expected
    except KeyError:
        # Invalid characters like I, O, Q or others not in map
        return None


def _model_year(vin: str) -> Optional[int]:
    code = vin[9]
    # Determine cycle based on approximate year; prefer newer cycle
    if not code:
        return None
    return YEAR_CODES.get(f"{code}2", YEAR_CODES.get(code))


def decode_vin(vin: str) -> Dict[str, str]:
    """Decode a VIN into its component parts and include validation.

    - WMI (first 3)
    - VDS (next 6)
    - VIS (last 8)
    - valid_check_digit (bool or None if undecidable due to invalid chars)
    - model_year (best-effort)
    - plant (position 11)
    """
    if len(vin) != 17:
        raise ValueError("VIN must be 17 characters long")

    vin = vin.upper()

    wmi = vin[:3]
    vds = vin[3:9]
    vis = vin[9:]
    valid = _check_digit(vin)
    year = _model_year(vin)
    plant = vin[10]

    data = {
        "vin": vin,
        "wmi": wmi,
        "vds": vds,
        "vis": vis,
        "valid_check_digit": valid,
        "model_year": year,
        "plant": plant,
    }
    return {k: v for k, v in data.items() if v is not None or k in {"vin", "wmi", "vds", "vis"}}


def get_make_from_wmi(wmi: str) -> Optional[str]:
    """Basic lookup for car make based on WMI."""
    wmi_to_make = {
        "1G1": "Chevrolet",
        "1G2": "Pontiac",
        "1GC": "Chevrolet",
        "1GT": "GMC",
        "2G1": "Chevrolet",
        "2G2": "Pontiac",
        "3G1": "Chevrolet",
        "3G2": "Pontiac",
        "4F2": "Mazda",
        "4M0": "Mercury",
        "5J6": "Honda",
        "JA3": "Mitsubishi",
        "JF1": "Subaru",
        "JM1": "Mazda",
        "JSA": "Suzuki",
        "KNA": "Kia",
        "LDC": "Honda",
        "LTV": "Toyota",
        "LVV": "Chery",
        "LSJ": "MG",
        "MAJ": "Mazda",
        "MNT": "Nissan",
        "NMT": "Nissan",
        "NM0": "Nissan",
        "PE1": "Ford",
        "PL1": "Hyundai",
        "RL1": "Renault",
        "SAD": "Land Rover",
        "SAJ": "Jaguar",
        "SAL": "Land Rover",
        "SAR": "Audi",
        "SAT": "Toyota",
        "SCA": "Scania",
        "SCC": "Lotus",
        "SCE": "Fiat",
        "SCF": "Ferrari",
        "SCL": "Mercedes-Benz",
        "SCM": "Mercedes-Benz",
        "SCN": "Porsche",
        "SCO": "Skoda",
        "SCP": "Porsche",
        "SCT": "Toyota",
        "SFD": "Ford",
        "SHH": "Honda",
        "SHS": "Honda",
        "SIT": "Toyota",
        "SJK": "Nissan",
        "SJN": "Nissan",
        "SKF": "Skoda",
        "TMA": "Hyundai",
        "TMB": "Skoda",
        "TRU": "Audi",
        "U5Y": "Kia",
        "VF1": "Renault",
        "VF3": "Peugeot",
        "VF7": "Citroen",
        "VSS": "Seat",
        "WBA": "BMW",
        "WDB": "Mercedes-Benz",
        "WMA": "BMW",
        "WME": "Mercedes-Benz",
        "WVW": "Volkswagen",
        "XMC": "Mitsubishi",
        "XTA": "Lada",
        "YK1": "Saab",
        "YS3": "Saab",
        "ZFA": "Fiat",
        "ZFF": "Ferrari",
        "ZHW": "Lamborghini",
        "ZOM": "Mercedes-Benz",
    }
    return wmi_to_make.get(wmi.upper())


if __name__ == "__main__":
    # Example usage:
    vin_number = "1M8GDM9A0KP042788"  # Example VIN
    decoded_data = decode_vin(vin_number)
    print(decoded_data)

    vin_number_invalid = "1M8GDM9A0KP04278"  # Invalid length
    try:
        decode_vin(vin_number_invalid)
    except ValueError as e:
        print(f"Error: {e}")

    vin_number_bad_chars = "1M8GDM9A0KO042788"  # Contains 'O'
    decoded_data_bad_chars = decode_vin(vin_number_bad_chars)
    print(decoded_data_bad_chars)
