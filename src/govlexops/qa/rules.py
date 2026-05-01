"""
QA Rule Engine.
문서가 저장되기 전에 통과해야 하는 품질 검사 룰.
"""

from dataclasses import dataclass
from datetime import date, datetime
from govlexops.schemas.legal_document import LegalDocument
from govlexops.core.seen_store import is_seen, mark_seen_many

# [pipline_upgrade 0-4] R07이 수용하는 발행 연도 하한.
# 1948 = 대한민국 정부 수립 / 미국 의회는 1789년부터지만 우리 데이터 범위는 현대 법령·법안에 한정됨.
# 1948 미만은 sentinel(date(1900,1,1)) 검출용 및 명백한 파싱 오류 표시.
_MIN_VALID_YEAR = 1948


@dataclass
class QualityFailure:
    """품질 검사 실패 1건의 기록."""

    failure_id: str
    rule_id: str  # R01, R02, R05
    severity: str  # error, warning
    source_id: str
    timestamp: str = ""
    observed: str = ""
    suggested_fix: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "failure_id": self.failure_id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "observed": self.observed,
            "suggested_fix": self.suggested_fix,
        }


class QARuleEngine:
    """
    문서 목록에 대해 품질 룰을 실행하고, 통과/실패를 분류합니다.

    룰 목록:
      R01 - 같은 content_hash 중복 → 거부
      R02 - 필수 필드 결측 → 격리
      R07 - 비정상/파싱실패 발행일 → 격리 [0-4]
      R05 - 같은 제목인데 날짜만 다름 → 경고

    영구 중복 저장(seen_store) 정책 [pipline_upgrade 0-1]:
      - validate() 시점에는 영구 저장소에 mark_seen()을 호출하지 않는다.
      - 이번 실행 내 중복 감지는 _seen_this_run(메모리 set)으로만 수행한다.
      - 모든 룰을 통과하고 save_documents까지 성공한 문서에 한해
        commit_seen_for_passed()를 호출하여 영구 저장소에 일괄 기록한다.
      - 이렇게 해야 R02/R05에서 거부된 문서가 영구 저장소에 잘못 박혀
        다음 실행에서 영원히 거부되는 데이터 손실 버그를 방지할 수 있다.
    """

    def __init__(self, use_persistent_store: bool = True):
        self.failures: list[QualityFailure] = []
        self._use_persistent = use_persistent_store
        self._seen_this_run: set[str] = set()  # content_hash
        self._seen_titles: dict[str, str] = {}  # title → first issued_date
        self._failure_count = 0

    def _make_failure_id(self) -> str:
        self._failure_count += 1
        return f"F{self._failure_count:04d}"

    def check_r01_duplicate(self, doc: LegalDocument) -> bool:
        """
        R01: 영구 저장소 + 이번 실행 중 중복 모두 체크.

        주의: 통과해도 영구 저장소에 mark_seen 하지 않는다(0-1 fix).
              영구 기록은 save_documents 성공 후 commit_seen_for_passed가 담당.
        """

        # 1. 이번 실행 중 중복 체크
        if doc.content_hash in self._seen_this_run:
            self.failures.append(
                QualityFailure(
                    failure_id=self._make_failure_id(),
                    rule_id="R01",
                    severity="error",
                    source_id=doc.source_id,
                    observed=f"이번 실행 중 중복: {doc.content_hash[:16]}...",
                    suggested_fix="동일 실행 내 중복 문서. 거부.",
                )
            )
            return False

        # 2. 영구 저장소 중복 체크
        if self._use_persistent and is_seen(doc.content_hash):
            self.failures.append(
                QualityFailure(
                    failure_id=self._make_failure_id(),
                    rule_id="R01",
                    severity="error",
                    source_id=doc.source_id,
                    observed=f"이전 실행에서 이미 수집된 문서: {doc.content_hash[:16]}...",
                    suggested_fix="이전 실행에서 이미 적재됨. 거부.",
                )
            )
            return False

        # 3. 통과 → 이번 실행 메모리에만 추가 (영구 저장은 commit 단계로 지연)
        self._seen_this_run.add(doc.content_hash)
        return True

    def check_r02_missing_fields(self, doc: LegalDocument) -> bool:
        """R02: 필수 필드가 비어있으면 격리."""
        missing = []
        if not doc.source_id:
            missing.append("source_id")
        if not doc.title:
            missing.append("title")
        if not doc.source_url:
            missing.append("source_url")
        if not doc.content_hash:
            missing.append("content_hash")

        if missing:
            self.failures.append(
                QualityFailure(
                    failure_id=self._make_failure_id(),
                    rule_id="R02",
                    severity="error",
                    source_id=doc.source_id or "(unknown)",
                    observed=f"결측 필드: {', '.join(missing)}",
                    suggested_fix="필수 필드를 채운 후 재수집.",
                )
            )
            return False
        return True

    def check_r07_invalid_date(self, doc: LegalDocument) -> bool:
        """R07: 비정상이거나 파싱 실패한 발행일을 격리한다.

        격리 조건 (하나라도 해당하면 실패):
          1. metadata.date_parse_failed == True
             → 수집기에서 명시적으로 "날짜 파싱 실패" 표시한 문서.
          2. issued_date.year < 1948
             → 한국 정부 수립 이전 / sentinel(date(1900,1,1)) 검출.
          3. issued_date.year > today.year + 1
             → 미래 날짜는 거의 항상 잘못된 데이터.

        도입 배경 [pipline_upgrade 0-4]:
          이전엔 수집기가 파싱 실패 시 date(2000,1,1)을 박고 silently 통과시켰다.
          이제 수집기는 sentinel(date(1900,1,1)) + metadata.date_parse_failed=True를
          남기고, R07이 명시적으로 격리한다. 어떤 문서가 왜 빠졌는지 quality_report.md에
          그대로 드러난다.
        """
        today = date.today()
        year = doc.issued_date.year

        reasons: list[str] = []
        if doc.metadata.get("date_parse_failed") is True:
            raw = doc.metadata.get("raw_issued_date", "")
            reasons.append(
                f"수집기 측 발행일 파싱 실패 (raw='{raw}')"
                if raw
                else "수집기 측 발행일 파싱 실패"
            )
        if year < _MIN_VALID_YEAR:
            reasons.append(f"발행 연도 비정상: {year} (< {_MIN_VALID_YEAR})")
        if year > today.year + 1:
            reasons.append(f"발행 연도 비정상: {year} (미래 날짜)")

        if reasons:
            self.failures.append(
                QualityFailure(
                    failure_id=self._make_failure_id(),
                    rule_id="R07",
                    severity="error",
                    source_id=doc.source_id or "(unknown)",
                    observed=" / ".join(reasons),
                    suggested_fix="원본 응답의 발행일자 필드 확인 후 재수집.",
                )
            )
            return False
        return True

    def check_r05_date_conflict(self, doc: LegalDocument) -> bool:
        """R05: 같은 제목인데 날짜만 다르면 경고."""
        title_key = doc.title.strip().lower()
        doc_date = str(doc.issued_date)

        if title_key in self._seen_titles:
            first_date = self._seen_titles[title_key]
            if first_date != doc_date:
                self.failures.append(
                    QualityFailure(
                        failure_id=self._make_failure_id(),
                        rule_id="R05",
                        severity="warning",
                        source_id=doc.source_id,
                        observed=f"제목 동일, 날짜 다름: {first_date} vs {doc_date}",
                        suggested_fix="날짜 확인 후 병합 또는 검토.",
                    )
                )
                return False
        else:
            self._seen_titles[title_key] = doc_date
        return True

    def validate(self, doc: LegalDocument) -> bool:
        """모든 룰을 순서대로 실행. R01/R02/R07은 실패 시 False, R05는 warning이라 통과시킴.

        실행 순서 [0-4 갱신]:
          R01 (중복) → R02 (필수 필드) → R07 (발행일 무결성) → R05 (제목 충돌 경고)
        """
        if not self.check_r01_duplicate(doc):
            return False

        if not self.check_r02_missing_fields(doc):
            return False

        if not self.check_r07_invalid_date(doc):
            return False

        self.check_r05_date_conflict(doc)
        # R05는 warning이라 통과는 시킴
        return True

    def commit_seen_for_passed(self, docs: list[LegalDocument]) -> int:
        """
        모든 룰을 통과하고 save_documents까지 성공한 문서들을
        영구 중복 저장소(seen_store)에 일괄 기록한다.

        호출 시점:
          파이프라인에서 save_documents(passed_docs)가 성공한 직후.

        반환:
          실제로 영구 저장소에 새로 기록한 건수 (이미 있던 해시는 제외).

        주의:
          - use_persistent_store=False 이면 아무 일도 하지 않고 0을 반환한다.
          - [pipline_upgrade 0-6] mark_seen_many로 한 번의 atomic write 사용.
            N건마다 N번의 staging+rename이 일어나던 비효율을 1번으로 압축.
          - is_seen 체크는 mark_seen_many 내부에서도 한 번 더 일어난다(이중 안전).
        """
        if not self._use_persistent or not docs:
            return 0

        records: list[dict] = []
        for doc in docs:
            if not doc.content_hash:
                continue
            if is_seen(doc.content_hash):
                continue
            records.append(
                {
                    "content_hash": doc.content_hash,
                    "source_id": doc.source_id,
                    "jurisdiction": doc.jurisdiction,
                }
            )

        if not records:
            return 0
        return mark_seen_many(records)

    def get_failures(self) -> list[dict]:
        return [f.to_dict() for f in self.failures]

    def get_summary(self) -> dict:
        """룰별 실패 건수 요약."""
        summary = {"R01": 0, "R02": 0, "R07": 0, "R05": 0}
        for f in self.failures:
            if f.rule_id in summary:
                summary[f.rule_id] += 1
        return summary
