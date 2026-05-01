"""GovLex CLI service entrypoint."""

from __future__ import annotations

import typer

app = typer.Typer(help="GovLex operations CLI")


@app.command()
def run(config: str = "configs/pipeline.yaml") -> None:
    """파이프라인 실행."""
    from govlexops.etl.pipeline import run as pipeline_run

    pipeline_run(config_path=config)


@app.command()
def replay(
    run_path: str = typer.Option(..., help="runs/run_xxx 경로"),
    only_failures: bool = typer.Option(False, help="이전 실패 source_id만 재검증"),
    regenerate_report: bool = typer.Option(False, help="replay 품질리포트 재생성"),
) -> None:
    """과거 run을 재검증하고 replay_report.md를 생성."""
    from govlexops.core.replay import replay_run

    out = replay_run(
        run_path=run_path,
        only_failures=only_failures,
        regenerate_report=regenerate_report,
    )
    typer.echo(f"replay report generated: {out}")


if __name__ == "__main__":
    app()
