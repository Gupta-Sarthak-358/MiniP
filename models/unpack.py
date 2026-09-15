"""Unpack shipped model zips (optional — predict.py loads from zips transparently).
Run: PY models/unpack.py   (extracts the 7 binaries next to the zips)
"""
import os, zipfile
D = os.path.dirname(os.path.abspath(__file__))
for zn in ("models_rf_avail.zip", "models_rf_veh.zip", "models_rest.zip"):
    zp = os.path.join(D, zn)
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            z.extractall(D)
        print("extracted", zn)
    else:
        print("missing", zn)
