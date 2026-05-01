from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MASTERPLAN = ROOT / "masterplan.md"
README = ROOT / "Readme.md"
WORKLOG = ROOT / "내가한거.md"

START_MARKER = "<!-- AUTO_PHASE_SYNC:START -->"
END_MARKER = "<!-- AUTO_PHASE_SYNC:END -->"


@dataclass(frozen=True)
class PhaseEntry:
    phase: str
    summary: str


DETAIL_PATTERN = re.compile(r"^\s*-\s+\*\*(\d+-\d+)\*\*:\s*(.+?)\s*$")
PHASE_ONLY_PATTERN = re.compile(r"(\d+-\d+)")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def extract_phase_entries(masterplan_text: str) -> list[PhaseEntry]:
    entries: list[PhaseEntry] = []
    index_by_phase: dict[str, int] = {}

    for line in masterplan_text.splitlines():
        detail = DETAIL_PATTERN.match(line)
        if detail:
            phase = detail.group(1)
            summary = detail.group(2).strip().strip('"')
            if phase not in index_by_phase:
                entries.append(PhaseEntry(phase=phase, summary=summary))
                index_by_phase[phase] = len(entries) - 1
            else:
                idx = index_by_phase[phase]
                entries[idx] = PhaseEntry(phase=phase, summary=summary)
            continue

        if "[x]" in line.lower():
            match = PHASE_ONLY_PATTERN.search(line)
            if match:
                phase = match.group(1)
                if phase not in index_by_phase:
                    entries.append(PhaseEntry(phase=phase, summary="완료 체크"))
                    index_by_phase[phase] = len(entries) - 1

    return entries


def _next_phase(current: str) -> str:
    major_s, minor_s = current.split("-")
    major = int(major_s)
    minor = int(minor_s)
    if minor >= 6:
        return f"{major + 1}-1"
    return f"{major}-{minor + 1}"


def build_sync_block(entries: list[PhaseEntry]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not entries:
        body = [
            "### 자동 동기화 상태",
            f"- 동기화 시각: {now}",
            "- 완료 페이즈를 찾지 못했습니다. `masterplan.md`의 완료 항목을 확인하세요.",
        ]
    else:
        latest = entries[-1]
        recent = list(reversed(entries[-10:]))
        body = [
            "### 자동 동기화 상태",
            f"- 마지막 완료 페이즈: **{latest.phase}**",
            f"- 다음 권장 페이즈: **{_next_phase(latest.phase)}**",
            f"- 동기화 시각: {now}",
            "",
            "#### 최근 완료 페이즈 (최신순)",
            "| Phase | 요약 |",
            "|---|---|",
        ]
        for entry in recent:
            body.append(f"| {entry.phase} | {entry.summary} |")

    return "\n".join([START_MARKER, *body, END_MARKER])


def replace_or_append_block(text: str, block: str) -> str:
    if START_MARKER in text and END_MARKER in text:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        return pattern.sub(block, text, count=1)

    stripped = text.rstrip()
    return f"{stripped}\n\n---\n\n{block}\n"


def main() -> None:
    masterplan_text = _read(MASTERPLAN)
    entries = extract_phase_entries(masterplan_text)
    block = build_sync_block(entries)

    updated_masterplan = replace_or_append_block(masterplan_text, block)
    updated_readme = replace_or_append_block(_read(README), block)
    updated_worklog = replace_or_append_block(_read(WORKLOG), block)

    _write(MASTERPLAN, updated_masterplan)
    _write(README, updated_readme)
    _write(WORKLOG, updated_worklog)

    latest = entries[-1].phase if entries else "N/A"
    print(f"[sync_phase_docs] synced. latest_phase={latest}")


if __name__ == "__main__":
    main()
