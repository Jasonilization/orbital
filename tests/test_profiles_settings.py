"""Education profiles and settings persistence tests."""
import pytest

from orbital.data import load_elements
from orbital.profiles import (
    EDUCATION_LEVELS, TILE_PRESETS, level_profile, tile_preset_fields,
    FIELDS, SECTION_FIELDS, COMPARE_FIELDS,
)
from orbital.settings import Settings


@pytest.fixture(scope="module")
def elements():
    return load_elements()


def test_levels_defined():
    assert list(EDUCATION_LEVELS) == ["general", "igcse", "alevel", "advanced"]


def test_every_profile_field_is_registered():
    for level, profile in EDUCATION_LEVELS.items():
        for section, fields in profile["fields"].items():
            assert section in SECTION_FIELDS or section == "advanced"
            for f in fields:
                assert f in FIELDS, (level, f)


def test_igcse_hides_university_level_defaults():
    p = EDUCATION_LEVELS["igcse"]
    chem = p["fields"]["chemistry"]
    # no ionisation energy, no electronegativity, no atomic radius by default
    assert "ionization" not in chem
    assert "electronegativity" not in chem
    assert "radius" not in chem
    # shells (2,8,1 style) and common oxidation states are there
    assert "shells" in chem
    assert "oxidation_states" in chem
    assert p.get("common_ox_states_only") is True
    # no history section by default
    assert "history" not in p["sections"]


def test_alevel_and_advanced_expose_more():
    assert "electronegativity" in EDUCATION_LEVELS["alevel"]["fields"]["chemistry"]
    adv = EDUCATION_LEVELS["advanced"]["fields"]["chemistry"]
    assert "ionization" in adv
    assert "advanced" in EDUCATION_LEVELS["advanced"]["sections"]


def test_tile_presets():
    assert tile_preset_fields("compact") == ["number", "symbol"]
    assert tile_preset_fields("standard") == ["number", "symbol", "mass"]
    assert "name" in tile_preset_fields("school")
    with pytest.raises(ValueError):
        tile_preset_fields("jumbo")


def test_compare_fields_all_registered():
    for f in COMPARE_FIELDS:
        assert f in FIELDS


# ---------------------------------------------------------------------------
# Settings (QSettings, scoped to a scratch location)


@pytest.fixture()
def settings(tmp_path):
    return Settings(ini_path=str(tmp_path / "settings.ini"))


def test_settings_defaults_roundtrip(tmp_path):
    s = Settings(ini_path=str(tmp_path / 'a.ini'))
    assert s.get("theme") == "system"
    assert s.get("tile_scale") == 1.0
    assert s.get("show_legend") is True


def test_settings_persist_across_instances(tmp_path):
    s1 = Settings(ini_path=str(tmp_path / 'b.ini'))
    s1.set("theme", "dark")
    s1.set("education_level", "igcse")
    s1.set("tile_scale", 1.25)
    s1.set("show_legend", False)
    s2 = Settings(ini_path=str(tmp_path / 'b.ini'))
    assert s2.get("theme") == "dark"
    assert s2.get("education_level") == "igcse"
    assert s2.get("tile_scale") == 1.25
    assert s2.get("show_legend") is False
    s2.reset()
    s3 = Settings(ini_path=str(tmp_path / 'b.ini'))
    assert s3.get("theme") == "system"


def test_tile_fields_custom_config(tmp_path):
    s = Settings(ini_path=str(tmp_path / 'c.ini'))
    assert s.tile_fields() == ["number", "symbol", "mass"]  # standard preset
    s.set("education_level", "igcse")
    s.set("tile_preset", "school")
    assert "name" in s.tile_fields()
    s.set("tile_fields", ["symbol", "period"])
    assert s.tile_fields() == ["symbol", "period"]
    # invalid fields get dropped
    s.set("tile_fields", ["symbol", "bogus"])
    assert s.tile_fields() == ["symbol"]


def test_layout_fallback(tmp_path):
    s = Settings(ini_path=str(tmp_path / 'd.ini'))
    s.set("layout", "spiral")
    assert s.layout_id() == "standard"
    s.set("layout", "extended")
    assert s.layout_id() == "extended"
    s.set("remember_layout", False)
    assert s.layout_id() == "standard"  # ignores stored layout
