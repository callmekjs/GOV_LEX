"""QA Rule Engine 테스트."""
import pytest
from datetime import date
from govlexops.schemas.legal_document import LegalDocument, make_content_hash
from govlexops.qa.rules import QARuleEngine


def _make_doc(source_id="test_doc", title="Test", content="hello", issued_date=date(2024, 1, 1)):
    """테스트용 문서를 간편하게 만드는 헬퍼."""
    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title=title,
        issued_date=issued_date,
        source_url="https://example.com",
        content_hash=make_content_hash(content),
    )


def test_r01_allows_unique():
    """R01: 서로 다른 문서는 통과."""
    engine = QARuleEngine()
    doc1 = _make_doc(source_id="doc1", content="본문A")
    doc2 = _make_doc(source_id="doc2", content="본문B")
    assert engine.validate(doc1) is True
    assert engine.validate(doc2) is True
    assert engine.get_summary()["R01"] == 0


def test_r01_blocks_duplicate():
    """R01: 같은 content_hash면 두 번째를 거부."""
    engine = QARuleEngine()
    doc1 = _make_doc(source_id="doc1", content="동일 본문")
    doc2 = _make_doc(source_id="doc2", content="동일 본문")  # 같은 내용
    assert engine.validate(doc1) is True
    assert engine.validate(doc2) is False
    assert engine.get_summary()["R01"] == 1


def test_r05_warns_date_conflict():
    """R05: 같은 제목 + 다른 날짜면 경고."""
    engine = QARuleEngine()
    doc1 = _make_doc(title="AI법", content="내용1", issued_date=date(2024, 3, 1))
    doc2 = _make_doc(title="AI법", content="내용2", issued_date=date(2024, 6, 1))
    engine.validate(doc1)
    engine.validate(doc2)
    assert engine.get_summary()["R05"] == 1


def test_summary_counts():
    """전체 요약이 정확한지."""
    engine = QARuleEngine()
    # 정상 1개
    engine.validate(_make_doc(source_id="ok", content="유니크"))
    # 중복 1개
    engine.validate(_make_doc(source_id="dup", content="유니크"))
    # [pipline_upgrade 0-4] R07 키 추가됨
    assert engine.get_summary() == {"R01": 1, "R02": 0, "R07": 0, "R05": 0}


def test_failures_list():
    """실패 목록이 dict로 나오는지."""
    engine = QARuleEngine()
    engine.validate(_make_doc(source_id="a", content="same"))
    engine.validate(_make_doc(source_id="b", content="same"))
    failures = engine.get_failures()
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "R01"
    assert failures[0]["source_id"] == "b"

def test_hash_ignores_whitespace_differences():
    """공백/줄바꿈이 달라도 같은 해시가 나와야 한다."""
    a = "안녕  세상"
    b = "안녕\n세상"
    c = " 안녕 세상 "
    assert make_content_hash(a) == make_content_hash(b) == make_content_hash(c)
def test_hash_ignores_unicode_form_differences():
    """같은 한글인데 조합형/완성형 차이여도 같은 해시가 나와야 한다."""
    composed = "가"                       # NFC 완성형
    decomposed = "\u1100\u1161"           # NFD 자모 분리 (ㄱ + ㅏ)
    assert make_content_hash(composed) == make_content_hash(decomposed)
def test_hash_differs_for_different_content():
    """내용 자체가 다르면 해시도 달라야 한다."""
    assert make_content_hash("서울") != make_content_hash("부산")

def test_r02_blocks_empty_source_id():
    """R02: source_id가 비어 있으면 실패."""
    doc = LegalDocument(
        source_id="",                 # 결측
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="제목 있음",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash=make_content_hash("내용"),
    )
    engine = QARuleEngine()
    assert engine.validate(doc) is False
    assert engine.get_summary()["R02"] == 1


def test_r02_blocks_empty_content_hash():
    """R02: content_hash가 비어 있으면 실패."""
    doc = LegalDocument(
        source_id="doc1",
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="제목 있음",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash="",              # 결측
    )
    engine = QARuleEngine()
    assert engine.validate(doc) is False
    assert engine.get_summary()["R02"] == 1

