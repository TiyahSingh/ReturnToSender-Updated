import json, socket, time

def send(t, p=None, timeout=30):
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

for cmd in [
    "open /Game/ThirdPerson/Lvl_ThirdPerson",
    "Open /Game/ThirdPerson/Lvl_ThirdPerson.Lvl_ThirdPerson",
]:
    print("CMD", cmd, send("execute_console_command", {"command": cmd}))
    time.sleep(12)
    a = send("get_actors_in_level", {})
    print(" n", len(a.get("actors") or []), "play", a.get("from_play_world"))
    for x in (a.get("actors") or [])[:25]:
        print(" ", x.get("class"), x.get("name"), x.get("location"))
    starts=[x for x in (a.get("actors") or []) if "PlayerStart" in str(x.get("class"))]
    print(" starts", starts)
    if starts:
        break
