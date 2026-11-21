import pytest

from app.core.masking import MASK_WIDTH, looks_masked, mask_secret


@pytest.mark.parametrize("secret", ["a", "abcdefgh", "abcdefghijk"])
def test_short_secrets_reveal_nothing(secret):
    assert set(mask_secret(secret)) == {"*"}


@pytest.mark.parametrize("length", [1, 5, 12, 19, 20, 80])
def test_star_run_has_a_fixed_width(length):
    assert mask_secret("x" * length).count("*") == MASK_WIDTH


def test_long_secret_keeps_only_three_characters_on_each_edge():
    secret = "sk-proj-" + "a" * 40 + "XYZ"
    masked = mask_secret(secret)
    assert masked.startswith("sk-") and masked.endswith("XYZ")
    assert "proj" not in masked


def test_empty_secret_masks_to_empty():
    assert mask_secret("") == ""


def test_looks_masked():
    assert looks_masked("sk-" + "*" * 20 + "xyz")
    assert looks_masked("•" * 8)
    assert not looks_masked("sk-real-key-123")
    assert not looks_masked("")
