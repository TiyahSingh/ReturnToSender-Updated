import json, socket, time, threading, math, hashlib
from pathlib import Path

def send(t, p=None, timeout=25):
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
    except Exception as e:
        return {"error": str(e)}

def xy_dist(a, b=(0.0, 0.0)):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

# Confirm PlayerStart still
starts = [a for a in send("get_actors_in_level", {}).get("actors", []) if a.get("class")=="PlayerStart"]
print("PLAYER_START", starts)

# Recompile to confirm
print("COMPILE", send("compile_blueprint", {"blueprint_name": "BP_ProceduralTownGenerator"}))

pkg_locs = []
mesh_ok_runs = []
for i in range(3):
    print(f"\n=== PIE {i+1} ===", flush=True)
    send("stop_play_in_editor", {})
    time.sleep(2)
    threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
    data = None
    for t in range(25):
        time.sleep(1)
        a = send("get_actors_in_level", {})
        if a.get("from_play_world"):
            actors = a.get("actors") or []
            pkgs = [x for x in actors if "LostPackage" in str(x.get("class",""))]
            gens = [x for x in actors if "ProceduralTown" in str(x.get("class",""))]
            comps = []
            if gens:
                comps = send("get_actor_components", {"name": gens[0]["name"]}).get("components") or []
            # Static mesh comps that look like spawned ones (not root)
            meshes = [c for c in comps if "StaticMesh" in c.get("class","") and "Root" not in c.get("name","")]
            too_close = []
            for c in meshes:
                loc = c.get("world_location") or c.get("relative_location") or [0,0,0]
                d = xy_dist((loc[0], loc[1]))
                if d < 200:
                    too_close.append((c.get("name"), loc, round(d,2)))
            pkg_info = []
            for p in pkgs:
                loc = p.get("location") or [0,0,0]
                d = xy_dist((loc[0], loc[1]))
                pkg_info.append((loc, round(d,2), d >= 200))
                pkg_locs.append(tuple(loc))
            print(f"actors={len(actors)} mesh_comps={len(meshes)} too_close_meshes={too_close}", flush=True)
            print(f"packages={pkg_info}", flush=True)
            mesh_ok_runs.append(len(too_close)==0 and len(meshes)>0)
            data = True
            break
    send("stop_play_in_editor", {})
    time.sleep(2)
    if not data:
        print("FAIL no play world", flush=True)
        mesh_ok_runs.append(False)

print("\nSUMMARY", flush=True)
print("mesh_clear_runs", mesh_ok_runs, "all_ok", all(mesh_ok_runs))
print("pkg_locs", pkg_locs)
print("unique_pkgs", len(set(pkg_locs)))
print("pkgs_all_clear", all(xy_dist((l[0],l[1]))>=200 for l in pkg_locs) if pkg_locs else False)
orig = Path(r"C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset")
bak = Path(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset")
print("orig_sha", sha1(orig))
print("bak_sha", sha1(bak))
print("untouched", sha1(orig) != sha1(bak))
