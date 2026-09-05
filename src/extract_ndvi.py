"""
extract_ndvi.py
----------------
Extrait des séries temporelles NDVI (Sentinel-2) pour des zones du Niger
(Diffa, Tillabéri, Zinder) via Google Earth Engine, et les exporte en CSV.

Prérequis :
    pip install earthengine-api geemap pandas
    Puis, la première fois : earthengine authenticate
    (nécessite un compte Google Earth Engine gratuit : https://earthengine.google.com)

Utilisation :
    python src/extract_ndvi.py
"""

import ee
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------------
# 1. Initialisation de Earth Engine
# ---------------------------------------------------------------------------
# Remplace "your-project-id" par l'ID de ton projet Google Cloud associé à GEE
ee.Initialize(project="desertification-niger")

# ---------------------------------------------------------------------------
# 2. Définition des zones d'étude (bounding boxes approximatives — à affiner)
# ---------------------------------------------------------------------------
ZONES = {
    "Diffa": ee.Geometry.Rectangle([12.8, 13.0, 13.5, 13.6]),
   "Tillaberi": ee.Geometry.Rectangle([0.9, 14.0, 1.6, 14.6]),
    "Zinder": ee.Geometry.Rectangle([8.7, 13.5, 9.4, 14.1]),
}

START_DATE = "2016-01-01"
END_DATE = "2025-12-31"
# Pas de temps : ici mensuel. Mets "YS" pour un pas annuel si tu préfères une série plus légère.
FREQ = "MS"


# ---------------------------------------------------------------------------
# 3. Fonctions de traitement
# ---------------------------------------------------------------------------
def mask_clouds_s2(image):
    """Masque les nuages à partir de la bande SCL (Scene Classification Layer)."""
    scl = image.select("SCL")
    # Classes à exclure : 3 (ombre nuage), 8 (nuage moyenne proba),
    # 9 (nuage haute proba), 10 (cirrus)
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def add_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


def get_monthly_ndvi(zone_geom, start, end):
    """Retourne une série temporelle NDVI moyen (mensuel) pour une géométrie donnée."""
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(zone_geom)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .map(mask_clouds_s2)
        .map(add_ndvi)
    )

    dates = pd.date_range(start, end, freq=FREQ)
    records = []

    for d in dates:
        period_start = d.strftime("%Y-%m-%d")
        #print(f" -> {period_start}", end=" ", flush=True)
        period_end = (d + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")
        monthly = collection.filterDate(period_start, period_end)
        count = monthly.size().getInfo()
        if count == 0:
            records.append({"date": period_start, "ndvi_mean": None, "n_images": 0})
            continue

        ndvi_img = monthly.select("NDVI").median()
        stats = ndvi_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=zone_geom,
            scale=30,
            maxPixels=1e9,
        )
        ndvi_mean = stats.get("NDVI").getInfo()
        records.append({"date": period_start, "ndvi_mean": ndvi_mean, "n_images": count})

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 4. Exécution principale
# ---------------------------------------------------------------------------
def main():
    for zone_name, geom in ZONES.items():
        print(f"Extraction NDVI pour {zone_name}...")
        df = get_monthly_ndvi(geom, START_DATE, END_DATE)
        out_path = f"data/ndvi_{zone_name.lower()}.csv"
        df.to_csv(out_path, index=False)
        print(f"  -> Sauvegardé dans {out_path} ({len(df)} lignes)")


if __name__ == "__main__":
    main()
