"""Final verification + PIE playtests for Req 4-7."""
import json
import socket
import time
import hashlib
from pathlib import Path

BP = "BP_ProceduralTownGenerator"
PKG = "BP_LostPackage"


def send(t, p=None, timeout=60):
    for attempt in range(3):
        try:
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
            return {"error": "empty"}
        except Exception as e:
            print("retry", t, e, flush=True)
            time.sleep(2)
    return {"error": "fail " + t}


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("=== SAFETY HASHES ===", flush=True)
orig = Path(r"C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset")
bak = Path(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset")
before = Path(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP_BEFORE_MCP\Content\Procedural\BP_ProceduralTownGenerator.uasset")
pkg = Path(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_LostPackage.uasset")
print("orig exists", orig.exists(), "sha", file_sha1(orig) if orig.exists() else None)
print("bak exists", bak.exists(), "sha", file_sha1(bak) if bak.exists() else None)
print("before_mcp exists", before.exists())
print("lost_pkg exists", pkg.exists())

print("=== COMPILE ===", flush=True)
print("gen", send("compile_blueprint", {"blueprint_name": BP}))
print("pkg", send("compile_blueprint", {"blueprint_name": PKG}))
print("mesh", send("set_static_mesh_properties", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "static_mesh": "/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"
}))

print("=== GRAPH CHECK ===", flush=True)
nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
fns = [n.get("function_name") or "" for n in nodes]
classes = [n.get("class") or "" for n in nodes]
titles = [n.get("title") or "" for n in nodes]
checks = {
    "MakeRotator": "MakeRotator" in fns,
    "MakeVector>=2": fns.count("MakeVector") >= 2,
    "RandomFloat>=4": fns.count("RandomFloatInRange") >= 4,
    "Array_Clear": "Array_Clear" in fns,
    "ForEachLoop": "ForEachLoop" in fns,
    "Vector_Distance": "Vector_Distance" in fns,
    "Array_Add": "Array_Add" in fns,
    "SpawnActor": "K2Node_SpawnActorFromClass" in classes or any("Spawn Actor" in t for t in titles),
    "Branches": classes.count("K2Node_IfThenElse") >= 4,
    "ForLoops": fns.count("ForLoop") >= 2,
}
for k, v in checks.items():
    print(f"  {k}: {v}")

bp = send("get_node_pins", {"blueprint_name": BP, "node_id": "38D207164FD12DF5F78EC6B35C9F85D4"})
print("BeginPlay.then", [p.get("linked_to") for p in bp.get("pins", []) if p["name"] == "then"])

# Confirm generator actor in level
actors = send("get_actors_in_level", {}).get("actors", [])
gens = [a for a in actors if "Procedural" in a.get("name", "") or "Town" in a.get("name", "")]
print("generator actors", gens[:10], "total actors", len(actors))

print("=== PIE RUNS ===", flush=True)
results = []
for i in range(3):
    print(f"--- PIE {i+1} ---", flush=True)
    print(send("play_in_editor", {}))
    time.sleep(6)
    pie_actors = send("get_actors_in_level", {}).get("actors", [])
    # During PIE, get_actors may still see editor world; try find packages
    pkgs = [a for a in pie_actors if "LostPackage" in a.get("name", "") or "BP_LostPackage" in a.get("class", "")]
    statics = [a for a in pie_actors if a.get("class") == "StaticMeshActor" or "StaticMesh" in a.get("class", "")]
    print("actors during pie", len(pie_actors), "pkg-like", pkgs[:5])
    results.append({"n": len(pie_actors), "pkgs": pkgs})
    print(send("stop_play_in_editor", {}))
    time.sleep(2)

print("ALL_CHECKS", checks)
print("PIE_RESULTS", results)
print("FINAL_OK", all(checks.values()), flush=True)
