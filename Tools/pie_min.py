import json, socket, time, threading, math, hashlib

def send(t, p=None, timeout=12):
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

def xy(a, b=(0, 0)):
    return math.hypot(a[0] - b[0], a[1] - b[1])

print("pre", send("get_actors_in_level", {}).get("from_play_world"), len(send("get_actors_in_level", {}).get("actors") or []))
threading.Thread(target=lambda: print("play", send("play_in_editor", {}, timeout=4)), daemon=True).start()
time.sleep(6)
results = []
for run in range(3):
    if run > 0:
        send("stop_play_in_editor", {}, timeout=8)
        time.sleep(2)
        threading.Thread(target=lambda: send("play_in_editor", {}, timeout=4), daemon=True).start()
        time.sleep(6)
    got = False
    for i in range(15):
        a = send("get_actors_in_level", {})
        print(f"run{run+1} t{i}", a.get("from_play_world"), len(a.get("actors") or []), a.get("error"))
        if a.get("from_play_world"):
            actors = a["actors"]
            pkgs = [x for x in actors if "LostPackage" in str(x.get("class", ""))]
            gens = [x for x in actors if "ProceduralTown" in str(x.get("class", ""))]
            pkg_info = [(p.get("location"), round(xy((p["location"][0], p["location"][1])), 1)) for p in pkgs]
            print(" PKG", pkg_info)
            too = []
            closes = 0
            meshes = []
            if gens:
                comps = (send("get_actor_components", {"name": gens[0]["name"]}, timeout=20) or {}).get("components") or []
                for c in comps:
                    if "StaticMesh" not in c.get("class", ""):
                        continue
                    if c.get("name") in ("DefaultSceneRoot", "Root", "RootComponent"):
                        continue
                    w = c.get("world_location") or [0, 0, 0]
                    d = xy((w[0], w[1]))
                    meshes.append((c.get("name"), [round(x, 1) for x in w], round(d, 1)))
                too = [m for m in meshes if m[2] < 200]
                for i1 in range(len(meshes)):
                    for i2 in range(i1 + 1, len(meshes)):
                        if xy((meshes[i1][1][0], meshes[i1][1][1]), (meshes[i2][1][0], meshes[i2][1][1])) < 200:
                            closes += 1
            print(" MESHES", len(meshes), "TOO_CLOSE", too, "PAIR_VIOL", closes)
            results.append({
                "pkg_ok": len(pkgs) >= 1 and all(d >= 200 for _, d in pkg_info),
                "tree_ok": len(too) == 0 and len(meshes) > 0,
                "pair_ok": closes == 0,
                "pkgs": pkg_info,
                "mesh_count": len(meshes),
            })
            got = True
            break
        time.sleep(1)
    if not got:
        results.append({"pkg_ok": False, "tree_ok": False, "pair_ok": False, "pkgs": [], "mesh_count": 0})

send("stop_play_in_editor", {}, timeout=8)
print("RESULTS", results)
print("PASS_TREES", all(r["tree_ok"] for r in results))
print("PASS_PAIRS", all(r["pair_ok"] for r in results))
print("PASS_PKG", all(r["pkg_ok"] for r in results))
print("UNIQUE_PKG", len(set(tuple(p[0]) for r in results for p in r["pkgs"])))
print("orig", hashlib.sha1(open(r"C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset", "rb").read()).hexdigest())
print("bak", hashlib.sha1(open(r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset", "rb").read()).hexdigest())
