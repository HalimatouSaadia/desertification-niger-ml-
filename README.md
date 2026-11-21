# Détection de la désertification par imagerie satellite — Niger

## Contexte et objectif
Suivre l'évolution du couvert végétal dans trois zones sensibles du Niger
(Diffa, Tillabéri, Zinder) entre 2000 et 2025, afin de détecter et
quantifier l'avancée (ou le recul) de la désertification à partir de
séries temporelles NDVI dérivées de l'imagerie satellite (Landsat et
Sentinel-2).

## Données utilisées
- **Copernicus / Sentinel-2 SR** (2016-2025) via Google Earth Engine 
  NDVI, résolution 10 m. https://developers.google.com/earthengine/datasets
- **USGS Landsat 5/7/8** (2000-2015) via Google Earth Engine NDVI,
  résolution 30 m, pour étendre la série avant l'existence de Sentinel-2.
  https://earthexplorer.usgs.gov
- **HDX / SRTM** — modèle numérique de terrain (élévation), pour
  contextualiser les zones. https://data.humdata.org/dataset/niger-elevation-model

## Méthodologie
1. **Extraction NDVI mensuelle** (Sentinel-2, 2016-2025) et **annuelle**
   (Landsat, 2000-2015) sur les 3 zones, avec masquage des nuages.
2. **Fusion des deux séries** en une chronologie continue 2000-2025
   (NDVI max annuel par zone).
3. **Calcul de tendance par pixel** (régression linéaire NDVI ~ année,
   2016-2025) pour cartographier les zones de reverdissement / dégradation
   au sein de chaque région.
4. **Classification par seuils NDVI** en 3 classes : sol nu (< 0.15),
   végétation clairsemée (0.15-0.30), végétation dense (≥ 0.30).
5. **Quantification des surfaces** (km²) par classe, comparées entre 2016
   et 2025.

## Installation
```bash
python -m venv venv
source venv/bin/activate   # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
earthengine authenticate   # une seule fois, nécessite un compte GEE gratuit
```
Le projet Google Cloud associé doit être enregistré pour Earth Engine
(voir https://code.earthengine.google.com/register).

## Exécution
```bash
python src/extract_ndvi.py        # génère data/ndvi_<zone>.csv (2016-2025)
jupyter notebook
```
Puis ouvrir `Notebooks/01_exploration_ndvi.ipynb` et exécuter les cellules
dans l'ordre (Kernel > Restart Kernel and Run All Cells).

## Structure du dépôt
```
desertification-niger-ml/
├── data/            # séries CSV (NDVI, classification, élévation)
├── Notebooks/       # 01_exploration_ndvi.ipynb — analyse complète
├── src/             # extract_ndvi.py — extraction NDVI Sentinel-2
├── outputs/         # cartes, graphiques
├── requirements.txt
└── README.md
```

## Aperçu des résultats

### Évolution NDVI 2000-2025
Les trois zones montrent une tendance de **reverdissement global** sur la
période, cohérente avec le phénomène documenté de « Sahel greening »
(récupération partielle après les sécheresses des années 1970-80).
Voir `outputs/ndvi_full_series_2000_2025.png`.

### Cartes de tendance par pixel (2016-2025)
Malgré le reverdissement dominant (vert), chaque zone présente des
**poches de dégradation localisée** (rouge) :
- **Diffa** : dégradation concentrée dans un secteur au nord-est de la zone.
- **Tillabéri** : dégradation limitée, deux foyers isolés près du fleuve Niger.
- **Zinder** : dégradation associée à des axes de circulation visibles sur l'image.

### Classification et quantification (km²)

| Zone | Sol nu 2016 | Sol nu 2025 | Variation | Végétation dense 2016 | Végétation dense 2025 |

| Diffa | 2204 km² | 879 km² | -60 % | 205 km² | 562 km² |
| Tillabéri | 2225 km² | 2202 km² | -1 % (stable) | 194 km² | 209 km² |
| Zinder | 3246 km² | 675 km² | -79 % | 28 km² | 53 km² |

Voir `outputs/classification_comparaison_2016_2025.png`.

### Contexte topographique
| Zone | Altitude min | Altitude max | Moyenne |

| Diffa | 267 m | 317 m | 295 m |
| Tillabéri | 188 m | 334 m | 244 m |
| Zinder | 375 m | 655 m | 451 m |

## Limites connues
- Les zones d'étude sont définies par de simples rectangles englobants
  (bounding boxes), pas des limites administratives précises.
  
- La transition Landsat → Sentinel-2 (fin 2015 / début 2016) introduit une
  **rupture méthodologique** visible dans la série temporelle (résolution
  et calibration différentes) : la comparaison directe entre les deux
  périodes doit être interprétée avec prudence. Une partie de la baisse de
  sol nu observée entre 2016 et 2025, notamment pour Zinder, peut refléter
  en partie cet artefact plutôt qu'une évolution écologique réelle.
  
- La classification par seuils NDVI est une méthode simple ; une
  classification supervisée (avec vérité terrain ou imagerie très haute
  résolution) affinerait les résultats.
  
- Le calcul de surface a été effectué à 30 m de résolution (résolution
  Landsat) pour des raisons de performance de calcul, plutôt qu'à 10 m
  (résolution native Sentinel-2).

Prédiction supervisée de la dégradation (3 algorithmes)

Problème: classification binaire au niveau du pixel. À partir des observations 2016-2020 (NDVI, réflectances, relief), prédire si le NDVI maximum annuel moyen ne progresse pas en 2021-2025 (cible « dégradé » : 4,8 % des 11 999 pixels échantillonnés).

Algorithmes comparés: Random Forest, Gradient Boosting, SVM (RBF), plus une baseline tirée au hasard. Validation croisée spatiale (5 plis, blocs de 0,1°).

Baseline :Rappel (0,050), Précision (0,049), F1 (0,050), ROC-AUC(0,501), PR-AUC(0,048)
Random Forest :Rappel (0,012 ), Précision (0,219), F1 (0,023), ROC-AUC(0,769), PR-AUC(0,136)
Gradient Boosting :Rappel (0,206 ), Précision (0,158 ), F1 (0,179 ), ROC-AUC(0,750), PR-AUC(0,123)
SVM (RBF) :Rappel (0,716), Précision (0,109), F1 (0,189), ROC-AUC(0,763), PR-AUC(0,130)

Lecture: le SVM est retenu pour un usage de détection (meilleur rappel, F1 et MCC) au prix de nombreuses fausses alertes ; le Gradient Boosting limite les fausses alertes. Aucun algorithme n'est nettement supérieur.

Limites la cible vient d'images satellite et mesure l'absence de progression du NDVI, pas une désertification confirmée sur le terrain ; Tillabéri concentre 66 % des pixels dégradés ; hyperparamètres non réglés.

Résultats : `outputs/ml_*.png` et `outputs/ml_comparaison_metriques.csv`.
