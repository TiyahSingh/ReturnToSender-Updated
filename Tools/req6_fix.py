import json, socket

BP = "BP_ProceduralTownGenerator"

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

# Find Set CandidateLocation and ForEach
nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
set_cand = None
fe = None
for n in nodes:
    title = n.get("title") or ""
    if title.startswith("Set CandidateLocation") or (n.get("class")=="K2Node_VariableSet" and "Candidate" in title):
        # get pins to confirm
        p = send("get_node_pins", {"blueprint_name": BP, "node_id": n["node_guid"]})
        print("SET?", title, p.get("title"))
        if "CandidateLocation" in (p.get("title") or ""):
            set_cand = n["node_guid"]
    if n.get("function_name") == "ForEachLoop" or title == "For Each Loop":
        fe = n["node_guid"]
        print("FE", fe)

# More reliable: scan all VariableSet for CandidateLocation
for n in nodes:
    if n.get("class") == "K2Node_VariableSet":
        p = send("get_node_pins", {"blueprint_name": BP, "node_id": n["node_guid"]})
        if "CandidateLocation" in (p.get("title") or ""):
            then_links = [x for pin in p.get("pins",[]) if pin["name"]=="then" for x in pin.get("linked_to",[])]
            print("Candidate set", n["node_guid"], "then->", then_links)
            set_cand = n["node_guid"]

print("Connecting set_cand.then -> fe.Exec", set_cand, fe)
print(send("connect_blueprint_nodes", {
    "blueprint_name": BP,
    "source_node_id": set_cand,
    "source_pin": "then",
    "target_node_id": fe,
    "target_pin": "Exec",
}))

# Defaults
for prop, val in [("MinSpawnDistance", 200.0), ("MaxSpawnAttempts", 10), ("bFoundValidLocation", False), ("bTooClose", False)]:
    print(prop, send("set_blueprint_property", {"blueprint_name": BP, "property_name": prop, "property_value": val}))

print("compile", send("compile_blueprint", {"blueprint_name": BP}))

# Verify ForEach Exec linked
p = send("get_node_pins", {"blueprint_name": BP, "node_id": fe})
for pin in p.get("pins", []):
    if pin["name"] in ("Exec", "execute", "Array", "LoopBody", "Completed"):
        print(pin["name"], "->", pin.get("linked_to"))
