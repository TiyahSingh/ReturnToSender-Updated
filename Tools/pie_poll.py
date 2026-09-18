import json, socket, time

def send(t, p=None, timeout=30):
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

send("stop_play_in_editor", {})
time.sleep(1)
print("play", send("play_in_editor", {}))
for i in range(20):
    time.sleep(1)
    a = send("get_actors_in_level", {})
    print(i, "from_play", a.get("from_play_world"), "n", len(a.get("actors", [])),
          "pkg", [x.get("name") for x in a.get("actors", []) if "Lost" in x.get("name","") or "Package" in x.get("class","")])
send("stop_play_in_editor", {})
