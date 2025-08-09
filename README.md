# Interstellar

Interstellar: AI-assisted 3D spaceship design in Houdini.

## Folders
- houdini: Houdini .hip scenes and assets
- scripts: Python/VEX snippets for procedural generation
- ai_tools: Stable Diffusion setups and generated outputs
- docs: Notes, references, prompts

## Scripts
- `scripts/setup_houdini_ai.py`: Builds a basic spaceship blockout in Houdini 20+ and optionally calls a Stable Diffusion API to generate a texture from a prompt, then assigns it to a Principled Shader. Run inside Houdini's Python shell or with `hython`.

## AI Integrations Setup (Windows, PowerShell)
The following commands set up local AI tools and dependencies for Houdini 20+ (Python 3.9).

### 1) Clone AI tools
```powershell
# From the project root
cd "${PWD}\ai_tools"

# Automatic1111 Stable Diffusion web UI
git clone --depth 1 https://github.com/AUTOMATIC1111/stable-diffusion-webui stable-diffusion-webui

# StableHoudini utilities
git clone https://github.com/stassius/StableHoudini.git StableHoudini
```

You can copy/paste the following from Cursor's terminal to populate `ai_tools/`:

```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar\ai_tools"
git clone --depth 1 https://github.com/AUTOMATIC1111/stable-diffusion-webui.git stable-diffusion-webui
git clone https://github.com/stassius/StableHoudini.git StableHoudini
```

### 2) Launch Stable Diffusion locally
```powershell
cd "${PWD}\stable-diffusion-webui"

# First run will set up a Python env and download dependencies.
# Add flags as needed: --xformers (NVIDIA), --listen (LAN), --autolaunch (open browser)
./webui-user.bat --autolaunch
```

Notes:
- Default server address is `http://127.0.0.1:7860`.
- Place models in `ai_tools/stable-diffusion-webui/models/Stable-diffusion` as needed.

### Enable Stable Diffusion API access
To use programmatic calls from Houdini, enable `--api` in `webui-user.bat`:

```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar\ai_tools\stable-diffusion-webui"
Copy-Item .\webui-user.bat .\webui-user.bat.bak -Force
Add-Content .\webui-user.bat "set COMMANDLINE_ARGS=%COMMANDLINE_ARGS% --api"
```

Re-launch the web UI afterwards.

### 3) Install Python deps for Houdini's Python 3.9
Houdini ships with its own Python. Install `requests` into that interpreter so `setup_houdini_ai.py` can call the Stable Diffusion API.

```powershell
# Set this to your actual Houdini install directory
$env:HFS = "C:\Program Files\Side Effects Software\Houdini 20.0.653"

# Houdini's embedded Python (3.9)
$py = Join-Path $env:HFS "python39\\python.exe"

# Ensure pip exists and upgrade it, then install requests
& $py -m ensurepip --upgrade
& $py -m pip install --upgrade pip
& $py -m pip install requests
```

Alternative (advanced): create a separate Python 3.9 venv and add its `site-packages` to `PYTHONPATH` before launching Houdini/hython.

### 4) Test the integration
Start Stable Diffusion first (step 2), then run the Houdini script via `hython`:

```powershell
# Using the same $env:HFS from above
$hython = Join-Path $env:HFS "bin\\hython.exe"

# Point to your project root
$proj = "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"

# Call the setup with the SD API URL; this builds the node network and tries to fetch a texture
& $hython -c "import sys; sys.path.append(r'$proj'); from scripts.setup_houdini_ai import setup_interstellar_ai; setup_interstellar_ai(sd_api_url='http://127.0.0.1:7860')"
```

If the AI step succeeds, a texture will be saved under `ai_tools/generated/` and assigned to the ship material. If the API is unreachable, the script will continue and use a default shader.

## Quick start: Launch SD and install Houdini deps (Windows)
Follow these numbered steps. Copy-paste the commands into Cursor’s terminal.

1) Launch Stable Diffusion (first run downloads dependencies)
```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar\ai_tools\stable-diffusion-webui"
.\u005cwebui-user.bat --autolaunch
```
- If you get a 404 on API docs, enable API support and re-launch:
```powershell
Copy-Item .\webui-user.bat .\webui-user.bat.bak -Force
Add-Content .\webui-user.bat "set COMMANDLINE_ARGS=%COMMANDLINE_ARGS% --api"
.\u005cwebui-user.bat --autolaunch
```
- Test in browser: `http://127.0.0.1:7860` (UI) and `http://127.0.0.1:7860/docs` (API docs)
- Try a prompt in the UI, e.g., "futuristic spaceship"

