import json, socket, time

def send(t, p=None, timeout=60):
    s = socket.socket(); s.settimeout(timeout); s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
    data = b""
    while True:
        c = s.recv(65536)
        if not c: break
        data += c
        try:
            return json.loads(data.decode()).get("result", json.loads(data.decode()))
        except Exception:
            pass

PKG="BP_LostPackage"
MESH="/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"

print("add mesh", send("add_component_to_blueprint", {
    "blueprint_name": PKG,
    "component_type": "StaticMeshComponent",
    "component_name": "PackageMesh",
    "scale": [2.0, 2.0, 2.0]
}))
print("set mesh", send("set_static_mesh_properties", {
    "blueprint_name": PKG, "component_name": "PackageMesh", "static_mesh": MESH
}))
print("add sphere", send("add_component_to_blueprint", {
    "blueprint_name": PKG,
    "component_type": "SphereComponent",
    "component_name": "OverlapSphere",
    "scale": [1.0, 1.0, 1.0]
}))
print("overlap", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "bGenerateOverlapEvents", "property_value": True
}))
print("radius", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "SphereRadius", "property_value": 100.0
}))
# small delay then compile
time.sleep(1)
print("compile", send("compile_blueprint", {"blueprint_name": PKG}))
# verify by spawning actor in level
print("spawn test", send("spawn_blueprint_actor", {
    "blueprint_name": PKG, "actor_name": "TestLostPackage",
    "location": [0, 0, 100]
}))
print("actors", [a for a in send("get_actors_in_level", {}).get("actors", []) if "Package" in a.get("name","") or "Lost" in a.get("name","")])
