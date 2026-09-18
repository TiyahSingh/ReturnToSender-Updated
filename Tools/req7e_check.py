"""Create a clean BP_LostPackage actor (new name) step-by-step."""
import json, socket, time

NAME = "BP_LostPackage"
# If old one is corrupted, use a clean name and retarget spawn
CLEAN = "BP_LostPackage"

def send(t, p=None, timeout=45):
    for attempt in range(3):
        try:
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
            return {"error":"empty"}
        except Exception as e:
            print("retry", t, e, flush=True); time.sleep(2)
    return {"error":"fail"}

def nid(r): return r.get("node_id") if isinstance(r, dict) else None

# Try compile existing first
print("compile existing", send("compile_blueprint", {"blueprint_name": NAME}), flush=True)

# Check components via set_static_mesh - if works, mesh exists
print("mesh set", send("set_static_mesh_properties", {
    "blueprint_name": NAME, "component_name": "PackageMesh",
    "static_mesh": "/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"
}), flush=True)

# Inspect nodes
nodes = send("find_blueprint_nodes", {"blueprint_name": NAME, "node_type": "All"}).get("nodes", [])
print("nodes", len(nodes))
for n in nodes:
    print(" ", n.get("title"), n.get("class"))

# Spawn into level to visually verify
print("spawn", send("spawn_blueprint_actor", {
    "blueprint_name": NAME,
    "actor_name": "LostPackage_Preview",
    "location": [300, 300, 50],
    "scale": [2,2,2]
}), flush=True)
actors = send("get_actors_in_level", {}).get("actors", [])
for a in actors:
    if "Package" in a.get("name","") or "Lost" in a.get("name",""):
        print("ACTOR", a)
        print("props", send("get_actor_properties", {"name": a["name"]}))
