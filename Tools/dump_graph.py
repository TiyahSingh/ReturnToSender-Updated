"""Dump full node titles/classes and pin connections for BP_ProceduralTownGenerator."""
import json, socket

BP = "BP_ProceduralTownGenerator"

def send(t, p=None):
    s = socket.socket(); s.settimeout(90); s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
    data = b""
    while True:
        c = s.recv(65536)
        if not c: break
        data += c
        try:
            r = json.loads(data.decode())
            return r.get("result", r)
        except Exception:
            pass

nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
# sort by x then y
nodes.sort(key=lambda n: (n.get("pos_x", 0), n.get("pos_y", 0)))
print(f"TOTAL={len(nodes)}")
for n in nodes:
    print(f"{n.get('pos_x'):6} {n.get('pos_y'):6} | {n.get('class'):30} | {n.get('title'):40} | fn={n.get('function_name')} | {n.get('node_guid')}")
