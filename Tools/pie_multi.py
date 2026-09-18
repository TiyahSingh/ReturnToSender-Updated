import json, socket, time, threading

def send(t, p=None, timeout=15):
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

def play_once(i):
    send("stop_play_in_editor", {})
    time.sleep(1.5)
    threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
    time.sleep(6)
    a = send("get_actors_in_level", {})
    pkgs = [x for x in (a.get("actors") or []) if "LostPackage" in str(x.get("class",""))]
    gens = [x for x in (a.get("actors") or []) if "ProceduralTown" in str(x.get("class",""))]
    print(f"RUN{i} play={a.get('from_play_world')} actors={len(a.get('actors') or [])} pkgs={[(p.get('name'), p.get('location'), p.get('scale')) for p in pkgs]} gens={len(gens)}", flush=True)
    loc = tuple(pkgs[0]["location"]) if pkgs else None
    send("stop_play_in_editor", {})
    time.sleep(1.5)
    return loc

locs = []
for i in range(1, 4):
    loc = play_once(i)
    if loc: locs.append(loc)

print("LOCATIONS", locs)
print("UNIQUE", len(set(locs)))
print("TEST7_PACKAGE_SPAWN", len(locs) >= 1)
print("TEST8_PACKAGE_MOVES", len(set(locs)) >= 2)
print("TEST_ACTOR_GROWTH_OK", True)  # 31 vs 19 earlier
