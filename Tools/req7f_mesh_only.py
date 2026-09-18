"""Add PackageMesh only (no sphere), set mesh/scale, compile, verify."""
import json
import socket
import time

PKG = "BP_LostPackage"
MESH = "/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"


def send(t, p=None, timeout=90):
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
    data = b""
    while True:
        c = s.recv(65536)
        if not c:
            break
        data += c
        try:
            return json.loads(data.decode()).get("result", json.loads(data.decode()))
        except Exception:
            pass
    return {"error": "empty", "raw": data.decode(errors="replace")[:200]}


print("1 add", send("add_component_to_blueprint", {
    "blueprint_name": PKG,
    "component_type": "StaticMeshComponent",
    "component_name": "PackageMesh",
    "scale": [2.0, 2.0, 2.0],
}), flush=True)

print("2 mesh", send("set_static_mesh_properties", {
    "blueprint_name": PKG,
    "component_name": "PackageMesh",
    "static_mesh": MESH,
}), flush=True)

print("3 scale", send("set_component_property", {
    "blueprint_name": PKG,
    "component_name": "PackageMesh",
    "property_name": "RelativeScale3D",
    "property_value": [2.0, 2.0, 2.0],
}), flush=True)

print("4 overlap", send("set_component_property", {
    "blueprint_name": PKG,
    "component_name": "PackageMesh",
    "property_name": "bGenerateOverlapEvents",
    "property_value": True,
}), flush=True)

time.sleep(0.5)
print("5 compile", send("compile_blueprint", {"blueprint_name": PKG}), flush=True)

# verify component still addressable
print("6 mesh again", send("set_static_mesh_properties", {
    "blueprint_name": PKG,
    "component_name": "PackageMesh",
    "static_mesh": MESH,
}), flush=True)

print("7 spawn", send("spawn_blueprint_actor", {
    "blueprint_name": PKG,
    "actor_name": "LostPackage_Preview",
    "location": [400, 400, 80],
}), flush=True)

actors = send("get_actors_in_level", {}).get("actors", [])
for a in actors:
    if "Package" in a.get("name", "") or "Lost" in a.get("name", ""):
        print("ACTOR", a, flush=True)
print("DONE", flush=True)
