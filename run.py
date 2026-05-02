import os
import sys
import subprocess
from pathlib import Path

ROOT       = Path(__file__).parent
AGENTS_DIR = ROOT / "agents"
VENV_DIR   = ROOT / ".venv"
PYTHON     = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PIP        = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")

def setup():
    if not VENV_DIR.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    else:
        print("✅ Virtual environment already exists")
    
    print("📦 Upgrading pip...")
    subprocess.run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    print("📦 Installing requirements...")
    subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    
    activate_cmd = r".venv\Scripts\activate" if os.name == "nt" else "source .venv/bin/activate"
    print(f"\n✅ Setup complete!")
    print(f"\n💡 Activate virtual environment in THIS terminal with: {activate_cmd}")

def list_agents():
    if not AGENTS_DIR.exists():
        print("📁 No agents directory found")
        return
    
    agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir() and (d / "agent.py").exists()]
    
    if not agents:
        print("📁 No agents found")
    else:
        print("\n📁 Available agents:")
        for agent in sorted(agents):
            print(f"  python ./run.py {agent}")

def run(agent_name: str):
    agent_path = AGENTS_DIR / agent_name / "agent.py"
    if not agent_path.exists():
        print(f"❌ Agent '{agent_name}' not found.\n")
        list_agents()
        sys.exit(1)
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    
    print(f"\n🚀 Running agent: {agent_name}\n{'─' * 50}")
    subprocess.run([str(PYTHON), str(agent_path)], env=env)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py [setup | list | <agent_name>]\n")
        print("Commands:")
        print("  setup              - Setup virtual environment")
        print("  list               - List all available agents")
        print("  <agent_name>       - Run a specific agent")
        print("\nAfter setup, activate venv manually:")
        print("  .venv\\Scripts\\activate  # Windows")
        print("  source .venv/bin/activate  # Mac/Linux")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "setup":
        setup()
    elif cmd == "list":
        list_agents()
    else:
        run(cmd)