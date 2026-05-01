"""[pipline_upgrade 0-6] save_documents의 atomic 동작 통합 테스트.

검증:
  - 정상 저장 (파일 생성 + 줄 수)
  - 기존 파일 보존 + append
  - 빈 입력 no-op
  - 저장 도중 실패 시 docs.jsonl 미손상
"""
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from govlexops.core import storage
from govlexops.core.storage import save_documents, load_documents
from govlexops.schemas.legal_document import LegalDocument, make_content_hash


def _make_doc(title: str, jurisdiction: str = "KR") -> LegalDocument:
    return LegalDocument(
        source_id=f"test_{title}",
        jurisdiction=jurisdiction,
        source_type="law",
        language="ko" if jurisdiction == "KR" else "en",
        title=title,
        issued_date=date(2024, 1, 1),
        source_url=f"https://example.com/{title}",
        content_hash=make_content_hash(f"{title}_2024-01-01"),
        metadata={},
    )


@pytest.fixture
def isolated_docs_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """매 테스트마다 격리된 docs.jsonl 경로로 갈아끼운다."""
    target = tmp_path / "docs.jsonl"
    monkeypatch.setattr(storage, "DOCS_PATH", target)
    return target


def test_save_documents_creates_file(isolated_docs_path: Path) -> None:
    docs = [_make_doc("법령A"), _make_doc("법령B")]
    saved = save_documents(docs)

    assert saved == 2
    assert isolated_docs_path.exists()
    loaded = load_documents()
    assert len(loaded) == 2
    titles = {d["title"] for d in loaded}
    assert titles == {"법령A", "법령B"}


def test_save_documents_appends_to_existing(isolated_docs_path: Path) -> None:
    save_documents([_make_doc("법령A")])
    save_documents([_make_doc("법령B"), _make_doc("법령C")])

    loaded = load_documents()
    assert len(loaded) == 3
    titles = [d["title"] for d in loaded]
    # append 순서 보존
    assert titles == ["법령A", "법령B", "법령C"]


def test_save_documents_empty_is_noop(isolated_docs_path: Path) -> None:
    save_documents([_make_doc("법령A")])
    mtime_before = isolated_docs_path.stat().st_mtime_ns

    saved = save_documents([])

    assert saved == 0
    # 빈 입력은 파일을 건드리지 않아야 한다.
    assert isolated_docs_path.stat().st_mtime_ns == mtime_before


def test_save_documents_failure_preserves_existing(isolated_docs_path: Path) -> None:
    """저장 도중 실패해도 기존 docs.jsonl은 손상되지 않아야 한다."""
    save_documents([_make_doc("기존문서")])
    original = isolated_docs_path.read_text(encoding="utf-8")

    # atomic rename을 강제로 실패시킨다.
    with patch("govlexops.core.atomic.os.replace", side_effect=OSError("simulated")):
        with pytest.raises(OSError):
            save_documents([_make_doc("새문서")])

    # 기존 docs.jsonl이 그대로 보존되어야 한다.
    assert isolated_docs_path.read_text(encoding="utf-8") == original
    loaded = load_documents()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "기존문서"


def test_no_staging_files_remain(isolated_docs_path: Path, tmp_path: Path) -> None:
    """save_documents 성공 후 staging 파일이 남으면 안 된다."""
    save_documents([_make_doc("문서A"), _make_doc("문서B")])

    leftovers = list(tmp_path.glob("docs.jsonl.staging.*"))
    assert leftovers == [], f"staging 잔존: {leftovers}"
