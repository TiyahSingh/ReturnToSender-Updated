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

nodes = send("find_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_type":"All"}).get("nodes",[])
for n in nodes:
    fn = n.get("function_name") or ""
    if fn in ("Array_Clear","Array_Add","ForEachLoop","Vector_Distance") or "Spawn" in (n.get("title") or ""):
        print("\n===", n.get("title"), n.get("node_guid"), n.get("class"))
        pins = send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":n["node_guid"]})
        for p in pins.get("pins",[]):
            print(f"  {p['direction']:6} {p['name']:20} cat={p.get('category')} sub={p.get('subcategory')} links={p.get('linked_to')}")
