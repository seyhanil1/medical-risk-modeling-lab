# Third-Party Notices

This project uses, adapts or refers to the third-party material listed below. Each item stays under
its own licence. None of it is relicensed under the project's MIT or CC BY 4.0 terms.

## 1. UCI Heart Disease data set (not redistributed)

- **Title:** Heart Disease
- **Creators:** Andras Janosi, William Steinbrunn, Matthias Pfisterer, Robert Detrano
- **Publisher:** UCI Machine Learning Repository (dataset id 45); donated 1988 by David W. Aha
- **DOI:** https://doi.org/10.24432/C52P4X
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/
- **Use here:** the data are **downloaded at run time** by `scripts/run_phase1.py` and are **not**
  stored in this repository. `data/raw/` and all person-level outputs in `data/private/` are
  git-ignored. Only aggregate result tables and figures derived from these data are published in
  `reports/`.
- **Changes made:** the processed files were parsed; `?` was treated as missing; for the
  non-Cleveland sites, physiologically impossible zeros in `trestbps`/`chol` were set to missing;
  the target `num` (0–4) was dichotomised into `disease = (num > 0)`. The original files are not
  modified.
- **Attribution requested by the data donors:** publications should name the principal
  investigators:
  - Andras Janosi, M.D. — Hungarian Institute of Cardiology, Budapest
  - William Steinbrunn, M.D. — University Hospital, Zurich
  - Matthias Pfisterer, M.D. — University Hospital, Basel
  - Robert Detrano, M.D., Ph.D. — V.A. Medical Center, Long Beach and Cleveland Clinic Foundation
- **Dataset citation:** Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989).
  *Heart Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X
- **Original study:** Detrano, R., Janosi, A., Steinbrunn, W., Pfisterer, M., Schmid, J., Sandhu, S.,
  Guppy, K., Lee, S., & Froelicher, V. (1989). International application of a new probability
  algorithm for the diagnosis of coronary artery disease. *American Journal of Cardiology*, 64(5),
  304–310. https://doi.org/10.1016/0002-9149(89)90524-9. This work is cited only; no text was copied.

`docs/data_dictionary.md` is an **adaptation**. It summarises and translates variable descriptions
and codes from the UCI file `heart-disease.names` (CC BY 4.0, as above) into Turkish and English.

## 2. TRIPOD+AI reporting guideline

- **Source:** Collins, G. S., Moons, K. G. M., Dhiman, P., Riley, R. D., et al. (2024). TRIPOD+AI
  statement: updated guidance for reporting clinical prediction models that use regression or
  machine learning methods. *BMJ*, 385, e078378. https://doi.org/10.1136/bmj-2023-078378
- **Licence of the article:** CC BY 4.0
- **Use here:** `docs/tripod_ai_checklist.md` is an **adaptation** of Table 2. The item numbers and
  section/topic structure follow the original. Each recommendation is **summarised in Turkish, not
  quoted**, and status, location and note columns were added for this project. It is not an
  official translation and is not endorsed by the TRIPOD authors.

## 3. Creative Commons licence text

`LICENSES/CC-BY-4.0.txt` is the unmodified legal code of the Creative Commons Attribution 4.0
International Public License, obtained from
https://creativecommons.org/licenses/by/4.0/legalcode.txt. Creative Commons permits verbatim
copying of its licence texts.

## 4. Python dependencies (not redistributed)

The packages are installed by the user from PyPI and are not part of this repository. They are
listed here for information. Licences were read from the installed package metadata of the tested
versions (`requirements-lock.txt`).

| Package | Tested version | Licence |
|---|---|---|
| numpy | 2.5.5 | BSD-3-Clause (with bundled components under 0BSD, MIT, Zlib, CC0-1.0) |
| pandas | 3.1.1 | BSD-3-Clause |
| scipy | 1.18.1 | BSD-3-Clause |
| matplotlib | 3.11.2 | Matplotlib License (PSF-based) |
| scikit-learn | 1.9.1 | BSD-3-Clause |
| joblib | 1.6.0 | BSD-3-Clause |
| threadpoolctl | 3.8.0 | BSD-3-Clause |
| pytest (development only) | 9.2.0 | MIT |

For the remaining transitive dependencies, check each package's own metadata.
