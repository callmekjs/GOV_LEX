"""
QA Rule Engine.
문서가 저장되기 전에 통과해야 하는 품질 검사 룰 3개.
"""
from dataclasses import dataclass, field
from datetime import datetime
from govlexops.schemas.legal_document import LegalDocument


@dataclass
class QualityFailure:
    """품질 검사 실패 1건의 기록."""
    failure_id: str
    rule_id: str          # R01, R02, R05
    severity: str         # error, warning
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
      R05 - 같은 제목인데 날짜만 다름 → 경고
    """

    def __init__(self):
        self.failures: list[QualityFailure] = []
        self._seen_hashes: set[str] = set()
        self._seen_titles: dict[str, str] = {}  # title → first issued_date
        self._failure_count = 0

    def _make_failure_id(self) -> str:
        self._failure_count += 1
        return f"F{self._failure_count:04d}"

    def check_r01_duplicate(self, doc: LegalDocument) -> bool:
        """R01: 같은 content_hash가 이미 있으면 중복."""
        if doc.content_hash in self._seen_hashes:
            self.failures.append(QualityFailure(
                failure_id=self._make_failure_id(),
                rule_id="R01",
                severity="error",
                source_id=doc.source_id,
                observed=f"content_hash 충돌: {doc.content_hash[:16]}...",
                suggested_fix="이미 적재된 문서와 동일. 신규 문서 거부.",
            ))
            return False
        self._seen_hashes.add(doc.content_hash)
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
            self.failures.append(QualityFailure(
                failure_id=self._make_failure_id(),
                rule_id="R02",
                severity="error",
                source_id=doc.source_id or "(unknown)",
                observed=f"결측 필드: {', '.join(missing)}",
                suggested_fix="필수 필드를 채운 후 재수집.",
            ))
            return False
        return True

    def check_r05_date_conflict(self, doc: LegalDocument) -> bool:
        """R05: 같은 제목인데 날짜만 다르면 경고."""
        title_key = doc.title.strip().lower()
        doc_date = str(doc.issued_date)

        if title_key in self._seen_titles:
            first_date = self._seen_titles[title_key]
            if first_date != doc_date:
                self.failures.append(QualityFailure(
                    failure_id=self._make_failure_id(),
                    rule_id="R05",
                    severity="warning",
                    source_id=doc.source_id,
                    observed=f"제목 동일, 날짜 다름: {first_date} vs {doc_date}",
                    suggested_fix="날짜 확인 후 병합 또는 검토.",
                ))
                return False
        else:
            self._seen_titles[title_key] = doc_date
        return True

    def validate(self, doc: LegalDocument) -> bool:
        """3개 룰을 순서대로 실행. 하나라도 실패하면 False."""
        r01 = self.check_r01_duplicate(doc)
        if not r01:
            return False

        r02 = self.check_r02_missing_fields(doc)
        if not r02:
            return False

        r05 = self.check_r05_date_conflict(doc)
        # R05는 warning이라 통과는 시킴
        return True

    def get_failures(self) -> list[dict]:
        return [f.to_dict() for f in self.failures]

    def get_summary(self) -> dict:
        """룰별 실패 건수 요약."""
        summary = {"R01": 0, "R02": 0, "R05": 0}
        for f in self.failures:
            if f.rule_id in summary:
                summary[f.rule_id] += 1
        return summary