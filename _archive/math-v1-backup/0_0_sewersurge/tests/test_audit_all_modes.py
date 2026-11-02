import csv
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_all_modes.py"
SPEC = importlib.util.spec_from_file_location("audit_all_modes", MODULE_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _write_lookup_csv(path: Path, book_id: int, payout: float, weight: float = 1.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sim_id", "weight", "payout"])
        writer.writerow([book_id, weight, payout])


def _load_first_book(mode: str):
    candidates = [
        Path(__file__).resolve().parents[1] / "library" / "books" / f"books_{mode}.jsonl",
        Path(__file__).resolve().parents[1] / "library" / "publish_files" / f"books_{mode}.jsonl.zst",
    ]
    for path in candidates:
        if not path.exists():
            continue
        if path.suffix == ".zst":
            zstd = pytest.importorskip("zstandard", reason="zstandard is required for compressed books")
            with path.open("rb") as handle:
                stream = zstd.ZstdDecompressor().stream_reader(handle)
                with __import__("io").TextIOWrapper(stream, encoding="utf-8") as text:
                    for line in text:
                        if not line.strip():
                            continue
                        return json.loads(line)
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                return json.loads(line)
    raise AssertionError(f"No books found for mode {mode!r}")


def test_missing_sewer_feature_is_allowed_for_none_tier_books(tmp_path, monkeypatch):
    mode = "base"
    book = _load_first_book(mode)
    board_event = next(event for event in book["events"] if event["type"] == "sewerBoard")
    award_event = next(event for event in book["events"] if event["type"] == "sewerAward")
    total_event = next(event for event in reversed(book["events"]) if event["type"] == "setTotalWin")
    final_event = next(event for event in reversed(book["events"]) if event["type"] == "finalWin")

    if board_event.get("scatterTier") != "none":
        pytest.skip("selected base book is not a none-tier book")

    trimmed = {
        "id": book["id"],
        "payoutMultiplier": book["payoutMultiplier"],
        "events": [
            event for event in book["events"]
            if event["type"] not in {"sewerFeature"}
        ],
    }
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    with (books_dir / f"books_{mode}.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(trimmed) + "\n")

    lookup_dir = tmp_path / "lookup_tables"
    publish_dir = tmp_path / "publish_files"
    publish_dir.mkdir(exist_ok=True)
    _write_lookup_csv(lookup_dir / f"lookUpTable_{mode}.csv", book["id"], float(book["payoutMultiplier"]))

    monkeypatch.setattr(AUDIT, "BOOK_DIR", books_dir)
    monkeypatch.setattr(AUDIT, "COMPRESSED_BOOK_DIR", tmp_path / "books_compressed")
    monkeypatch.setattr(AUDIT, "LOOKUP_DIR", lookup_dir)
    monkeypatch.setattr(AUDIT, "PUBLISH_DIR", publish_dir)

    result = AUDIT.audit_mode(mode, 1.0, 96.5, 0.5)
    assert result["structural_failures"] == []
    assert "missing required Sewer/SDK event" not in "\n".join(result["structural_failures"])


def test_lookup_table_uses_integer_payout_units_and_feature_key(tmp_path, monkeypatch):
    mode = "bonus"
    book = _load_first_book(mode)
    feature_event = next(event for event in book["events"] if event["type"] == "sewerFeature")
    award_event = next(event for event in book["events"] if event["type"] == "sewerAward")
    assert "feature" in feature_event
    assert feature_event["feature"] in {"bonus", "deep-run"}
    assert award_event["scatterTier"] == feature_event["feature"]

    books_dir = tmp_path / "books"
    books_dir.mkdir()
    with (books_dir / f"books_{mode}.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(book) + "\n")

    lookup_dir = tmp_path / "lookup_tables"
    publish_dir = tmp_path / "publish_files"
    publish_dir.mkdir(exist_ok=True)
    payout = float(book["payoutMultiplier"])
    _write_lookup_csv(lookup_dir / f"lookUpTable_{mode}.csv", book["id"], payout)

    monkeypatch.setattr(AUDIT, "BOOK_DIR", books_dir)
    monkeypatch.setattr(AUDIT, "COMPRESSED_BOOK_DIR", tmp_path / "books_compressed")
    monkeypatch.setattr(AUDIT, "LOOKUP_DIR", lookup_dir)
    monkeypatch.setattr(AUDIT, "PUBLISH_DIR", publish_dir)

    result = AUDIT.audit_mode(mode, 100.0, 96.5, 0.5)
    assert result["lookup_table"]["errors"] == []
    assert result["structural_failures"] == []


def test_publish_files_book_and_lut_are_used_when_present(tmp_path, monkeypatch):
    zstd = pytest.importorskip("zstandard", reason="zstandard is required for compressed book fixtures")
    mode = "base"
    book = _load_first_book(mode)

    library_dir = tmp_path / "library"
    publish_dir = library_dir / "publish_files"
    publish_dir.mkdir(parents=True)
    with (publish_dir / f"books_{mode}.jsonl.zst").open("wb") as handle:
        handle.write(zstd.ZstdCompressor().compress((json.dumps(book) + "\n").encode("utf-8")))

    _write_lookup_csv(publish_dir / f"lookUpTable_{mode}_0.csv", book["id"], float(book["payoutMultiplier"]))
    (library_dir / "publish_files" / "index.json").write_text(
        json.dumps({"modes": [{"name": mode, "events": f"books_{mode}.jsonl.zst", "weights": f"lookUpTable_{mode}_0.csv"}]}, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(AUDIT, "LIBRARY_DIR", library_dir)
    monkeypatch.setattr(AUDIT, "BOOK_DIR", library_dir / "books")
    monkeypatch.setattr(AUDIT, "COMPRESSED_BOOK_DIR", library_dir / "books_compressed")
    monkeypatch.setattr(AUDIT, "LOOKUP_DIR", library_dir / "lookup_tables")
    monkeypatch.setattr(AUDIT, "PUBLISH_DIR", publish_dir)

    result = AUDIT.audit_mode(mode, 1.0, 96.5, 0.5)
    assert result["book_source"].endswith(f"books_{mode}.jsonl.zst")
    assert result["lookup_table"]["path"].endswith(f"lookUpTable_{mode}_0.csv")
    assert result["lookup_table"]["status"] == "optimized"
    assert result["lookup_table"]["errors"] == []
    assert result["structural_failures"] == []
