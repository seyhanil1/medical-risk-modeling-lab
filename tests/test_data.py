"""Gerçek Cleveland verisi üzerinde bütünlük ve belgeyle uyum testleri."""
import pandas as pd

from mrml import audit, config, data_io


def test_sha256_matches_recorded(raw_path):
    assert data_io.sha256_of(raw_path) == config.EXPECTED_SHA256[config.CLEVELAND_FILENAME]


def test_shape_matches_documentation(df):
    assert df[config.COLUMNS].shape == (303, 14)
    assert audit.check_shape(df)["ok"]


def test_target_counts_match_names_file(df):
    # heart-disease.names, bölüm 10: Cleveland 164 / 55 / 36 / 35 / 13
    counts = df["num"].value_counts().sort_index().tolist()
    assert counts == [164, 55, 36, 35, 13]


def test_binary_target_derivation(df):
    assert df["disease"].value_counts().sort_index().tolist() == [164, 139]
    assert ((df["num"] > 0).astype(int) == df["disease"].astype(int)).all()


def test_missing_values_only_in_ca_and_thal(df):
    miss = df[config.COLUMNS].isna().sum()
    assert miss["ca"] == 4
    assert miss["thal"] == 2
    assert miss.drop(["ca", "thal"]).sum() == 0


def test_no_duplicates(df):
    assert audit.duplicate_summary(df)["n_exact_duplicate_rows"] == 0


def test_no_out_of_domain_codes(df):
    issues = audit.consistency_issues(df)
    assert (issues["severity"] == "error").sum() == 0


def test_integer_codes_are_int64(df):
    for col in config.COLUMNS:
        if col != "oldpeak":
            assert str(df[col].dtype) == "Int64", col
    assert pd.api.types.is_float_dtype(df["oldpeak"])


def test_other_site_checksums_recorded_and_match(raw_path):
    # raw_path fixture: veri indirilmemişse (yeni klon) test atlanır, hata vermez
    for fname in config.OTHER_SITES.values():
        path = config.EXTRACT_DIR / fname
        assert data_io.sha256_of(path) == config.EXPECTED_SHA256[fname]


def test_no_patient_overlap_between_sites(df):
    """Merkezler arasında 13 değişkende birebir aynı kayıt yok (aynı kişinin iki merkezde
    bulunmasına karşı kaba bir kontrol; kimlik bilgisi olmadığından kesin değildir)."""
    feats = [c for c in config.COLUMNS if c != "num"]
    frames = [df[feats].assign(site="Cleveland")]
    frames += [data_io.load_site(f)[feats].assign(site=s) for s, f in config.OTHER_SITES.items()]
    allr = pd.concat(frames, ignore_index=True)
    dup = allr[allr.duplicated(subset=feats, keep=False)]
    sites_per_record = dup.groupby(feats, dropna=False)["site"].nunique()
    assert (sites_per_record <= 1).all()