2) (Optional) Download a base model
- Put a `.safetensors` or `.ckpt` model (e.g., SD 1.5) into:
  `ai_tools/stable-diffusion-webui/models/Stable-diffusion/`

3) Install Python deps for Houdini 20.5 (Python 3.9)
```powershell
# Set to your installed build (use your latest 20.5 build)
$env:HFS = "C:\Program Files\Side Effects Software\Houdini 20.5.682"

# Houdini's embedded Python (3.9). If this path doesn't exist, see Troubleshooting below.
$py = Join-Path $env:HFS "python39\python.exe"
& $py -m ensurepip --upgrade
& $py -m pip install --upgrade pip
& $py -m pip install requests
```

Troubleshooting (Python versions):
- Stable Diffusion uses its own Python (3.10+) in a separate venv. This does not affect Houdini.
- Houdini uses its embedded Python. If `python39` does not exist, your build may ship with a different version (e.g., `python311`). Try:
```powershell
$py = Join-Path $env:HFS "python311\python.exe"
```
Then rerun the pip commands above.

No Git commit yet—verify everything runs, then commit changes later.

## Generate your first spaceship (test run)
Follow these steps to verify the setup and build the initial blockout with an AI texture.

1) Launch Houdini 20.5 and save a new scene
- Open Houdini 20.5
- File → New Scene
- File → Save As → save to: `houdini/interstellar_ship.hip`

2) Ensure Stable Diffusion is running
- Start the web UI and API (see steps above) and confirm:
  - UI: `http://127.0.0.1:7860`
  - API docs: `http://127.0.0.1:7860/docs`

3) Option A: Run the script via hython (one command)
```powershell
# Update this to your installed Houdini build path
$env:HFS = "C:\Program Files\Side Effects Software\Houdini 20.5.682"
$hython = Join-Path $env:HFS "bin\hython.exe"

# Your Interstellar project path
$proj = "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"

# Build the spaceship and request an AI texture
& $hython -c "import sys; sys.path.append(r'$proj'); from scripts.setup_houdini_ai import setup_interstellar_ai; setup_interstellar_ai(sd_api_url='http://127.0.0.1:7860', prompt='gigantic interstellar spaceship hull with detailed panels and thrusters', prompt_tweaks='add procedural rivets and glowing conduits')"
```

4) Option B: Run inside Houdini’s Python Shell (GUI)
- Windows → Python Shell, then paste and run:
```python
import sys
sys.path.append(r"C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar")
from scripts.setup_houdini_ai import setup_interstellar_ai
setup_interstellar_ai(
    sd_api_url='http://127.0.0.1:7860',
    prompt='gigantic interstellar spaceship hull with detailed panels and thrusters',
    prompt_tweaks='add procedural rivets and glowing conduits'
)
```

5) Check outputs
- Houdini viewport: you should see a tube hull with two engine spheres; material assigned.
- Files: `ai_tools/generated/ship_view.png` and `ai_tools/generated/ship_texture.png` (if the API returned an image).
- If the texture is missing, the script still assigns a default Principled Shader.

6) Troubleshooting
- Error “hou not found”: run with `hython` (Option A) or inside Houdini’s Python Shell (Option B).
- “requests not found”: install with Houdini’s Python (see earlier pip steps).
- Snapshot render fails: okay to proceed; the script falls back to a text-only prompt for texture.

7) Commit results to GitHub (after you verify)
```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"
git add houdini/ ai_tools/generated/
git commit -m "feat: initial spaceship blockout with AI texture"
git push
```

### StableHoudini install and configuration (Houdini 20.5)
StableHoudini provides TOP nodes to batch SD tasks. After cloning in `ai_tools/StableHoudini`:

1) Install HDA in Houdini:
- Houdini → Assets → Install Asset Library…
- Select `ai_tools/StableHoudini/hda/top_stable_diffusion.hda`

2) Place side folders next to the HDA (optional convenience):
```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"
New-Item -ItemType Directory -Force -Path ".\ai_tools\StableHoudini\hda\Python",".\ai_tools\StableHoudini\hda\Presets" | Out-Null
Copy-Item -Recurse -Force ".\ai_tools\StableHoudini\Python\*" ".\ai_tools\StableHoudini\hda\Python" 2>$null
Copy-Item -Recurse -Force ".\ai_tools\StableHoudini\Presets\*" ".\ai_tools\StableHoudini\hda\Presets" 2>$null
```

