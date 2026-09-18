import json, socket

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

print("pins", send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":"38D207164FD12DF5F78EC6B35C9F85D4"}))
print("del", send("delete_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_ids":["FA579263487AC0025B3C9B9D61AEB583"]}, timeout=60))
