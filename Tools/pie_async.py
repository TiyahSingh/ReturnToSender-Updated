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

# fire play in background thread so hang doesn't block
def do_play():
    print("play_resp", send("play_in_editor", {}, timeout=5), flush=True)

th = threading.Thread(target=do_play, daemon=True)
th.start()
time.sleep(8)
for i in range(12):
    a = send("get_actors_in_level", {}, timeout=10)
    pkgs = [x for x in (a.get("actors") or []) if "LostPackage" in str(x.get("class",""))+str(x.get("name",""))]
    print(i, "playworld", a.get("from_play_world"), "n", len(a.get("actors") or []), "pkgs", pkgs[:3], flush=True)
    if a.get("from_play_world") and pkgs:
        break
    time.sleep(1)

# Check latest log for undetermined after latest compile
print("stop", send("stop_play_in_editor", {}, timeout=10))
