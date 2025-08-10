"""
Setup Houdini + AI scaffold for Interstellar.

This script is intended to be run inside Houdini 20+ (Python 3.9) via the Python shell or `hython`.

It will:
- Build a simple spaceship blockout network (hull tube + engine spheres)
- Create a UV pipeline and material assignment
- Optionally render a viewport snapshot and send it to a Stable Diffusion API (e.g., Automatic1111) to generate a texture
- Apply the generated texture to a Principled Shader
    - Allow prompt-driven procedural tweaks like rivets and glowing conduits
    - Optionally add a cockpit (dashboard grid + hologram orbs) with an interior camera
    - Best-effort StableHoudini TOPs hook for advanced texturing via SD Dream PDG (if HDA installed)

Notes:
- The Stable Diffusion integration is best-effort and assumes a local API server. If unavailable, the script will skip the texture step gracefully.
- For production, adapt the renderer/material pipeline to your studio standards (e.g., Karma, MaterialX, USD).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def _ensure_houdini() -> None:
    try:
        import hou  # type: ignore
    except Exception as exc:  # pragma: no cover - only runs outside Houdini
        raise RuntimeError(
            "This script must be run inside Houdini (hou module not found)."
        ) from exc


def _check_versions() -> None:
    import hou  # type: ignore

    # Python
    if not (sys.version_info.major == 3 and sys.version_info.minor == 9):
        # Continue anyway but warn; H20 ships with 3.9
        print(f"[Interstellar] Warning: Python {sys.version_info.major}.{sys.version_info.minor} detected; recommended 3.9")

    # Houdini
    try:
        major = hou.applicationVersion()[0]
        if major < 20:
            print(f"[Interstellar] Warning: Houdini {hou.applicationVersionString()} detected; recommended 20+")
    except Exception:
        pass


def _get_or_create(parent, type_name: str, node_name: str):
    node = parent.node(node_name)
    if node is None:
        node = parent.createNode(type_name, node_name=node_name)
    return node


def _create_spaceship_blockout(prompt_tweaks: Optional[str] = None):
    import hou  # type: ignore

    obj = hou.node("/obj")
    if obj is None:
        raise RuntimeError("/obj not found")

    geo = _get_or_create(obj, "geo", "interstellar_ship")
    # Clear default file node inside new geo containers
    for c in geo.children():
        try:
            if c.type().name() == "file":
                c.destroy()
        except Exception:
            pass

    # Main HULL (5km ~ 5000 units along Z)
    hull_length = 5000.0
    hull_radius = 80.0

    core = _get_or_create(geo, "tube", "hull_core")
    core.parm("type").set(1)  # Polygon
    core.parm("orient").set(2)  # Z axis
    core.parm("height").set(hull_length)
    core.parm("rad1").set(hull_radius)
    core.parm("rad2").set(hull_radius)
    core.parm("cap").set(True)

    # Layered metallic shielding (slightly larger radii shells)
    shield1 = _get_or_create(geo, "tube", "hull_shield_1")
    for p in ("type", "orient", "height", "rad1", "rad2", "cap"):
        shield1.parm(p).set(core.parm(p))
    shield1.parm("rad1").set(hull_radius * 1.05)
    shield1.parm("rad2").set(hull_radius * 1.05)

    shield2 = _get_or_create(geo, "tube", "hull_shield_2")
    for p in ("type", "orient", "height", "rad1", "rad2", "cap"):
        shield2.parm(p).set(core.parm(p))
    shield2.parm("rad1").set(hull_radius * 1.1)
    shield2.parm("rad2").set(hull_radius * 1.1)

    # Fusion engines (rear): nozzle cones + plasma cores near tail (negative Z)
    tail_z = -hull_length * 0.5
    engine_offset = 140.0
    nozzle_length = 150.0
    nozzle_radius = 40.0

    noz_l = _get_or_create(geo, "cone", "engine_nozzle_L")
    noz_l.parm("type").set(1)  # polygon
    noz_l.parm("height").set(nozzle_length)
    noz_l.parm("rad").set(nozzle_radius)
    noz_l.parmTuple("t").set((engine_offset, 0.0, tail_z + nozzle_length * 0.5))
    noz_l.parmTuple("r").set((90.0, 0.0, 0.0))  # aim along +Z

    noz_r = _get_or_create(geo, "cone", "engine_nozzle_R")
    noz_r.parm("type").set(1)
    noz_r.parm("height").set(nozzle_length)
    noz_r.parm("rad").set(nozzle_radius)
    noz_r.parmTuple("t").set((-engine_offset, 0.0, tail_z + nozzle_length * 0.5))
    noz_r.parmTuple("r").set((90.0, 0.0, 0.0))

    plasma_l = _get_or_create(geo, "sphere", "engine_plasma_L")
    plasma_l.parm("type").set(2)
    plasma_l.parm("radx").set(nozzle_radius * 0.6)
    plasma_l.parm("rady").set(nozzle_radius * 0.6)
    plasma_l.parm("radz").set(nozzle_radius * 0.6)
    plasma_l.parmTuple("t").set((engine_offset, 0.0, tail_z + nozzle_length))

    plasma_r = _get_or_create(geo, "sphere", "engine_plasma_R")
    plasma_r.parm("type").set(2)
    plasma_r.parm("radx").set(nozzle_radius * 0.6)
    plasma_r.parm("rady").set(nozzle_radius * 0.6)
    plasma_r.parm("radz").set(nozzle_radius * 0.6)
    plasma_r.parmTuple("t").set((-engine_offset, 0.0, tail_z + nozzle_length))

    # Bussard scoops (front): intake ring + cone (positive Z)
    nose_z = hull_length * 0.5
    scoop_ring = _get_or_create(geo, "torus", "bussard_ring")
    scoop_ring.parm("type").set(1)
    scoop_ring.parm("rad1").set(hull_radius * 1.6)
    scoop_ring.parm("rad2").set(hull_radius * 0.2)
    scoop_ring.parmTuple("t").set((0.0, 0.0, nose_z - 50.0))

    scoop_cone = _get_or_create(geo, "cone", "bussard_cone")
    scoop_cone.parm("type").set(1)
    scoop_cone.parm("height").set(400.0)
    scoop_cone.parm("rad").set(hull_radius * 1.2)
    scoop_cone.parmTuple("t").set((0.0, 0.0, nose_z - 200.0))
    scoop_cone.parmTuple("r").set((-90.0, 0.0, 0.0))  # open toward +Z

    merge = _get_or_create(geo, "merge", "ship_merge")
    merge.setInput(0, core)
    merge.setInput(1, shield1)
    merge.setInput(2, shield2)
    merge.setInput(3, noz_l)
    merge.setInput(4, noz_r)
    merge.setInput(5, plasma_l)
    merge.setInput(6, plasma_r)
    merge.setInput(7, scoop_ring)
    merge.setInput(8, scoop_cone)

    polyreduce = _get_or_create(geo, "polyreduce::2.0", "opt_reduce") if hou.sopNodeTypeCategory().nodeType("polyreduce::2.0") else _get_or_create(geo, "polyreduce", "opt_reduce")
    polyreduce.setInput(0, merge)
    polyreduce.parm("percentage").set(100)  # default no reduction; keep node for later

    # UVs
    uvflatten = _get_or_create(geo, "uvflatten::2.0", "uvs") if hou.sopNodeTypeCategory().nodeType("uvflatten::2.0") else _get_or_create(geo, "uvunwrap", "uvs")
    uvflatten.setInput(0, polyreduce)

    # Optional: prompt-driven tweaks
    output = uvflatten
    if prompt_tweaks:
        output = _apply_prompt_tweaks(geo, output, prompt_tweaks)

    # Material assignment placeholder
    mat_sop = _get_or_create(geo, "material", "assign_material")
    mat_sop.setInput(0, output)

    # Flag the display node
    geo.setDisplayFlag(True)
    mat_sop.setDisplayFlag(True)
    mat_sop.setRenderFlag(True)

    return {
        "obj": obj,
        "geo": geo,
        "mat_sop": mat_sop,
        "uv_out": output,
        "hull": core,
        "engines": (noz_l, noz_r),
        "plasma": (plasma_l, plasma_r),
        "bussard": (scoop_ring, scoop_cone),
    }


def _add_cockpit(parent_obj, style_prompt: Optional[str] = None):
    """Create a cockpit: dashboard grid, hologram spheres, and interior camera.

    style_prompt examples: "retro-futuristic cockpit with neon holograms"
    """
    import hou  # type: ignore

    geo = _get_or_create(parent_obj, "geo", "interstellar_cockpit")
    for c in geo.children():
        try:
            if c.type().name() == "file":
                c.destroy()
        except Exception:
            pass

    # Dashboard as a thin grid panel inside hull
    grid = _get_or_create(geo, "grid", "dashboard_grid")
    grid.parm("sizex").set(4.0)
    grid.parm("sizey").set(2.0)
    grid.parmTuple("t").set((0.0, 1.2, 0.0))
    grid.parmTuple("r").set((-10.0, 0.0, 0.0))

    # Hologram emitters: scattered small spheres above dashboard
    scatter = _get_or_create(geo, "scatter", "holo_scatter")
    scatter.setInput(0, grid)
    scatter.parm("npts").set(20)
    scatter.parm("relax").set(1)

    sphere = _get_or_create(geo, "sphere", "holo_orb")
    sphere.parm("type").set(2)
    sphere.parm("radx").set(0.07)
    sphere.parm("rady").set(0.07)
    sphere.parm("radz").set(0.07)

    ctp = _get_or_create(geo, "copytopoints", "holo_copy")
    ctp.setInput(0, sphere)
    ctp.setInput(1, scatter)

    merge = _get_or_create(geo, "merge", "cockpit_merge")
    merge.setInput(0, grid)
    merge.setInput(1, ctp)

    # UVs for cockpit
    uvflatten = _get_or_create(geo, "uvflatten::2.0", "cockpit_uvs") if hou.sopNodeTypeCategory().nodeType("uvflatten::2.0") else _get_or_create(geo, "uvunwrap", "cockpit_uvs")
    uvflatten.setInput(0, merge)

    # Interior camera
    cam = _get_or_create(parent_obj, "cam", "cockpit_cam")
    cam.parmTuple("t").set((0.0, 1.5, 2.5))
    cam.parmTuple("r").set((-8.0, 0.0, 0.0))

    # Simple emissive look hint: attribute for holograms
    attrib = _get_or_create(geo, "attribcreate", "holo_emission_hint")
    attrib.setInput(0, uvflatten)
    attrib.parm("name").set("emit")
    attrib.parm("class").set(1)  # point
    attrib.parm("type").set(0)  # float
    attrib.parm("value1").set(5.0)

    attrib.setDisplayFlag(True)
    attrib.setRenderFlag(True)

    return {"geo": geo, "camera": cam, "out": attrib}


def _apply_prompt_tweaks(geo_node, input_node, prompt_text: str):
    """Add simple procedural details based on keywords in prompt_text."""
    import hou  # type: ignore

    text = prompt_text.lower()
    out = input_node

    if "rivet" in text:
        # Scatter points on hull, copy small circles as rivets
        scatter = _get_or_create(geo_node, "scatter", "rivets_scatter")
        scatter.setInput(0, out)
        scatter.parm("npts").set(400)

        circle = _get_or_create(geo_node, "circle", "rivet_circle")
        circle.parm("type").set(1)  # polygon
        circle.parm("radx").set(0.05)
        circle.parm("rady").set(0.05)

        ctp = _get_or_create(geo_node, "copytopoints", "rivets_copy")
        ctp.setInput(0, circle)
        ctp.setInput(1, scatter)

        out = _connect_merge(geo_node, out, ctp, name="merge_rivets")

    if "glow" in text or "conduit" in text:
        # Simple glowing conduit: a curve extruded with polywire
        curve = _get_or_create(geo_node, "curve", "conduit_curve")
        curve.parm("type").set(1)  # NURBS for easy shaping
        # Provide a tiny default shape along the hull
        curve.parm("coords").set("-1 0 -10  0 0 0  1 0 10")

        polywire = _get_or_create(geo_node, "polywire", "conduit_wire")
        polywire.setInput(0, curve)
        polywire.parm("radius").set(0.05)

        out = _connect_merge(geo_node, out, polywire, name="merge_conduit")

    return out


def _connect_merge(parent, a, b, name: str = "merge"):
    node = parent.node(name)
    if node is None or node.type().name() != "merge":
        node = parent.createNode("merge", node_name=name)
    # find next free input
    inputs = [i for i in range(10)]
    # connect existing first input if not connected
    if node.input(0) is None:
        node.setInput(0, a)
        node.setInput(1, b)
    else:
        # find available slot
        idx = 1
        while node.input(idx) is not None:
            idx += 1
        node.setInput(idx, b)
        # ensure first input remains the base chain
        if node.input(0) != a:
            node.setInput(0, a)
    return node


def _create_camera_and_lights():
    import hou  # type: ignore

    obj = hou.node("/obj")
    cam = _get_or_create(obj, "cam", "interstellar_cam")
    cam.parmTuple("t").set((0, 5, 50))
    cam.parmTuple("r").set((-10, 0, 0))

    light = _get_or_create(obj, "hlight", "key_light")
    light.parmTuple("t").set((20, 30, 40))

    fill = _get_or_create(obj, "hlight", "fill_light")
    fill.parmTuple("t").set((-25, -10, 20))

    return cam


def _try_stablehoudini_pdg(cockpit_geo_path: str) -> None:
    """If StableHoudini TOP node types are available, build a minimal img2img PDG graph.

    This function is best-effort and safe to call even if StableHoudini is not installed.
    """
    try:
        import hou  # type: ignore
        # Check for TOPs context
        topnet = hou.node("/obj").node("stablehoudini_pdg")
        if topnet is None:
            topnet = hou.node("/obj").createNode("topnet", node_name="stablehoudini_pdg")

        # Try a StableHoudini TOP (node name may vary; using a generic name)
        # Common HDA op names could be like: "sd_img2img" or "top_stable_diffusion" under TOPs
        # We'll attempt to create by explicit type name if present, else skip.
        node_types = [
            "sd_img2img",  # hypothetical
            "top_stable_diffusion",  # HDA name from StableHoudini
        ]
        sd_top = None
        for t in node_types:
            if hou.topNodeTypeCategory().nodeType(t):
                sd_top = topnet.createNode(t, node_name="sd_img2img_cockpit")
                break
        if sd_top is None:
            print("[Interstellar] StableHoudini TOP node not found; skipping PDG setup.")
            return

        # Minimal wiring and parms (actual parms depend on HDA; set only when they exist)
        if sd_top.parm("api_url"):
            sd_top.parm("api_url").set("http://127.0.0.1:7860")
        if sd_top.parm("prompt"):
            sd_top.parm("prompt").set("retro-futuristic cockpit with neon holograms, high-fidelity panels")

        # Add a partition or local scheduler if needed
        if topnet.node("localscheduler") is None:
            try:
                localsched = topnet.createNode("localscheduler", node_name="localscheduler")
                sd_top.setInput(0, localsched)
            except Exception:
                pass

        topnet.layoutChildren()
    except Exception as exc:
        print(f"[Interstellar] StableHoudini PDG setup skipped: {exc}")


def _render_viewport_snapshot(output_path: Path, camera_path: str, objects_path: str) -> bool:
    """Render with OpenGL ROP if available, otherwise skip gracefully."""
    import hou  # type: ignore

    out = hou.node("/out")
    if out is None:
        return False

    # Prefer OpenGL ROP for speed; may be named "ogl" or "opengl" depending on version
    rop_type = "opengl" if hou.ropNodeTypeCategory().nodeType("opengl") else ("ogl" if hou.ropNodeTypeCategory().nodeType("ogl") else None)
    if rop_type is None:
        print("[Interstellar] No OpenGL ROP available; skipping snapshot render.")
        return False

    rop = _get_or_create(out, rop_type, "interstellar_snapshot")
    rop.parm("camera").set(camera_path)
    rop.parm("vm_picture").set(str(output_path))
    rop.parm("trange").set(0)
    rop.parm("res1").set(1024)
    rop.parm("res2").set(1024)
    try:
        rop.render()
        return output_path.exists()
    except Exception as exc:
        print(f"[Interstellar] Snapshot render failed: {exc}")
        return False


def _call_stable_diffusion(init_image: Optional[Path], prompt: str, output_image: Path, api_url: Optional[str]) -> bool:
    """Send an image/prompt to a Stable Diffusion HTTP API (Automatic1111-compatible).

    If api_url is None or request fails, returns False.
    """
    if not api_url:
        print("[Interstellar] No Stable Diffusion API URL provided; skipping.")
        return False

    try:
        import requests  # type: ignore
    except Exception:
        print("[Interstellar] 'requests' not available in this Houdini Python; skipping SD call.")
        return False

    payload = {
        "prompt": prompt,
        "steps": 20,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a",
        "width": 1024,
        "height": 1024,
    }

    files = None
    endpoint = "/sdapi/v1/txt2img"
    if init_image and init_image.exists():
        # Use img2img when we have an init image
        endpoint = "/sdapi/v1/img2img"
        import base64

        with init_image.open("rb") as f:
            init_b64 = base64.b64encode(f.read()).decode("utf-8")
        payload.update({
            "init_images": [init_b64],
            "denoising_strength": 0.6,
        })

    try:
        resp = requests.post(api_url.rstrip("/") + endpoint, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images") or []
        if not images:
            print("[Interstellar] SD returned no images.")
            return False

        import base64
        img_b64 = images[0]
        png_bytes = base64.b64decode(img_b64)
        output_image.parent.mkdir(parents=True, exist_ok=True)
        output_image.write_bytes(png_bytes)
        return True
    except Exception as exc:
        print(f"[Interstellar] Stable Diffusion request failed: {exc}")
        return False


def _create_or_update_material(texture_path: Optional[Path]):
    import hou  # type: ignore

    matnet = hou.node("/mat")
    if matnet is None:
        matnet = hou.node("/").createNode("matnet", node_name="mat")

    # Try a modern Principled Shader name first, fallback to legacy
    shader_type = "principledshader::2.0" if hou.matNodeTypeCategory().nodeType("principledshader::2.0") else "principledshader"
    mat = _get_or_create(matnet, shader_type, "ship_mat")

    # Base color texture
    if texture_path and texture_path.exists():
        # Toggle texture usage if param exists
        for parm_name in ("basecolor_useTexture", "basecolortex_useTexture"):
            if mat.parm(parm_name):
                mat.parm(parm_name).set(1)
        for parm_name in ("basecolor_texture", "basecolortex_texture"):
            if mat.parm(parm_name):
                mat.parm(parm_name).set(str(texture_path))

    return mat


def _assign_material_to_geo(material_node_path: str, material_sop):
    if material_sop is None:
        return
    # Assign to all primitives
    if material_sop.parm("shop_materialpath1"):
        material_sop.parm("num_materials").set(1)
        material_sop.parm("group1").set("")
        material_sop.parm("shop_materialpath1").set(material_node_path)


def setup_interstellar_ai(
    prompt: str = "futuristic metallic spaceship panel with neon accents",
    prompt_tweaks: Optional[str] = "add procedural rivets and glowing conduits",
    sd_api_url: Optional[str] = None,
    cockpit_style: Optional[str] = None,
    build_stablehoudini_pdg: bool = False,
) -> None:
    """Create the base spaceship network and optional AI texturing.

    Parameters:
    - prompt: Text prompt for Stable Diffusion texture generation
    - prompt_tweaks: Keywords to influence procedural details (e.g., "rivets", "glowing conduits")
    - sd_api_url: Stable Diffusion API base URL (e.g., http://127.0.0.1:7860). If None, AI step is skipped.
    """

    _ensure_houdini()
    _check_versions()

    import hou  # type: ignore

    # Build geometry and details
    nodes = _create_spaceship_blockout(prompt_tweaks=prompt_tweaks)
    # Optionally add cockpit
    cockpit_nodes = None
    if cockpit_style:
        cockpit_nodes = _add_cockpit(nodes["obj"], style_prompt=cockpit_style)

    # Camera and simple lights for a quick snapshot
    cam = _create_camera_and_lights()

    # Paths
    project_root = Path(hou.expandString("$HIP")) if hou.expandString("$HIP") else Path.cwd()
    ai_dir = project_root / "ai_tools" / "generated"
    snapshot_path = ai_dir / "ship_view.png"
    texture_path = ai_dir / "ship_texture.png"
    cockpit_snapshot_path = ai_dir / "cockpit_view.png"
    cockpit_texture_path = ai_dir / "cockpit_texture.png"

    # Quick snapshot render (best effort)
    snapshot_ok = _render_viewport_snapshot(
        output_path=snapshot_path,
        camera_path=cam.path(),
        objects_path=nodes["geo"].path(),
    )

    # Call SD (prefers img2img when snapshot is available)
    sd_ok = _call_stable_diffusion(
        init_image=snapshot_path if snapshot_ok else None,
        prompt=prompt,
        output_image=texture_path,
        api_url=sd_api_url,
    )

    # Cockpit-specific texture (if cockpit exists)
    if cockpit_nodes is not None:
        cockpit_cam = cockpit_nodes["camera"]
        cockpit_snapshot_ok = _render_viewport_snapshot(
            output_path=cockpit_snapshot_path,
            camera_path=cockpit_cam.path(),
            objects_path=cockpit_nodes["geo"].path(),
        )
        cockpit_ok = _call_stable_diffusion(
            init_image=cockpit_snapshot_path if cockpit_snapshot_ok else None,
            prompt=cockpit_style or "retro-futuristic cockpit with neon holograms",
            output_image=cockpit_texture_path,
            api_url=sd_api_url,
        )
        # Optionally hook up StableHoudini PDG for further iterations
        if build_stablehoudini_pdg:
            _try_stablehoudini_pdg(cockpit_nodes["geo"].path())

    # Create/assign material
    mat = _create_or_update_material(texture_path if sd_ok else None)
    _assign_material_to_geo(mat.path(), nodes["mat_sop"])

    print("[Interstellar] Setup complete.")
    if sd_ok:
        print(f"[Interstellar] Applied AI texture: {texture_path}")
    else:
        print("[Interstellar] AI texture step skipped or failed; using default shader settings.")

    if cockpit_nodes is not None:
        if cockpit_texture_path.exists():
            print(f"[Interstellar] Applied cockpit AI texture: {cockpit_texture_path}")
        else:
            print("[Interstellar] Cockpit AI texture step skipped or failed.")


if __name__ == "__main__":  # pragma: no cover
    # Example usage: run inside Houdini Python shell or hython
    # setup_interstellar_ai(sd_api_url="http://127.0.0.1:7860")
    setup_interstellar_ai()


