"""
Standalone hython script to generate a 5km interstellar ship blockout in Houdini,
optionally fetch an AI texture from a local Stable Diffusion API, assign a
Principled shader, and save the scene.

Run with:
  hython scripts/generate_interstellar_ship.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _safe_requests():
    try:
        import requests  # type: ignore
        return requests
    except Exception:
        return None


def call_sd_txt2img(prompt: str, out_path: Path, api_url: str = "http://127.0.0.1:7860") -> bool:
    """Best-effort call to Automatic1111 txt2img API and write a PNG.
    Returns True on success, False otherwise.
    """
    requests = _safe_requests()
    if requests is None:
        print("[Interstellar] 'requests' not available; skipping SD texture.")
        return False

    payload = {
        "prompt": prompt,
        "steps": 20,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a",
        "width": 1024,
        "height": 1024,
    }
    try:
        resp = requests.post(api_url.rstrip("/") + "/sdapi/v1/txt2img", json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images") or []
        if not images:
            print("[Interstellar] SD returned no images; skipping.")
            return False
        import base64  # lazy import

        img_b64 = images[0]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(base64.b64decode(img_b64))
        print(f"[Interstellar] Wrote AI texture: {out_path}")
        return True
    except Exception as exc:
        print(f"[Interstellar] SD txt2img failed: {exc}")
        return False


def get_or_create(parent, type_name: str, node_name: str):
    node = parent.node(node_name)
    if node is None:
        node = parent.createNode(type_name, node_name=node_name)
    return node


def build_ship(prompt_for_texture: Optional[str]) -> None:
    import hou  # type: ignore

    obj = hou.node("/obj")
    if obj is None:
        obj = hou.node("/").createNode("obj", node_name="obj")

    geo = get_or_create(obj, "geo", "interstellar_ship")
    # Clear default file SOPs if any
    for c in geo.children():
        try:
            if c.type().name() == "file":
                c.destroy()
        except Exception:
            pass

    # Dimensions
    hull_length = 5000.0
    hull_radius = 80.0

    core = get_or_create(geo, "tube", "hull_core")
    core.parm("type").set(1)  # polygon
    core.parm("orient").set(2)  # Z axis
    core.parm("height").set(hull_length)
    core.parm("rad1").set(hull_radius)
    core.parm("rad2").set(hull_radius)
    core.parm("cap").set(True)

    shield1 = get_or_create(geo, "tube", "hull_shield_1")
    for p in ("type", "orient", "height", "rad1", "rad2", "cap"):
        shield1.parm(p).set(core.parm(p))
    shield1.parm("rad1").set(hull_radius * 1.05)
    shield1.parm("rad2").set(hull_radius * 1.05)

    shield2 = get_or_create(geo, "tube", "hull_shield_2")
    for p in ("type", "orient", "height", "rad1", "rad2", "cap"):
        shield2.parm(p).set(core.parm(p))
    shield2.parm("rad1").set(hull_radius * 1.1)
    shield2.parm("rad2").set(hull_radius * 1.1)

    shield3 = get_or_create(geo, "tube", "hull_shield_3")
    for p in ("type", "orient", "height", "rad1", "rad2", "cap"):
        shield3.parm(p).set(core.parm(p))
    shield3.parm("rad1").set(hull_radius * 1.2)
    shield3.parm("rad2").set(hull_radius * 1.2)

    # Engines (rear)
    tail_z = -hull_length * 0.5
    engine_offset = 140.0
    nozzle_length = 150.0
    nozzle_radius = 40.0

    noz_l = get_or_create(geo, "cone", "engine_nozzle_L")
    noz_l.parm("type").set(1)
    noz_l.parm("height").set(nozzle_length)
    noz_l.parm("rad").set(nozzle_radius)
    noz_l.parmTuple("t").set((engine_offset, 0.0, tail_z + nozzle_length * 0.5))
    noz_l.parmTuple("r").set((90.0, 0.0, 0.0))

    noz_r = get_or_create(geo, "cone", "engine_nozzle_R")
    noz_r.parm("type").set(1)
    noz_r.parm("height").set(nozzle_length)
    noz_r.parm("rad").set(nozzle_radius)
    noz_r.parmTuple("t").set((-engine_offset, 0.0, tail_z + nozzle_length * 0.5))
    noz_r.parmTuple("r").set((90.0, 0.0, 0.0))

    plasma_l = get_or_create(geo, "sphere", "engine_plasma_L")
    plasma_l.parm("type").set(2)
    for p in ("radx", "rady", "radz"):
        plasma_l.parm(p).set(nozzle_radius * 0.6)
    plasma_l.parmTuple("t").set((engine_offset, 0.0, tail_z + nozzle_length))

    plasma_r = get_or_create(geo, "sphere", "engine_plasma_R")
    plasma_r.parm("type").set(2)
    for p in ("radx", "rady", "radz"):
        plasma_r.parm(p).set(nozzle_radius * 0.6)
    plasma_r.parmTuple("t").set((-engine_offset, 0.0, tail_z + nozzle_length))

    # Bussard scoop (front)
    nose_z = hull_length * 0.5
    ring = get_or_create(geo, "torus", "bussard_ring")
    ring.parm("type").set(1)
    ring.parm("rad1").set(hull_radius * 1.6)
    ring.parm("rad2").set(hull_radius * 0.2)
    ring.parmTuple("t").set((0.0, 0.0, nose_z - 50.0))

    cone = get_or_create(geo, "cone", "bussard_cone")
    cone.parm("type").set(1)
    cone.parm("height").set(400.0)
    cone.parm("rad").set(hull_radius * 1.2)
    cone.parmTuple("t").set((0.0, 0.0, nose_z - 200.0))
    cone.parmTuple("r").set((-90.0, 0.0, 0.0))

    # Merge → UVs → Material
    merge = get_or_create(geo, "merge", "ship_merge")
    for idx, n in enumerate([
        core, shield1, shield2, shield3, noz_l, noz_r, plasma_l, plasma_r, ring, cone
    ]):
        merge.setInput(idx, n)

    uv_op = (
        "uvflatten::2.0" if hou.sopNodeTypeCategory().nodeType("uvflatten::2.0") else "uvunwrap"
    )
    uvs = get_or_create(geo, uv_op, "uvs")
    uvs.setInput(0, merge)

    # Material SOP
    mat_sop = get_or_create(geo, "material", "assign_material")
    mat_sop.setInput(0, uvs)

    # Material in /mat
    matnet = hou.node("/mat")
    if matnet is None:
        matnet = hou.node("/").createNode("matnet", node_name="mat")
    shader_type = (
        "principledshader::2.0"
        if hou.matNodeTypeCategory().nodeType("principledshader::2.0")
        else "principledshader"
    )
    mat = get_or_create(matnet, shader_type, "ship_mat")

    # Optional AI texture
    texture_file: Optional[Path] = None
    if prompt_for_texture:
        project_root = Path.cwd()
        texture_file = project_root / "ai_tools" / "generated" / "ship_texture.png"
        ok = call_sd_txt2img(prompt_for_texture, texture_file)
        if ok:
            # Toggle texture parms when present
            for name in ("basecolor_useTexture", "basecolortex_useTexture"):
                if mat.parm(name):
                    mat.parm(name).set(1)
            for name in ("basecolor_texture", "basecolortex_texture"):
                if mat.parm(name):
                    mat.parm(name).set(str(texture_file))

    # Assign material to all prims
    if mat_sop.parm("num_materials"):
        mat_sop.parm("num_materials").set(1)
    if mat_sop.parm("group1"):
        mat_sop.parm("group1").set("")
    if mat_sop.parm("shop_materialpath1"):
        mat_sop.parm("shop_materialpath1").set(mat.path())

    # Display flags
    geo.setDisplayFlag(True)
    mat_sop.setDisplayFlag(True)
    mat_sop.setRenderFlag(True)

    geo.layoutChildren()


def main() -> None:
    try:
        import hou  # type: ignore
    except Exception as exc:
        raise SystemExit("This script must be run with hython (Houdini Python).") from exc

    # New empty scene
    try:
        hou.hipFile.clear()
    except Exception:
        pass

    # Build with an example texture prompt
    texture_prompt = (
        "layered metallic shielding, interstellar spacecraft hull panels, "
        "futuristic metallic plating, subtle grime and seams, high detail"
    )
    build_ship(prompt_for_texture=texture_prompt)

    # Ensure output directory exists and save .hipnc
    project_root = Path.cwd()
    out_dir = project_root / "houdini"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "generated_interstellar_ship.hipnc"
    hou.hipFile.save(str(out_file))
    print(f"[Interstellar] Scene saved: {out_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[Interstellar] Error: {e}")


