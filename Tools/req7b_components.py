import json, socket

def send(t, p=None, timeout=45):
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
    "blueprint_name": PKG, "component_type": "StaticMeshComponent", "component_name": "PackageMesh"
}))
print("set mesh", send("set_static_mesh_properties", {
    "blueprint_name": PKG, "component_name": "PackageMesh", "static_mesh": MESH
}))
print("scale", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "property_name": "RelativeScale3D", "property_value": [2.0, 2.0, 2.0]
}))
print("add sphere", send("add_component_to_blueprint", {
    "blueprint_name": PKG, "component_type": "SphereComponent", "component_name": "OverlapSphere"
}))
print("overlap", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "bGenerateOverlapEvents", "property_value": True
}))
print("radius", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "SphereRadius", "property_value": 80.0
}))
print("compile", send("compile_blueprint", {"blueprint_name": PKG}))
