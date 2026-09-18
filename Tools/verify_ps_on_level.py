import json, socket, time, threading, math, hashlib
from pathlib import Path

def send(t, p=None, timeout=60):
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

print("open map", send("execute_console_command", {"command": "Open /Game/ThirdPerson/Lvl_ThirdPerson"}), flush=True)
time.sleep(8)
actors = send("get_actors_in_level", {}).get("actors", [])
starts = [a for a in actors if "PlayerStart" in a.get("class","")]
gens = [a for a in actors if "ProceduralTown" in a.get("class","")]
print("PLAYER_START", starts, flush=True)
print("GENERATOR", gens, flush=True)
print("actor_count", len(actors), flush=True)

print("COMPILE", send("compile_blueprint", {"blueprint_name": "BP_ProceduralTownGenerator"}), flush=True)

# Verify BeginPlay chain still has protect
nodes = send("find_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_type":"All"}).get("nodes",[])
for n in nodes:
    if n.get("function_name")=="GetActorOfClass" or "Get Actor Of Class" in (n.get("title") or ""):
        pins = send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":n["node_guid"]})
        print("GetActorOfClass pins class", [(p["name"], p.get("default_object")) for p in pins.get("pins",[]) if "Class" in p["name"]], flush=True)

pkg_locs=[]; mesh_ok=[]
for i in range(3):
    print(f"\n=== PIE {i+1} ===", flush=True)
    send("stop_play_in_editor", {})
    time.sleep(2)
    threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
    ok=False
    for t in range(30):
        time.sleep(1)
        a = send("get_actors_in_level", {})
        if not a.get("from_play_world"):
            continue
        actors = a.get("actors") or []
        pkgs = [x for x in actors if "LostPackage" in str(x.get("class",""))]
        gens = [x for x in actors if "ProceduralTown" in str(x.get("class",""))]
        comps=[]
        if gens:
            comps = send("get_actor_components", {"name": gens[0]["name"]}).get("components") or []
        meshes = [c for c in comps if "StaticMesh" in c.get("class","")]
        # exclude likely default scene root with ~0 size by requiring non-zero relative or name contains NODE_/StaticMeshComponent
        spawned = []
        for c in meshes:
            rel = c.get("relative_location") or [0,0,0]
            world = c.get("world_location") or rel
            # spawned trees have non-trivial XY usually; include all static meshes except pure root at exactly generator origin with no mesh? keep all and filter root by name
            if c.get("name") in ("DefaultSceneRoot", "RootComponent", "Root"):
                continue
            spawned.append((c.get("name"), world, xy_dist((world[0], world[1]))))
        too_close = [s for s in spawned if s[2] < 200]
        pkg_info=[]
        for p in pkgs:
            loc=p.get("location") or [0,0,0]
            d=xy_dist((loc[0],loc[1]))
            pkg_info.append((loc, round(d,2), d>=200))
            pkg_locs.append(tuple(loc))
        print(f"actors={len(actors)} static_meshes={len(spawned)} too_close={[(n,loc,round(d,1)) for n,loc,d in too_close]}", flush=True)
        print(f"packages={pkg_info}", flush=True)
        # pairwise separation sample among spawned
        closes=[]
        for i1 in range(len(spawned)):
            for i2 in range(i1+1, len(spawned)):
                a1=spawned[i1][1]; a2=spawned[i2][1]
                d=xy_dist((a1[0],a1[1]), (a2[0],a2[1]))
                if d < 200:
                    closes.append((spawned[i1][0], spawned[i2][0], round(d,1)))
        print(f"pair_too_close_count={len(closes)} sample={closes[:5]}", flush=True)
        mesh_ok.append(len(too_close)==0 and len(spawned)>0)
        ok=True
        break
    send("stop_play_in_editor", {})
    time.sleep(2)
    if not ok:
        print("FAIL no play world", flush=True)
        mesh_ok.append(False)

print("\nSUMMARY", flush=True)
print("trees_clear_of_player", mesh_ok, "all", all(mesh_ok))
print("pkg_locs", pkg_locs)
print("unique_pkgs", len(set(pkg_locs)))
print("pkgs_clear", all(xy_dist((l[0],l[1]))>=200 for l in pkg_locs) if pkg_locs else False)
print("orig", sha1(r"C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset"))
print("bak", sha1(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset"))
