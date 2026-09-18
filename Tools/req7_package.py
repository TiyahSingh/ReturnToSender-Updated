"""Requirement 7: BP_LostPackage + procedural spawn after main loop."""
import json, socket, time

BP = "BP_ProceduralTownGenerator"
PKG = "BP_LostPackage"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"
MESH = "/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"

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
            return {"error": "empty"}
        except Exception as e:
            print("RETRY", t, e, flush=True); time.sleep(1)
    return {"error": "fail "+t}

def nid(r):
    return r.get("node_id") if isinstance(r, dict) else None

def connect(src, spit, dst, dpin, label=""):
    r = send("connect_blueprint_nodes", {
        "blueprint_name": BP, "source_node_id": src, "source_pin": spit,
        "target_node_id": dst, "target_pin": dpin,
    })
    print(f"  C {label}: {'OK' if isinstance(r,dict) and 'error' not in str(r.get('error','')) and 'Failed' not in str(r) else r}", flush=True)
    return r

def pins(bp, node):
    return send("get_node_pins", {"blueprint_name": bp, "node_id": node})

print("=== CREATE BP_LostPackage ===", flush=True)
print(send("create_blueprint", {"name": PKG, "parent_class": "Actor", "path": "/Game/Procedural/"}), flush=True)
print(send("add_component_to_blueprint", {
    "blueprint_name": PKG, "component_type": "StaticMeshComponent", "component_name": "PackageMesh"
}), flush=True)
print(send("set_static_mesh_properties", {
    "blueprint_name": PKG, "component_name": "PackageMesh", "static_mesh": MESH
}), flush=True)
# scale
print(send("set_component_property", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "property_name": "RelativeScale3D", "property_value": {"x": 2.0, "y": 2.0, "z": 2.0}
}), flush=True)

print(send("add_component_to_blueprint", {
    "blueprint_name": PKG, "component_type": "SphereComponent", "component_name": "OverlapSphere"
}), flush=True)
print(send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "bGenerateOverlapEvents", "property_value": True
}), flush=True)
# Sphere radius
print(send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "SphereRadius", "property_value": 80.0
}), flush=True)

# Event graph: ActorBeginOverlap -> PrintString -> DestroyActor
print("=== PKG EVENT GRAPH ===", flush=True)
# Try different event names
ev = None
for ename in ("ReceiveActorBeginOverlap", "ActorBeginOverlap", "ReceiveActorBeginOverlap"):
    r = send("add_blueprint_event_node", {"blueprint_name": PKG, "event_name": ename, "node_position": [0, 0]})
    print("event", ename, r, flush=True)
    if r and r.get("node_id") and "error" not in r:
        ev = r.get("node_id"); break

print_id = nid(send("add_blueprint_function_node", {
    "blueprint_name": PKG, "target": "KismetSystemLibrary", "function_name": "PrintString",
    "node_position": [300, 0], "params": {"InString": "Package found!"}
}))
# force string
send("set_node_pin_default", {"blueprint_name": PKG, "node_id": print_id, "pin_name": "InString", "default_value": "Package found!"})
destroy = nid(send("add_blueprint_function_node", {
    "blueprint_name": PKG, "target": "Actor", "function_name": "K2_DestroyActor",
    "node_position": [600, 0]
}))
if not destroy:
    destroy = nid(send("add_blueprint_function_node", {
        "blueprint_name": PKG, "target": "self", "function_name": "K2_DestroyActor",
        "node_position": [600, 0]
    }))

if ev and print_id:
    send("connect_blueprint_nodes", {"blueprint_name": PKG, "source_node_id": ev, "source_pin": "then", "target_node_id": print_id, "target_pin": "execute"})
if print_id and destroy:
    send("connect_blueprint_nodes", {"blueprint_name": PKG, "source_node_id": print_id, "source_pin": "then", "target_node_id": destroy, "target_pin": "execute"})

print("compile pkg", send("compile_blueprint", {"blueprint_name": PKG}), flush=True)

print("=== SPAWN PACKAGE AFTER MAIN LOOP ===", flush=True)
# Check Main For Completed links
mp = pins(BP, MAIN_FOR)
for pin in mp.get("pins", []):
    if pin["name"] == "Completed":
        print("MainFor.Completed ->", pin.get("linked_to"), flush=True)

# Build package spawn validation (similar to tree spawn)
set_ff = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [400, 1100], "default_value": "false"}))
gmax = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "MaxSpawnAttempts", "node_position": [500, 1180]}))
retry = nid(send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": "ForLoop", "node_position": [600, 1100]}))
send("set_node_pin_default", {"blueprint_name": BP, "node_id": retry, "pin_name": "FirstIndex", "default_value": "1"})
connect(MAIN_FOR, "Completed", set_ff, "execute", "MainDone->SetFF")
connect(set_ff, "then", retry, "execute", "SetFF->Retry")
connect(gmax, "MaxSpawnAttempts", retry, "LastIndex", "Max->Last")

gfound = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [780, 1000]}))
bskip = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [900, 1080]}))
connect(retry, "LoopBody", bskip, "execute", "Retry->BSkip")
connect(gfound, "bFoundValidLocation", bskip, "Condition", "Found->Cond")

