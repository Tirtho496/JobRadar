from app.core.profile import get_locations, get_profile, get_sources_config


def test_default_configuration_is_structurally_valid():
    profile = get_profile()
    locations = get_locations()
    sources = get_sources_config()

    assert profile.name
    assert profile.preferred_roles
    assert profile.skills
    assert locations.countries
    assert all(cfg.code and cfg.cities for cfg in locations.countries.values())
    assert "public_sources" in sources
