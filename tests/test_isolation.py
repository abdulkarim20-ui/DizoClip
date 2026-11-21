from pathlib import Path

from app.config.paths import KEYS_FILE
from app.core.runtime import user_data_dir


def test_tests_never_use_the_real_user_data_folder():
    real = (Path(__file__).resolve().parents[1] / "User_Data").resolve()
    assert user_data_dir().resolve() != real
    assert not str(Path(KEYS_FILE).resolve()).startswith(str(real))
