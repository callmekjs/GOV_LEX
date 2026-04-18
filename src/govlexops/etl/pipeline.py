from govlexops.core.run_context import create_run_context
from govlexops.core.logging import log_event
  
def run():
      run_dir = create_run_context()
      log_event(run_dir, "pipeline_started")
      print(f"✓ Run started at: {run_dir}")
      
      # TODO Day 3~: 실제 수집 로직
      log_event(run_dir, "pipeline_finished", status="ok")
      print(f"✓ Run finished. Check: {run_dir}/events.jsonl")
  
if __name__ == "__main__":
      run()