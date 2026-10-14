import pytest
from downloader import safe_filename

@pytest.mark.parametrize("raw, expected", [
    ("Normal Song", "Normal Song"),
    ("AC/DC - Thunder", "ACDC - Thunder"),
    ('What? "Is": This*', "What Is This"),
    ("  spaces  ", "spaces"),
    ("", ""),
    ("Хорошая песня", "Хорошая песня"),
])
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected