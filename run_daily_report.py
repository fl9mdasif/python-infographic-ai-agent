"""
Orchestrator: Daily Report
Layer 2: Decision Making
"""
import subprocess
import sys

SCRIPTS = [
    "execution/scout_trends.py",
    "execution/generate_content.py",
    "execution/generate_visuals.py",
    "execution/build_dashboard.py",
]

def run_step(script_path):
    print(f"\n--- Running: {script_path} ---")
    try:
        # Check platform for 'python' vs 'python3' or 'py'
        # Assuming 'py' or 'python' works in this environment
        cmd = [sys.executable, script_path]
        result = subprocess.run(cmd, check=True)
        if result.returncode != 0:
            print(f"Error executing {script_path}")
            return False
        return True
    except Exception as e:
        print(f"Failed to run {script_path}: {e}")
        return False

def main():
    print("Starting Daily Report Orchestrator...")
    for script in SCRIPTS:
        success = run_step(script)
        if not success:
            print("Pipeline stopped due to error.")
            sys.exit(1)
    
    print("\n✅ Daily Report Complete!")
    print("Open .tmp/index.html to view.")

if __name__ == "__main__":
    main()
