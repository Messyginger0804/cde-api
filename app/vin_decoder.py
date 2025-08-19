"""Simple VIN decoder."""

from typing import Dict


def decode_vin(vin: str) -> Dict[str, str]:
    """Decode a VIN into its component parts.

    The function performs minimal validation and splits the VIN into
    WMI (first 3 characters), VDS (next 6 characters), and VIS (last 8 characters).
    """
    if len(vin) != 17:
        raise ValueError("VIN must be 17 characters long")

    return {
        "vin": vin,
        "wmi": vin[:3],
        "vds": vin[3:9],
        "vis": vin[9:],
    }
