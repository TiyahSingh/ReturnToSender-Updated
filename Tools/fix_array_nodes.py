import json, socket, time

BP = "BP_ProceduralTownGenerator"
BEGIN = "38D207164FD12DF5F78EC6B35C9F85D4"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"
SET_MESH = "7221A4844CA81D97B3AE2B938CD87279"
SPAWN = "BAAEFA5B432AB0D8D80DBF95577F2923"

def send(t, p=None, timeout=60):
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

def nid(r):
    return r.get("node_id") if isinstance(r, dict) else None

def connect(src, spit, dst, dpin, label=""):
    r = send("connect_blueprint_nodes", {
        "blueprint_name": BP, "source_node_id": src, "source_pin": spit,
        "target_node_id": dst, "target_pin": dpin,
    })
    print(f"C {label}: {'OK' if isinstance(r,dict) and 'source_node_id' in r else r}", flush=True)
    return r

# Delete broken CallFunction array nodes
old = [
    "34DFDA084EA6FD47E0BC23ACF64F3265",  # Clear
    "75004589462661442518CCB528082153",  # Add trees
    "A4C7C5494B23E4B49813F3B6B20C1DD9",  # Add package
]
print("delete", send("delete_blueprint_nodes", {"blueprint_name": BP, "node_ids": old}))

# New Clear
g1 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [40, 360]}))
clr = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Clear", "node_position": [200, 360]}))
print("clear class", send("get_node_pins", {"blueprint_name": BP, "node_id": clr}).get("class"))
connect(BEGIN, "then", clr, "execute", "BP->Clear")
connect(g1, "SpawnedLocations", clr, "TargetArray", "arr->clear")
connect(clr, "then", MAIN_FOR, "execute", "Clear->For")

# New Add after SetStaticMesh
g2 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1600, 400]}))
g3 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1600, 480]}))
add1 = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Add", "node_position": [1800, 400]}))
print("add1 class", send("get_node_pins", {"blueprint_name": BP, "node_id": add1}).get("class"))
connect(SET_MESH, "then", add1, "execute", "Mesh->Add")
connect(g2, "SpawnedLocations", add1, "TargetArray", "arr")
connect(g3, "CandidateLocation", add1, "NewItem", "item")

# New Add after Spawn
g4 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1300, 1700]}))
g5 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1300, 1780]}))
add2 = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Add", "node_position": [1500, 1700]}))
connect(SPAWN, "then", add2, "execute", "Spawn->Add")
connect(g4, "SpawnedLocations", add2, "TargetArray", "arr2")
connect(g5, "CandidateLocation", add2, "NewItem", "item2")

# Check pin categories
for label, node in [("Clear", clr), ("Add1", add1), ("Add2", add2)]:
    pins = send("get_node_pins", {"blueprint_name": BP, "node_id": node})
    print(label, "class", pins.get("class"))
    for p in pins.get("pins", []):
        if p["name"] in ("TargetArray", "NewItem"):
            print(" ", p["name"], "cat", p.get("category"), "linked", bool(p.get("linked_to")))

print("COMPILE", send("compile_blueprint", {"blueprint_name": BP}))
time.sleep(1)
print("DONE", flush=True)
