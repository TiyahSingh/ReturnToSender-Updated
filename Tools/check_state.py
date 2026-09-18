import json, socket

def send(t, p=None, timeout=45):
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

# Check generator
nodes = send("find_blueprint_nodes", {"blueprint_name": "BP_ProceduralTownGenerator", "node_type": "All"}).get("nodes", [])
print("GEN NODES", len(nodes))
fns = {}
for n in nodes:
    k = n.get("function_name") or n.get("class") or "?"
    fns[k] = fns.get(k, 0) + 1
print("counts", fns)
bp = send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":"38D207164FD12DF5F78EC6B35C9F85D4"})
print("BeginPlay.then", [p.get("linked_to") for p in bp.get("pins",[]) if p["name"]=="then"])

# Check package exists
pkg = send("find_blueprint_nodes", {"blueprint_name": "BP_LostPackage", "node_type": "All"})
print("PKG", pkg if isinstance(pkg, dict) and pkg.get("error") else f"nodes={len(pkg.get('nodes',[]))}")
if pkg.get("nodes"):
    for n in pkg["nodes"]:
        print(" ", n.get("title"), n.get("class"), n.get("node_guid"))
