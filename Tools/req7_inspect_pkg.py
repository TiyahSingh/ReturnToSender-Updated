import json, socket, time

def send(t, p=None, timeout=60):
    for attempt in range(3):
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
            return {"error":"empty"}
        except Exception as e:
            print("retry", e); time.sleep(2)
    return {"error":"fail"}

PKG="BP_LostPackage"
nodes = send("find_blueprint_nodes", {"blueprint_name": PKG, "node_type": "All"}).get("nodes", [])
print("PKG nodes", len(nodes))
for n in nodes:
    print(" ", n.get("title"), n.get("class"), n.get("function_name"), n.get("node_guid"))
    p = send("get_node_pins", {"blueprint_name": PKG, "node_id": n["node_guid"]})
    for pin in p.get("pins", []):
        if pin.get("linked_to") or pin["name"] in ("then","execute","InString","self"):
            print("   ", pin["name"], "->", pin.get("linked_to"), "def=", pin.get("default_value"))

print("COMPILE", send("compile_blueprint", {"blueprint_name": PKG}))
