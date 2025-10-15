#!/usr/bin/env python3
"""
Utility to download component assets from the Nexar Supply GraphQL API.

Requirements:
    - Python 3.8+
    - Network access to https://identity.nexar.com and https://api.nexar.com

Authentication:
    The script prefers the environment variables `NEXAR_CLIENT_ID`
    and `NEXAR_CLIENT_SECRET` (client-credentials flow).  You can also pass
    an access token directly via `--token` to avoid requesting a new one,
    which helps when you are working with a limited number of tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

GRAPHQL_ENDPOINT = "https://api.nexar.com/graphql"
TOKEN_ENDPOINT = "https://identity.nexar.com/connect/token"
DEFAULT_SCOPE = "supply.domain"
USER_AGENT = "NESP-NexarDownloader/1.0 (+https://github.com/)"


@dataclass
class PartSpec:
    mpn: str
    folder: str
    description: str


PARTS: Iterable[PartSpec] = [
    PartSpec(
        mpn="ESP32-S3-WROOM-1-N16R8",
        folder="esp32 module",
        description="ESP32-S3 module, 16 MB Flash + 8 MB PSRAM",
    ),
    PartSpec(
        mpn="CL10B104KB8NNNC",
        folder="decoupling capacitor",
        description="0.1 µF 0603 X7R decoupling capacitor",
    ),
    PartSpec(
        mpn="CL10A106KP8NNNC",
        folder="local bulk capacitor",
        description="10 µF 6.3 V X5R local bulk capacitor",
    ),
    PartSpec(
        mpn="RC0603FR-0710KL",
        folder="enable resistor",
        description="10 kΩ 0603 EN pull-up resistor",
    ),
    PartSpec(
        mpn="KMR211GLFS",
        folder="reset switch",
        description="C&K KMR2 4×4 mm tactile reset switch",
    ),
    PartSpec(
        mpn="RC0603FR-07100RL",
        folder="reset resistor",
        description="100 Ω 0603 EN series resistor",
    ),
    PartSpec(
        mpn="B2B-PH-SM4-TB",
        folder="battery connector",
        description="JST-PH 2-pin battery connector",
    ),
    PartSpec(
        mpn="NCP15XH103F03RC",
        folder="battery ntc",
        description="Murata 10 kΩ NTC thermistor for battery sensing",
    ),
    PartSpec(
        mpn="0ZCJ0100FF2E",
        folder="battery polyfuse",
        description="Bel Fuse 1 A battery polyfuse",
    ),
    PartSpec(
        mpn="0ZCJ0150FF2C",
        folder="vbus polyfuse",
        description="Bel Fuse 1.5 A VBUS polyfuse",
    ),
    PartSpec(
        mpn="LQH32PN2R2NN0",
        folder="vbus inductor",
        description="Murata 2.2 µH 2 A inductor",
    ),
    PartSpec(
        mpn="RC0805FR-075K1L",
        folder="usb cc resistor",
        description="5.1 kΩ 1% USB-C CC pull-down resistor",
    ),
    PartSpec(
        mpn="PESD5V0S4UD",
        folder="usb esd array",
        description="Nexperia 4-channel USB ESD array",
    ),
    PartSpec(
        mpn="GRM31CR60J226ME",
        folder="buck output capacitor",
        description="Murata 22 µF 10 V X5R capacitor",
    ),
    PartSpec(
        mpn="GRM32DR61E106KA12L",
        folder="power bulk capacitor",
        description="Murata 10 µF 25 V X5R bulk capacitor",
    ),
    PartSpec(
        mpn="SMAJ5.0A",
        folder="vbus tvs diode",
        description="Littelfuse SMAJ5.0A TVS diode",
    ),
    PartSpec(
        mpn="EEE-FC1A101P",
        folder="display amp bulk capacitor",
        description="Panasonic 100 µF 10 V electrolytic capacitor",
    ),
    PartSpec(
        mpn="RC0603FR-0747KL",
        folder="spi pullup resistor",
        description="47 kΩ 0603 pull-up resistor",
    ),
    PartSpec(
        mpn="LTST-C190KRKT",
        folder="indicator led",
        description="Lite-On LTST-C190 series 0603 LED",
    ),
    PartSpec(
        mpn="RC0603FR-071K0L",
        folder="led resistor",
        description="1 kΩ 0603 LED current-limiting resistor",
    ),
    PartSpec(
        mpn="CT11025.0F260",
        folder="tact switch",
        description="CIT 6×6 mm tact switch, 5 mm actuator",
    ),
    PartSpec(
        mpn="MAX98357AETE+T",
        folder="class d amplifier",
        description="Analog Devices MAX98357A I²S Class-D amplifier",
    ),
    PartSpec(
        mpn="CVS-1508",
        folder="speakers",
        description="SameSky 15 mm 8 Ω speaker",
    ),
    PartSpec(
        mpn="RC0603FR-0710RL",
        folder="zobel resistor",
        description="10 Ω 0603 resistor for Zobel network",
    ),
    PartSpec(
        mpn="C0603C474K4RACTU",
        folder="zobel capacitor",
        description="Kemet 0.47 µF 0603 capacitor",
    ),
    PartSpec(
        mpn="PESD5V0S1UL",
        folder="sd esd protection",
        description="Nexperia PESD5V0S1UL ESD protection diode",
    ),
]


def http_post_form(url: str, data: Dict[str, str], timeout: float = 30.0) -> Dict[str, object]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def http_post_json(
    url: str,
    payload: Dict[str, object],
    token: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, object]:
    encoded = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=encoded, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_token(client_id: str, client_secret: str, scope: str = DEFAULT_SCOPE) -> str:
    response = http_post_form(
        TOKEN_ENDPOINT,
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
    )
    token = response.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to obtain token from Nexar: {response}")
    return token


def fetch_part(token: str, mpn: str) -> Dict[str, object]:
    query = """
    query ($mpn: String!) {
      supSearch(q: $mpn, limit: 1) {
        results {
          part {
            mpn
            manufacturer { name }
            shortDescription
            sellers { company { name } }
            bestDatasheet { name url }
            documentCollections {
              name
              documents { name url }
            }
            cad {
              addToLibraryUrl
              hasKicad
              downloadUrlKicad
              hasAltium
              downloadUrlAltium
              hasEagle
              downloadUrlEagle
              hasOrcad
              downloadUrlOrcad
            }
          }
        }
      }
    }
    """
    data = http_post_json(
        GRAPHQL_ENDPOINT,
        payload={"query": query, "variables": {"mpn": mpn}},
        token=token,
    )
    if "errors" in data:
        raise RuntimeError(f"Nexar query error for {mpn}: {data['errors']}")
    results = data.get("data", {}).get("supSearch", {}).get("results") or []
    if not results:
        raise RuntimeError(f"Nexar did not return a result for {mpn}")
    return results[0]["part"]


def pick_datasheet(part: Dict[str, object]) -> Optional[Dict[str, str]]:
    best = part.get("bestDatasheet") or {}
    if best.get("url"):
        return {"name": best.get("name") or "Datasheet", "url": best["url"]}
    seen = set()
    for collection in part.get("documentCollections") or []:
        for doc in collection.get("documents") or []:
            url = doc.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            name = doc.get("name") or collection.get("name") or "Document"
            if "datasheet" in name.lower():
                return {"name": name, "url": url}
    return None


def download_file(url: str, destination: Path, *, overwrite: bool = False) -> bool:
    if destination.exists() and not overwrite and destination.stat().st_size > 0:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, destination.open("wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc
    return True


def ensure_digikey_seller(part: Dict[str, object]) -> bool:
    sellers = part.get("sellers") or []
    for seller in sellers:
        company = (seller or {}).get("company") or {}
        if company.get("name", "").strip().lower() == "digikey":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download datasheets (and KiCad libraries when available) from Nexar."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "components",
        help="Base output directory (default: %(default)s)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("NEXAR_ACCESS_TOKEN"),
        help="Existing Nexar access token (optional)",
    )
    parser.add_argument(
        "--client-id",
        default=os.getenv("NEXAR_CLIENT_ID"),
        help="Nexar client ID (optional when --token is supplied)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.getenv("NEXAR_CLIENT_SECRET"),
        help="Nexar client secret (optional when --token is supplied)",
    )
    parser.add_argument(
        "--skip-cad",
        action="store_true",
        help="Skip downloading KiCad libraries even if available",
    )
    args = parser.parse_args()

    token = args.token
    if not token:
        if not args.client_id or not args.client_secret:
            parser.error("Either --token or both --client-id/--client-secret must be provided.")
        token = fetch_token(args.client_id, args.client_secret)
    else:
        token = token.strip()

    base_dir = args.output
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Saving assets into: {base_dir}")
    print()

    for spec in PARTS:
        print(f"=== {spec.mpn} ({spec.description}) ===")
        try:
            part = fetch_part(token, spec.mpn)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! Failed to fetch part information: {exc}")
            print()
            continue

        digi_available = ensure_digikey_seller(part)
        if not digi_available:
            print("  ! Warning: DigiKey does not list this part in Nexar's seller data.")

        target_dir = base_dir / spec.folder
        target_dir.mkdir(parents=True, exist_ok=True)

        datasheet = pick_datasheet(part)
        if datasheet:
            filename = f"{spec.mpn} datasheet.pdf"
            file_path = target_dir / filename
            try:
                changed = download_file(datasheet["url"], file_path)
                status = "downloaded" if changed else "already up to date"
                print(f"  - Datasheet ({status}): {file_path}")
            except Exception as exc:  # noqa: BLE001
                print(f"  ! Failed to download datasheet: {exc}")
        else:
            print("  ! No datasheet URL reported by Nexar.")

        if not args.skip_cad:
            cad_info = part.get("cad") or {}
            kicad_url = cad_info.get("downloadUrlKicad")
            if cad_info.get("hasKicad") and kicad_url:
                ext = Path(urllib.parse.urlparse(kicad_url).path).suffix or ".zip"
                cad_path = target_dir / f"{spec.mpn} kicad{ext}"
                try:
                    changed = download_file(kicad_url, cad_path)
                    status = "downloaded" if changed else "already up to date"
                    print(f"  - KiCad library ({status}): {cad_path}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  ! Failed to download KiCad library: {exc}")
            else:
                print("  - KiCad library: not published (or not accessible with current plan).")
        print()
        # Polite spacing between API calls
        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
