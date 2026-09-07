"""Owner-directed translation revision requests."""

from translation_v2.revision_manifest import TranslationRevisionManifest


def test_revision_manifest_resolves_locale_specific_entry(tmp_path):
    manifest_path = tmp_path / "translation_revision.yaml"
    manifest_path.write_text(
        "posts:\n"
        "  post-one:\n"
        "    pt-br:\n"
        "      reason: stale ai studio translation\n"
        "      notes: revisit tone\n",
        encoding="utf-8",
    )

    manifest = TranslationRevisionManifest(path=manifest_path)
    entry = manifest.get(slug="post-one", target_locale="pt-br")

    assert entry is not None
    assert entry.payload["reason"] == "stale ai studio translation"
    assert entry.payload["notes"] == "revisit tone"
    assert entry.marker


def test_revision_manifest_accepts_legacy_artifacts_root(tmp_path):
    manifest_path = tmp_path / "translation_revision.yaml"
    manifest_path.write_text(
        "artifacts:\n"
        "  post-one:\n"
        "    pt-br:\n"
        "      reason: legacy key still supported\n",
        encoding="utf-8",
    )

    manifest = TranslationRevisionManifest(path=manifest_path)
    entry = manifest.get(slug="post-one", target_locale="pt-br")

    assert entry is not None
    assert entry.payload["reason"] == "legacy key still supported"
