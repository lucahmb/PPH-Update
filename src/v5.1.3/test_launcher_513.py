import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "start_pph_hub.sh"
text = LAUNCHER.read_text()
subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)

match = re.search(r"<<'PYPROC'\n(.*?)\nPYPROC", text, re.S)
assert match, "hub_running() PYPROC heredoc not found"
checker_src = match.group(1)
assert "proc_cwd" in checker_src, "fix must resolve relative argv paths via the inspected process's own cwd"

work = Path("/tmp/pph513_test") / str(os.getpid())
target_dir = work / "app" / "pph_hub"
other_dir = work / "elsewhere"
target_dir.mkdir(parents=True, exist_ok=True)
other_dir.mkdir(parents=True, exist_ok=True)
target = target_dir / "pph3_app.py"
target.write_text("# dummy\n")
checker_script = work / "checker.py"
checker_script.write_text(checker_src)

# A process running from a DIFFERENT directory that just happens to carry the same
# relative argv string the real launcher uses. Pre-fix, this used to be mistaken for
# an already-running hub because the resolve() ran against the checker's own cwd
# instead of this process's cwd.
decoy = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(5)", "pph_hub/pph3_app.py"],
    cwd=str(other_dir),
)
try:
    time.sleep(0.3)
    result = subprocess.run(
        [sys.executable, str(checker_script), str(target), str(os.getuid())],
        cwd=str(target_dir.parent),
    )
    assert result.returncode == 1, (
        f"false positive: unrelated process with a relative argv path was mistaken "
        f"for a running hub (exit code {result.returncode}, expected 1/not-running)"
    )
finally:
    decoy.kill()
    decoy.wait()

# A process that genuinely runs the target with an absolute path must still be detected.
real = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)", str(target)])
try:
    time.sleep(0.3)
    result = subprocess.run(
        [sys.executable, str(checker_script), str(target), str(os.getuid())],
        cwd=str(target_dir.parent),
    )
    assert result.returncode == 0, "a genuinely running hub process must still be detected"
finally:
    real.kill()
    real.wait()

print("PPH 5.1.3 launcher false-positive fix tests OK")
