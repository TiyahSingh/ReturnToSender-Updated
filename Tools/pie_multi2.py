import json, socket, time, threading

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

def capture():
    send("stop_play_in_editor", {})
    time.sleep(2)
    threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
    for t in range(20):
        time.sleep(1)
        a = send("get_actors_in_level", {})
        if a.get("from_play_world"):
            pkgs = [x for x in (a.get("actors") or []) if "LostPackage" in str(x.get("class",""))]
            print("OK", "actors", len(a.get("actors") or []), "pkgs", [(p.get("location"), p.get("scale")) for p in pkgs], flush=True)
            loc = tuple(pkgs[0]["location"]) if pkgs else None
            send("stop_play_in_editor", {})
            time.sleep(2)
            return loc
    print("FAIL no play world", flush=True)
    send("stop_play_in_editor", {})
    return None

locs=[]
for i in range(3):
    print("===", i+1, flush=True)
    loc = capture()
    if loc: locs.append(loc)
print("LOCS", locs)
print("UNIQUE", len(set(round(x,1) for loc in locs for x in [loc])))  # wrong
print("UNIQUE_TUPLES", len(set(locs)))
