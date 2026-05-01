from datetime import datetime
from pathlib import Path
import uuid


def create_run_context(base_dir: str = "runs") -> Path:
    """새로운 run_id 폴더를 만들고 경로를 돌려준다"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    run_dir = Path(base_dir) / f"run_{ts}_{short}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
