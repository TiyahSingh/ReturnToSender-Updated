import json, socket, time, threading, math

def send(t, p=None, timeout=20):
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

def pie_capture():
    send("stop_play_in_editor", {})
    time.sleep(2)
    threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
    for t in range(25):
        time.sleep(1)
        a = send("get_actors_in_level", {})
        if a.get("from_play_world"):
            actors = a.get("actors") or []
            pkgs = [x for x in actors if "LostPackage" in str(x.get("class",""))]
            gens = [x for x in actors if "ProceduralTown" in str(x.get("class",""))]
            # try properties on generator for components
            props = None
            if gens:
                props = send("get_actor_properties", {"name": gens[0]["name"]})
            return {
                "n": len(actors),
                "pkgs": pkgs,
                "gens": gens,
                "props": props,
            }
    return None

results = []
for i in range(3):
    print(f"=== PIE {i+1} ===", flush=True)
    r = pie_capture()
    if not r:
        print("FAIL no play world", flush=True)
        continue
    pkgs = r["pkgs"]
    print("actors", r["n"], "packages", [(p.get("location"), p.get("scale")) for p in pkgs], flush=True)
    if pkgs:
        loc = pkgs[0]["location"]
        d = xy_dist((loc[0], loc[1]))
        print("package XY dist from PlayerStart XY(0,0):", round(d,2), "OK" if d >= 200 else "TOO_CLOSE", flush=True)
    # dump props keys if any
    props = r.get("props")
    if isinstance(props, dict):
        keys = list(props.keys())[:30]
        print("gen props keys sample", keys, flush=True)
        # search nested for relative location-like values
        s = json.dumps(props)
        if "StaticMesh" in s or "Relative" in s:
            print("props contain mesh/relative refs", flush=True)
    results.append(r)
    send("stop_play_in_editor", {})
    time.sleep(2)

pkg_locs = []
for r in results:
    for p in r.get("pkgs") or []:
        pkg_locs.append(tuple(p.get("location") or []))
print("PKG_LOCS", pkg_locs)
print("UNIQUE_PKGS", len(set(pkg_locs)))
print("ALL_PKGS_CLEAR", all(xy_dist((l[0], l[1])) >= 200 for l in pkg_locs) if pkg_locs else False)
print("ORIG_HASH_CHECK next")
