import pytest

from mrml import config, data_io


@pytest.fixture(scope="session")
def raw_path():
    path = config.EXTRACT_DIR / config.CLEVELAND_FILENAME
    if not path.exists():
        pytest.skip("Veri yok — önce `python scripts/run_phase1.py` çalıştırın.")
    return path


@pytest.fixture(scope="session")
def df(raw_path):
    return data_io.load_cleveland(raw_path)