def test_r02_failure_does_not_mark_seen(tmp_path, monkeypatch):
    """
    [pipline_upgrade 0-1 회귀 방지]
    R01은 통과해도 R02에서 거부된 문서는 영구 저장소(seen_store)에
    절대 기록되어선 안 된다. (이게 박혀버리면 다음 실행에서 영원히 거부됨)
    """
    from govlexops.core import seen_store

    # tmp_path로 격리: 진짜 seen_store 파일을 건드리지 않게
    monkeypatch.chdir(tmp_path)
    seen_store._seen = None  # 모듈 캐시 리셋 (cwd 기준 다시 로드)

    # R02 실패 문서: source_id 비어 있음. content_hash는 정상.
    will_fail_hash = make_content_hash("R02에 걸려야 할 본문")
    doc = LegalDocument(
        source_id="",  # ← R02 결측 트리거
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="유효한 제목",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash=will_fail_hash,
    )

    engine = QARuleEngine(use_persistent_store=True)
    result = engine.validate(doc)

    # 1. R02에서 거부됐는지
    assert result is False
    assert engine.get_summary()["R02"] == 1

    # 2. 핵심: 영구 저장소에 그 해시가 절대 들어가면 안 된다
    seen_store._seen = None  # 캐시 리셋해서 디스크에서 다시 읽도록
    assert seen_store.is_seen(will_fail_hash) is False, (
        "R02에서 거부된 문서의 content_hash가 영구 저장소에 잘못 기록됨. "
        "0-1 버그가 회귀했다."
    )


def test_commit_seen_for_passed_only_persists_after_save(tmp_path, monkeypatch):
    """
    [pipline_upgrade 0-1 회귀 방지]
    validate()만으로는 영구 저장소에 기록되지 않고,
    commit_seen_for_passed()를 호출해야만 영구 저장된다.
    """
    from govlexops.core import seen_store

    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = _make_doc(source_id="persist_me", content="저장될 본문")
    engine = QARuleEngine(use_persistent_store=True)

    # 1. validate만 호출 → 통과는 하지만 영구 저장은 X
    assert engine.validate(doc) is True
    seen_store._seen = None  # 디스크에서 다시 읽도록 캐시 리셋
    assert seen_store.is_seen(doc.content_hash) is False, (
        "validate만으로 영구 저장에 기록됨. "
        "save 성공 전에 mark_seen이 호출되는 0-1 버그 회귀."
    )

    # 2. commit 호출 → 영구 저장됨
    committed = engine.commit_seen_for_passed([doc])
    assert committed == 1

    seen_store._seen = None
    assert seen_store.is_seen(doc.content_hash) is True


def test_commit_seen_for_passed_idempotent(tmp_path, monkeypatch):
    """
    [pipline_upgrade 0-1 부속]
    같은 문서를 두 번 commit해도 영구 저장소에 두 번 기록되지 않고,
    두 번째 호출의 새 기록 카운트는 0이다.
    """
    from govlexops.core import seen_store

    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = _make_doc(source_id="once", content="한번만 저장")
    engine = QARuleEngine(use_persistent_store=True)
    engine.validate(doc)

    first = engine.commit_seen_for_passed([doc])
    second = engine.commit_seen_for_passed([doc])

    assert first == 1
    assert second == 0  # 이미 있는 해시는 새로 기록되지 않아야 함


def test_r07_blocks_year_below_1948(tmp_path, monkeypatch):
    """[pipline_upgrade 0-4] 1948년 미만 발행일은 격리.

    수집기가 폴백으로 박는 sentinel(date(1900,1,1))이 자동으로 잡힌다.
    """
    from govlexops.core import seen_store
    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = LegalDocument(
        source_id="ancient_doc",
        jurisdiction="KR",
        source_type="law",
        language="ko",
        title="고대 법령",
        issued_date=date(1900, 1, 1),  # ← sentinel
        source_url="https://example.com",
        content_hash=make_content_hash("ancient"),
    )

    engine = QARuleEngine(use_persistent_store=False)
    assert engine.validate(doc) is False
    summary = engine.get_summary()
    assert summary["R07"] == 1
    # R07 실패 시 R05는 실행되지 않는다 (validate가 False 반환 후 종료)
    assert summary["R05"] == 0


