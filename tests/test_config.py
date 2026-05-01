from pathlib import Path

import pytest

from govlexops.core.config import load_pipeline_config


def test_load_pipeline_config_from_yaml(tmp_path: Path):
    cfg_path = tmp_path / "pipeline.yaml"
    cfg_path.write_text(
        """
kr_law:
  queries: [인공지능, 데이터]
  max_per_query: 10
  issued_since_year_offset: -2
kr_decree:
  queries: [시행령, 대통령령]
  max_per_query: 12
  issued_since_year_offset: -2
  target: ordin
us_congress:
  congress: 119
  max_count: 30
  min_intro_year_offset: -1
kr_assembly:
  assemblies: [제22대]
  test_limit: 100
  page_size: 50
  start_year_offset: -2
  end_year_offset: -1
""".strip(),
        encoding="utf-8",
    )

    cfg = load_pipeline_config(cfg_path)
    assert cfg.kr_law.max_per_query == 10
    assert cfg.kr_law.queries == ["인공지능", "데이터"]
    assert cfg.kr_decree.max_per_query == 12
    assert cfg.kr_decree.target == "ordin"
    assert cfg.us_congress.congress == 119
    assert cfg.kr_assembly.page_size == 50


def test_load_pipeline_config_raises_when_missing():
    with pytest.raises(FileNotFoundError):
        load_pipeline_config("configs/not-exists.yaml")
