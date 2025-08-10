"""
Run inside hython. Automates:
- Install StableHoudini HDA (best-effort)
- Create TOP network scaffold
- Build Interstellar ship + cockpit via setup_interstellar_ai
- Save .hip to houdini/interstellar_ship.hip
"""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    import hou  # type: ignore

    project_root = Path(os.getcwd())

    # Install StableHoudini HDA best-effort
    hda_file = project_root / "ai_tools" / "StableHoudini" / "hda" / "top_Stable_Diffusion.hda"
    try:
        if hda_file.exists():
            hou.hda.installFile(str(hda_file))
            print(f"[Interstellar] Installed HDA: {hda_file}")
    except Exception as exc:
        print(f"[Interstellar] HDA install skipped: {exc}")

    # Create TOP network scaffold
    obj = hou.node("/obj")
    if obj is None:
        raise RuntimeError("/obj not found")
    topnet = obj.node("stablehoudini_pdg") or obj.createNode("topnet", node_name="stablehoudini_pdg")
    try:
        if topnet.node("localscheduler") is None:
            topnet.createNode("localscheduler", node_name="localscheduler")
    except Exception as exc:
        print(f"[Interstellar] localscheduler setup skipped: {exc}")

    # Create SD Dream (PDG) node if available and set basic parms
    sd_node = topnet.node("sd_dream1")
    if sd_node is None:
        try:
            # HDA internal type name is the basename of the .hda (TOP operator)
            sd_node = topnet.createNode("top_Stable_Diffusion", node_name="sd_dream1")
        except Exception as exc:
            print(f"[Interstellar] Could not create SD Dream node: {exc}")
            sd_node = None
    if sd_node is not None:
        try:
            if sd_node.parm("api_url"):
                sd_node.parm("api_url").set("http://127.0.0.1:7860")
            if sd_node.parm("prompt"):
                sd_node.parm("prompt").set("retro-futuristic cockpit with neon holograms")
        except Exception as exc:
            print(f"[Interstellar] Could not set SD Dream parms: {exc}")

    # Build geometry using project script
    from scripts.setup_houdini_ai import setup_interstellar_ai

    setup_interstellar_ai(
        sd_api_url="http://127.0.0.1:7860",
        prompt="futuristic metallic spaceship panel with neon accents",
        prompt_tweaks="add procedural rivets and glowing conduits",
        cockpit_style="retro-futuristic cockpit with neon holograms",
        build_stablehoudini_pdg=True,
    )

    hip_path = project_root / "houdini" / "interstellar_ship.hip"
    hip_path.parent.mkdir(parents=True, exist_ok=True)
    hou.hipFile.save(str(hip_path))
    print(f"[Interstellar] Saved .hip to {hip_path}")


if __name__ == "__main__":
    main()