def test_r07_blocks_future_date(tmp_path, monkeypatch):
    """[pipline_upgrade 0-4] today+1 초과 미래 날짜는 격리."""
    from govlexops.core import seen_store
    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = LegalDocument(
        source_id="future_doc",
        jurisdiction="US",
        source_type="bill",
        language="en",
        title="Future Bill",
        issued_date=date(9999, 1, 1),
        source_url="https://example.com",
        content_hash=make_content_hash("future"),
    )

    engine = QARuleEngine(use_persistent_store=False)
    assert engine.validate(doc) is False
    assert engine.get_summary()["R07"] == 1


def test_r07_blocks_when_metadata_flag_set(tmp_path, monkeypatch):
    """[pipline_upgrade 0-4] metadata.date_parse_failed=True면
    issued_date 자체가 정상 범위라도 격리한다.

    수집기가 raw 응답에서 발행일을 파싱하지 못한 경우의 명시적 표지.
    """
    from govlexops.core import seen_store
    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = LegalDocument(
        source_id="parse_failed_doc",
        jurisdiction="KR",
        source_type="bill",
        language="ko",
        title="파싱 실패 의안",
        issued_date=date(2024, 5, 15),  # 자체로는 정상이지만…
        source_url="https://example.com",
        content_hash=make_content_hash("parse fail"),
        metadata={
            "date_parse_failed": True,
            "raw_issued_date": "이상한 날짜 형식",
        },
    )

    engine = QARuleEngine(use_persistent_store=False)
    assert engine.validate(doc) is False
    summary = engine.get_summary()
    assert summary["R07"] == 1
    # 격리 사유에 raw 값이 포함되어야 한다 (운영 추적성)
    failures = engine.get_failures()
    r07_fail = next(f for f in failures if f["rule_id"] == "R07")
    assert "이상한 날짜 형식" in r07_fail["observed"]


def test_r07_passes_normal_date(tmp_path, monkeypatch):
    """[pipline_upgrade 0-4] 1948 ~ today+1 범위 + 파싱 표지 없음 → 통과."""
    from govlexops.core import seen_store
    monkeypatch.chdir(tmp_path)
    seen_store._seen = None

    doc = _make_doc(content="ok normal", issued_date=date(2024, 5, 15))
    engine = QARuleEngine(use_persistent_store=False)

    assert engine.validate(doc) is True
    assert engine.get_summary()["R07"] == 0


def test_global_failure_log_is_cumulative(tmp_path, monkeypatch):
    """
    report가 run별 기록 외에 data_index/quality/failures.jsonl 에도
    누적 append 되는지 확인.
    """
    import json
    from govlexops.qa.report import generate_quality_report
    from govlexops.qa.rules import QARuleEngine

    # tmp_path 로 cwd 이동 → data_index가 진짜 쓰이는지 격리된 곳에서 검증
    monkeypatch.chdir(tmp_path)

    # run1
    run1 = tmp_path / "runs" / "run_test_1"
    run1.mkdir(parents=True)
    engine1 = QARuleEngine()
    engine1.validate(_make_doc(source_id="a", content="same"))
    engine1.validate(_make_doc(source_id="b", content="same"))  # R01
    generate_quality_report(run1, engine1, total_input=2, total_passed=1)

    # run2
    run2 = tmp_path / "runs" / "run_test_2"
    run2.mkdir(parents=True)
    engine2 = QARuleEngine()
    engine2.validate(_make_doc(source_id="c", content="same2"))
    engine2.validate(_make_doc(source_id="d", content="same2"))  # R01
    generate_quality_report(run2, engine2, total_input=2, total_passed=1)

    global_log = tmp_path / "data_index" / "quality" / "failures.jsonl"
    lines = global_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # 두 번 실행분이 누적됨

    run_ids = {json.loads(l)["run_id"] for l in lines}
    assert run_ids == {"run_test_1", "run_test_2"}