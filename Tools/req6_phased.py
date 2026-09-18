"""Requirement 6 - phased, robust."""
import json, socket, sys, time

BP = "BP_ProceduralTownGenerator"
BEGIN = "38D207164FD12DF5F78EC6B35C9F85D4"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"
ADD_COMP = "4105BB2B41B6638EC11B34B85FE9A792"
SET_MESH = "7221A4844CA81D97B3AE2B938CD87279"
MAKE_TF = "8B86D4EA427CD3372B00C8B0EC212C6A"
RAND_X = "A0C6631E4EED711A6BFC4DA4EF24FCF6"
RAND_Y = "7E8EF3E840365BA7F606A5AE5D1CD15C"

def send(t, p=None, timeout=45):
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
                    r = json.loads(data.decode())
                    return r.get("result", r)
                except Exception:
                    pass
            return {"error": "empty", "raw": data.decode(errors="replace")[:300]}
        except Exception as e:
            print(f"  RETRY {t} attempt {attempt+1}: {e}", flush=True)
            time.sleep(1)
    return {"error": f"failed {t}"}

def nid(r):
    return r.get("node_id") if isinstance(r, dict) else None

def connect(src, spit, dst, dpin, label=""):
    r = send("connect_blueprint_nodes", {
        "blueprint_name": BP, "source_node_id": src, "source_pin": spit,
        "target_node_id": dst, "target_pin": dpin,
    })
    print(f"  C {label}: {r if (isinstance(r,dict) and r.get('error')) else 'OK'}", flush=True)
    return r

def pins(node):
    return send("get_node_pins", {"blueprint_name": BP, "node_id": node})

