from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _synapse_files():
    return sorted((REPO_ROOT / "synapse").rglob("*.py"))


def test_synapse_has_no_raw_not_implemented_error_raises() -> None:
    offending = []
    for path in _synapse_files():
        text = path.read_text(encoding="utf-8")
        if "raise NotImplementedError(" in text:
            offending.append(path.relative_to(REPO_ROOT).as_posix())

    assert offending == []


def test_runtime_cache_placeholders_raise_runtime_error() -> None:
    expected_runtime_guards = {
        "synapse/storage/databases/main/end_to_end_keys.py": "raise RuntimeError(",
        "synapse/storage/databases/main/pusher.py": "raise RuntimeError(",
        "synapse/storage/databases/main/presence.py": "raise RuntimeError(",
        "synapse/storage/databases/main/keys.py": "raise RuntimeError(",
        "synapse/storage/databases/main/signatures.py": "raise RuntimeError(",
    }

    for rel_path, expected in expected_runtime_guards.items():
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert expected in text
