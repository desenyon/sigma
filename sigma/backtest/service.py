import asyncio
import json
import os
import shlex
import subprocess
from typing import AsyncIterator, Dict, Any, Optional
import shutil

class BacktestService:
    def __init__(self, data_dir: str = "~/.sigma/lean_data"):
        self.data_dir = os.path.expanduser(data_dir)
        self.lean_cli = shutil.which("lean") or "lean"
        
    async def run_lean(self, algorithm_file: str, project_dir: str) -> AsyncIterator[Dict[str, Any]]:
        """Run LEAN backtest and stream results."""
        
        # Validate project structure
        # lean backtest "Project Name"
        
        # We assume the project is already "init-ed" or valid for LEAN.
        # But for ad-hoc strategies, we might need a temp project.
        
        project_name = os.path.basename(project_dir)
        parent_dir = os.path.dirname(project_dir)
        
        cmd = [
            self.lean_cli, "backtest", project_name,
            "--output", "backtest-result",
            "--verbose"
        ]
        
        # LEAN runs in CWD usually or expects config.
        # We should run execution in the parent dir of the project so "lean backtest Project" works.
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=parent_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Stream output
        yield {"type": "status", "message": "Starting LEAN engine..."}
        
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                if not line_str: continue
                
                # Parse typical LEAN logs if possible
                if "Error" in line_str:
                     yield {"type": "error", "message": line_str}
                else:
                     yield {"type": "log", "message": line_str}
                 
                # Trying to detect progress or stats in logs
                # LEAN logs: "STATISTICS:: ..."
            
        await process.wait()
        
        if process.returncode != 0:
            err_msg = "Unknown error"
            if process.stderr:
                stderr_data = await process.stderr.read()
                err_msg = stderr_data.decode()
            yield {"type": "error", "message": f"LEAN failed: {err_msg}"}
            return

        # Parse results
        json_file = os.path.join(project_dir, "backtest-result", f"{project_name}.json") # Filename varies usually? 
        # Actually lean backtest creates a file in the output dir with a name.
        # We need to find the latest json in that dir.
        
        result_dir = os.path.join(project_dir, "backtest-result")
        if os.path.exists(result_dir):
            files = [f for f in os.listdir(result_dir) if f.endswith(".json")]
            if files:
                # Get newest
                latest = max([os.path.join(result_dir, f) for f in files], key=os.path.getctime)
                try:
                    with open(latest, 'r') as f:
                        data = json.load(f)
                    yield {"type": "result", "data": data}
                except Exception as e:
                    yield {"type": "error", "message": f"Failed to parse results: {e}"}
            else:
                 yield {"type": "error", "message": "No result JSON found."}
        else:
             yield {"type": "error", "message": "No result directory found."}

    async def create_project(self, name: str, code: str) -> str:
        """Create a LEAN project with the given code."""
        # Typically ~/.sigma/lean_projects/Name
        projects_dir = os.path.expanduser("~/.sigma/lean_projects")
        os.makedirs(projects_dir, exist_ok=True)
        
        project_path = os.path.join(projects_dir, name)
        os.makedirs(project_path, exist_ok=True)
        
        # content
        # main.py
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write(code)
            
        # config.json needed? 
        # lean init usually creates `lean.json` in root.
        # We assume the user has a workspace or we set one up in ~/.sigma/lean_data?
        # The service should ensure a workspace exists.
        
        return project_path

SERVICE = BacktestService()