def main():
    print("=== VARS ===", flush=True)
    for name, typ, default in [
        ("SpawnedLocations", "VectorArray", None),
        ("CandidateLocation", "Vector", "0.000000,0.000000,0.000000"),
        ("MinSpawnDistance", "Float", "200.000000"),
        ("MaxSpawnAttempts", "Integer", "10"),
        ("bFoundValidLocation", "Boolean", "false"),
        ("bTooClose", "Boolean", "false"),
    ]:
        p = {"blueprint_name": BP, "variable_name": name, "variable_type": typ, "is_exposed": True}
        if default is not None: p["default_value"] = default
        print(" ", name, send("add_blueprint_variable", p), flush=True)

    # Check if already wired
    bpins = pins(BEGIN)
    then_links = []
    for p in bpins.get("pins", []):
        if p["name"] == "then":
            then_links = p.get("linked_to") or []
    print("BeginPlay.then ->", then_links, flush=True)
    if any("Array_Clear" in (l.get("node_title") or "") or "Clear" in (l.get("node_title") or "") for l in then_links):
        print("ALREADY_HAS_CLEAR - abort to avoid duplicates", flush=True)
        return

    print("=== CLEAR ===", flush=True)
    g1 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [40, 360]}))
    clr = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Clear", "node_position": [200, 360]}))
    print("ids", g1, clr, flush=True)
    connect(BEGIN, "then", clr, "execute", "BP->Clear")
    connect(g1, "SpawnedLocations", clr, "TargetArray", "arr->clear")
    connect(clr, "then", MAIN_FOR, "execute", "Clear->For")

    print("=== RETRY SETUP ===", flush=True)
    set_ff = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [420, 300], "default_value": "false"}))
    gmax = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "MaxSpawnAttempts", "node_position": [520, 380]}))
    retry = nid(send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": "ForLoop", "node_position": [600, 300]}))
    send("set_node_pin_default", {"blueprint_name": BP, "node_id": retry, "pin_name": "FirstIndex", "default_value": "1"})
    connect(MAIN_FOR, "LoopBody", set_ff, "execute", "Main->SetFF")
    connect(set_ff, "then", retry, "execute", "SetFF->Retry")
    connect(gmax, "MaxSpawnAttempts", retry, "LastIndex", "Max->Last")

    print("=== SKIP BRANCH ===", flush=True)
    gfound = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [780, 200]}))
    bskip = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [900, 280]}))
    connect(retry, "LoopBody", bskip, "execute", "Retry->BSkip")
    connect(gfound, "bFoundValidLocation", bskip, "Condition", "Found->BSkip")

    set_tcf = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [1100, 360], "default_value": "false"}))
    connect(bskip, "else", set_tcf, "execute", "else->TCF")

    print("=== CANDIDATE LOC ===", flush=True)
    locv = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "MakeVector", "node_position": [-40, 640]}))
    send("set_node_pin_default", {"blueprint_name": BP, "node_id": locv, "pin_name": "Z", "default_value": "0.0"})
    send("disconnect_pin", {"blueprint_name": BP, "node_id": MAKE_TF, "pin_name": "Location_X"})
    send("disconnect_pin", {"blueprint_name": BP, "node_id": MAKE_TF, "pin_name": "Location_Y"})
    connect(RAND_X, "ReturnValue", locv, "X", "X")
    connect(RAND_Y, "ReturnValue", locv, "Y", "Y")
    set_cand = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1100, 480]}))
    connect(set_tcf, "then", set_cand, "execute", "TCF->Cand")
    connect(locv, "ReturnValue", set_cand, "CandidateLocation", "Vec->Cand")

    print("=== FOREACH DISTANCE ===", flush=True)
    gsp = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1280, 560]}))
    fe = nid(send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": "ForEachLoop", "node_position": [1400, 480]}))
    print("ForEach pins:", json.dumps(pins(fe), indent=None)[:800], flush=True)
    connect(set_cand, "then", fe, "execute", "Cand->FE")
    # try common pin names for array input
    for apin in ("Array", "Map", "TargetArray", "InArray"):
        r = connect(gsp, "SpawnedLocations", fe, apin, f"arr->{apin}")
        if isinstance(r, dict) and not r.get("error") and "Failed" not in str(r):
            if "source_node_id" in r or r.get("success", True):
                break

    gcand = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1480, 640]}))
    dist = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Vector_Distance", "node_position": [1680, 640]}))
    print("Dist pins:", [(p["name"], p["direction"]) for p in pins(dist).get("pins", [])], flush=True)
    connect(gcand, "CandidateLocation", dist, "V1", "V1")
    # Array Element pin
    for ep in ("Array Element", "ArrayElement", "Element", "Item"):
        r = connect(fe, ep, dist, "V2", f"elem->{ep}")
        if isinstance(r, dict) and "source_node_id" in r:
            break

    gmin = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "MinSpawnDistance", "node_position": [1680, 760]}))
    less = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Less_DoubleDouble", "node_position": [1880, 700]}))
    if not less:
        less = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Less_FloatFloat", "node_position": [1880, 700]}))
    print("Less pins:", [(p["name"], p["direction"]) for p in pins(less).get("pins", [])], flush=True)
    connect(dist, "ReturnValue", less, "A", "A")
    connect(gmin, "MinSpawnDistance", less, "B", "B")

    bclose = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [2080, 640]}))
    connect(fe, "LoopBody", bclose, "execute", "FE->BClose")
    connect(less, "ReturnValue", bclose, "Condition", "Less->BClose")
    set_tct = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [2280, 600], "default_value": "true"}))
    connect(bclose, "then", set_tct, "execute", "close->true")

    gtc = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bTooClose", "node_position": [1400, 820]}))
    bok = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [1600, 820]}))
    connect(fe, "Completed", bok, "execute", "FEDone->BOk")
    connect(gtc, "bTooClose", bok, "Condition", "TC->BOk")
    set_ft = nid(send("add_blueprint_variable_set", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [1800, 900], "default_value": "true"}))
    connect(bok, "else", set_ft, "execute", "notClose->found")

    print("=== SPAWN BRANCH ===", flush=True)
    gfound2 = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "bFoundValidLocation", "node_position": [600, 520]}))
    bspawn = nid(send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [750, 520]}))
    connect(retry, "Completed", bspawn, "execute", "RetryDone->BSpawn")
    connect(gfound2, "bFoundValidLocation", bspawn, "Condition", "Found->BSpawn")
    connect(bspawn, "then", ADD_COMP, "execute", "Valid->Add")

    gcandtf = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [40, 768]}))
    connect(gcandtf, "CandidateLocation", MAKE_TF, "Location", "Cand->Loc")

    gspa = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "SpawnedLocations", "node_position": [1600, 400]}))
    gcadda = nid(send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "CandidateLocation", "node_position": [1600, 480]}))
    aadd = nid(send("add_blueprint_function_node", {"blueprint_name": BP, "target": "KismetArrayLibrary", "function_name": "Array_Add", "node_position": [1800, 400]}))
    print("Array_Add pins:", [(p["name"], p["direction"]) for p in pins(aadd).get("pins", [])], flush=True)
    connect(SET_MESH, "then", aadd, "execute", "Mesh->Add")
    connect(gspa, "SpawnedLocations", aadd, "TargetArray", "arr")
    connect(gcadda, "CandidateLocation", aadd, "NewItem", "item")

    print("=== COMPILE ===", flush=True)
    print(send("compile_blueprint", {"blueprint_name": BP}, timeout=90), flush=True)
    print("REQ6_PHASE1_DONE", flush=True)

if __name__ == "__main__":
    main()
