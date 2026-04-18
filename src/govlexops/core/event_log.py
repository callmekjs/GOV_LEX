import json
from datetime import datetime
from pathlib import Path
  
def log_event(run_dir: Path, event_type: str, **data) -> None:
      """events.jsonl에 이벤트 한 줄 추가"""
      record = {
          "timestamp": datetime.now().isoformat(),
          "event_type": event_type,
          **data,
      }
      with open(run_dir / "events.jsonl", "a", encoding="utf-8") as f:
          f.write(json.dumps(record, ensure_ascii=False) + "\n")