3) Configure StableHoudini after first use:
- Open `config.ini` created by StableHoudini (commonly in your Houdini prefs or near the HDA)
- Set `API URL = http://127.0.0.1:7860`
- Set `Timeout = 0.15`

Compatibility: tested with Houdini 20.5 (Python 3.9). If using a different Houdini build, ensure Python 3.9 compatibility or adjust paths accordingly.

## Version Control: Git + GitHub

### Initialize repository locally
```powershell
cd "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"
git init
git add .
git commit -m "chore: initial commit for Interstellar"
```

### Create GitHub repository
- Using GitHub CLI (recommended):
```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli -e --source winget
gh --version

# Authenticate once if needed
gh auth login

# Create and push in one step from project root
gh repo create Interstellar --public --source . --remote origin --push
```

- Or manual (via website):
  1. Create a new repo named "Interstellar" on GitHub (no README).
  2. Then set remote and push:
```powershell
git remote add origin https://github.com/<your-user>/Interstellar.git
git branch -M main
git push -u origin main
```

Authentication:
- If prompted for credentials during `git push` over HTTPS, use a GitHub Personal Access Token (PAT) as the password. You can create one from GitHub → Settings → Developer settings → Personal access tokens.

Verify on GitHub after push:
```powershell
start https://github.com/<your-user>/Interstellar
```

### Clone instructions
```powershell
git clone https://github.com/<your-user>/Interstellar.git
cd Interstellar
```

### Contributor setup
- Install Houdini 20+ (Python 3.9) and ensure `hython` is available.
- Follow the AI setup in this README (Stable Diffusion web UI + requests in Houdini Python).
- Optional: install Git LFS for large binary assets you do want to track (textures, renders).

### Basic Git workflow
```powershell
# Check status
git status

# Stage changes
git add <files-or-dirs>

# Commit with a message
git commit -m "feat: add new cockpit generator"

# Push to origin
git push

# Pull latest changes
git pull
```

## Vibe coding workflow (AI-assisted)

### 1) Generate Houdini nodes with AI (in Cursor)
Use natural language to request Python/VEX snippets that build node networks.

Example prompts (paste into Cursor):
- "In Houdini Python (hou), create a retro-futuristic cockpit: tube hull, grid dashboard, scattered spheres as holographic projectors; add UVs and a Principled Shader; camera at t=(0,3,8)."
- "Add procedural rivets on the hull and glowing conduits around engines; expose rivet density and conduit radius as parameters."

Run generated code inside Houdini: Windows → Python Shell, or via `hython`.

### 2) Quick blockout + AI texture
Ensure Stable Diffusion web UI is running (`http://127.0.0.1:7860`), then:
```powershell
# Using your $env:HFS and $proj from earlier
$hython = Join-Path $env:HFS "bin\hython.exe"
$proj = "C:\Users\sugar\Desktop\ALL AI GAMES\Projects in prgress\Interstellar"
& $hython -c "import sys; sys.path.append(r'$proj'); from scripts.setup_houdini_ai import setup_interstellar_ai; setup_interstellar_ai(sd_api_url='http://127.0.0.1:7860', prompt='futuristic metallic spaceship panel with neon accents', prompt_tweaks='add procedural rivets and glowing conduits', cockpit_style='retro-futuristic cockpit with neon holograms', build_stablehoudini_pdg=True)"
```
Outputs: `ai_tools/generated/ship_view.png` and `ai_tools/generated/ship_texture.png` (if SD is reachable).

### 3) Export to Unity for 3D exploration
- In Houdini: use ROP FBX Character Output (or File → Export → Filmbox FBX) to export `exports/ship.fbx`.
  - In `/out`, create an FBX ROP (e.g., `rop_fbx1`), set Output File to `$HIP/exports/ship.fbx`, set Obj Path to `/obj/interstellar_ship` (and cockpit `/obj/interstellar_cockpit` if desired).
  - Render the ROP to write the FBX.
- In Unity: place `ship.fbx` under `Assets/Models/`. Assign the generated texture to your material (e.g., Standard/URP/Lit) and tweak emission for neon accents.

### 4) Iterate visuals with Stable Diffusion
Change the prompt to explore styles:
- "weathered star cruiser panels, subtle grime, painted squad insignia"
- "sleek white ceramic hull with cyan emissive tracers, minimalistic"

Re-run the script (Step 2) to refresh textures and materials.

### 5) Commit progress to GitHub
```powershell
git add .
git commit -m "vibe: cockpit blockout + SD neon panel texture"
git push
```