set_tcf = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [1100, 1160], "default_value": "false"}))
connect(bskip, "else", set_tcf, "execute", "else->TCF")

# New randoms for package location
rx = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "RandomFloatInRange", "node_position": [900, 1300], "params": {"Min": -1500, "Max": 1500}}))
ry = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "RandomFloatInRange", "node_position": [900, 1400], "params": {"Min": -1500, "Max": 1500}}))
send("set_node_pin_default", {"blueprint_name": BP, "node_id": rx, "pin_name": "Min", "default_value": "-1500.0"})
send("set_node_pin_default", {"blueprint_name": BP, "node_id": rx, "pin_name": "Max", "default_value": "1500.0"})
send("set_node_pin_default", {"blueprint_name": BP, "node_id": ry, "pin_name": "Min", "default_value": "-1500.0"})
send("set_node_pin_default", {"blueprint_name": BP, "node_id": ry, "pin_name": "Max", "default_value": "1500.0"})
locv = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "MakeVector", "node_position": [1120, 1320]}))
send("set_node_pin_default", {"blueprint_name": BP, "node_id": locv, "pin_name": "Z", "default_value": "0.0"})
connect(rx, "ReturnValue", locv, "X", "rx")
connect(ry, "ReturnValue", locv, "Y", "ry")
set_cand = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1300, 1200]}))
connect(set_tcf, "then", set_cand, "execute", "TCF->Cand")
connect(locv, "ReturnValue", set_cand, "CandidateLocation", "Vec->Cand")

gsp = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1400, 1400]}))
fe = nid(send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": "ForEachLoop", "node_position": [1500, 1200]}))
connect(set_cand, "then", fe, "Exec", "Cand->FE")
connect(gsp, "SpawnedLocations", fe, "Array", "arr->FE")

gcand = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1600, 1400]}))
dist = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Vector_Distance", "node_position": [1800, 1400]}))
connect(gcand, "CandidateLocation", dist, "V1", "V1")
connect(fe, "Array Element", dist, "V2", "V2")
gmin = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "MinSpawnDistance", "node_position": [1800, 1520]}))
less = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Less_DoubleDouble", "node_position": [2000, 1450]}))
connect(dist, "ReturnValue", less, "A", "A")
connect(gmin, "MinSpawnDistance", less, "B", "B")
bclose = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [2200, 1380]}))
connect(fe, "LoopBody", bclose, "execute", "FE->B")
connect(less, "ReturnValue", bclose, "Condition", "Less->B")
set_tct = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [2400, 1340], "default_value": "true"}))
connect(bclose, "then", set_tct, "execute", "true")

gtc = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [1500, 1550]}))
bok = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [1700, 1550]}))
connect(fe, "Completed", bok, "execute", "FEDone")
connect(gtc, "bTooClose", bok, "Condition", "TC")
set_ft = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [1900, 1620], "default_value": "true"}))
connect(bok, "else", set_ft, "execute", "found")

# After retry: if found, SpawnActor
gfound2 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [600, 1600]}))
bspawn = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [750, 1600]}))
connect(retry, "Completed", bspawn, "execute", "RetryDone")
connect(gfound2, "bFoundValidLocation", bspawn, "Condition", "Found")

spawn = nid(send("add_blueprint_spawn_actor_from_class", {
    "blueprint_name": BP,
    "actor_class": "/Game/Procedural/BP_LostPackage.BP_LostPackage",
    "node_position": [1000, 1700]
}))
print("SPAWN NODE", spawn, flush=True)
print("Spawn pins:", [(p["name"], p["direction"]) for p in pins(BP, spawn).get("pins", [])], flush=True)
connect(bspawn, "then", spawn, "execute", "Valid->Spawn")

# Transform: MakeTransform from CandidateLocation, scale 2,2,2
gcandt = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [700, 1850]}))
mt = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "MakeTransform", "node_position": [900, 1850]}))
sv = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "MakeVector", "node_position": [700, 1980]}))
send("set_node_pin_default", {"blueprint_name": BP, "node_id": sv, "pin_name": "X", "default_value": "2.0"})
send("set_node_pin_default", {"blueprint_name": BP, "node_id": sv, "pin_name": "Y", "default_value": "2.0"})
send("set_node_pin_default", {"blueprint_name": BP, "node_id": sv, "pin_name": "Z", "default_value": "2.0"})
connect(gcandt, "CandidateLocation", mt, "Location", "Loc")
connect(sv, "ReturnValue", mt, "Scale", "Scale")
# SpawnActor usually has SpawnTransform pin
connect(mt, "ReturnValue", spawn, "SpawnTransform", "TF")

# Add location to SpawnedLocations after spawn
gspa = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1300, 1700]}))
gcadda = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1300, 1780]}))
aadd = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Add", "node_position": [1500, 1700]}))
connect(spawn, "then", aadd, "execute", "Spawn->Add")
connect(gspa, "SpawnedLocations", aadd, "TargetArray", "arr")
connect(gcadda, "CandidateLocation", aadd, "NewItem", "item")

print("=== COMPILE BOTH ===", flush=True)
print("pkg", send("compile_blueprint", {"blueprint_name": PKG}), flush=True)
print("gen", send("compile_blueprint", {"blueprint_name": BP}), flush=True)
print("REQ7_DONE", flush=True)
