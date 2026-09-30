from app.core.dedupe import content_hash, probable_duplicate


def test_content_hash_is_stable():
    assert content_hash("Acme", "Software Engineer", "Berlin") == content_hash("ACME", "Software Engineer", "Berlin")


def test_probable_duplicate():
    assert probable_duplicate("Acme GmbH", "Software Engineer", "Berlin", "Acme GmbH", "Software Engineer", "Berlin, Germany")
