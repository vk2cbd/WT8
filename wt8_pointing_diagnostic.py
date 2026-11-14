#!/usr/bin/env python3
"""Read-only astronomical pointing comparison. Never connects to antenna hardware.

Examples:
  python3 wt8_pointing_diagnostic.py source --ra-hours 16.5 --dec-deg -26 --time 2026-11-14T10:00:00Z
  python3 wt8_pointing_diagnostic.py moon --time 2026-11-14T10:00:00Z
  python3 wt8_pointing_diagnostic.py sun --time 2026-11-14T10:00:00Z

Requires: python3 -m pip install astropy
All calculations are geometric (atmospheric pressure=0).
"""
from __future__ import annotations

import argparse
import math
from datetime import datetime, timezone

from wt8_astro import equatorial_to_horizontal, moon_position


def parse_utc(value):
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("--time must include a UTC offset or Z")
    return when.astimezone(timezone.utc)


def astropy_altaz(target, latitude, longitude, when, ra_hours=None, dec_deg=None):
    import astropy.units as u
    from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body, get_sun
    from astropy.time import Time

    location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=0 * u.m)
    instant = Time(when)
    frame = AltAz(obstime=instant, location=location, pressure=0 * u.hPa)
    if target == "source":
        coord = SkyCoord(ra=ra_hours * u.hourangle, dec=dec_deg * u.deg, frame="icrs")
    elif target == "sun":
        coord = get_sun(instant)
    else:
        coord = get_body("moon", instant, location)
    horizontal = coord.transform_to(frame)
    return float(horizontal.az.deg), float(horizontal.alt.deg)


def angular_separation(az1, el1, az2, el2):
    """Great-circle angular separation in arcminutes (stable for small offsets)."""
    a1, e1, a2, e2 = map(math.radians, (az1, el1, az2, el2))
    delta_az = a2 - a1
    hav = math.sin((e2 - e1) / 2.0)**2 + math.cos(e1) * math.cos(e2) * math.sin(delta_az / 2.0)**2
    return math.degrees(2.0 * math.asin(math.sqrt(max(0.0, min(1.0, hav))))) * 60


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=("source", "sun", "moon"))
    parser.add_argument("--ra-hours", type=float)
    parser.add_argument("--dec-deg", type=float)
    parser.add_argument("--latitude", type=float, default=-32.724)
    parser.add_argument("--longitude", type=float, default=152.130167)
    parser.add_argument("--time", required=True, help="UTC ISO8601 with Z or offset")
    args = parser.parse_args(argv)
    when = parse_utc(args.time)
    if not (-90 <= args.latitude <= 90 and -180 <= args.longitude <= 180):
        parser.error("Invalid site latitude/longitude")
    if args.target == "source":
        if args.ra_hours is None or args.dec_deg is None:
            parser.error("source requires --ra-hours and --dec-deg (ICRS/J2000)")
        if not (math.isfinite(args.ra_hours) and math.isfinite(args.dec_deg)
                and 0 <= args.ra_hours < 24 and -90 <= args.dec_deg <= 90):
            parser.error("Invalid source RA/Dec")
        old = equatorial_to_horizontal(args.ra_hours, args.dec_deg, args.latitude, args.longitude, when)
    elif args.target == "moon":
        p = moon_position(args.latitude, args.longitude, when)
        old = (p.azimuth, p.elevation)
    else:
        old = None  # WT8 has no native Sun position calculation in wt8_astro.py
    try:
        new = astropy_altaz(args.target, args.latitude, args.longitude, when, args.ra_hours, args.dec_deg)
    except ImportError as exc:
        parser.error(f"Astropy is required: {exc}")
    print(f"Target: {args.target} | UTC: {when.isoformat()} | site: {args.latitude:.6f}, {args.longitude:.6f}")
    print(f"Astropy geometric: Az {new[0]:.6f} deg, El {new[1]:.6f} deg")
    if old is None:
        print("WT8 legacy: not available for Sun; no comparison calculated")
        return
    daz = (old[0] - new[0] + 180) % 360 - 180
    delv = old[1] - new[1]
    print(f"WT8 legacy:       Az {old[0]:.6f} deg, El {old[1]:.6f} deg")
    print(f"Legacy minus Astropy: dAz {daz*60:+.3f} arcmin, dEl {delv*60:+.3f} arcmin")
    print(f"Great-circle separation: {angular_separation(*old, *new):.3f} arcmin")
    print("Diagnostic only: no antenna commands or tracking settings changed.")


if __name__ == "__main__":
    main()
