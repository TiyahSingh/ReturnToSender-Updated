"""Requirement 6: distance/collision prevention in BP_ProceduralTownGenerator."""
import json, socket, sys, time

BP = "BP_ProceduralTownGenerator"

# Existing node IDs
BEGIN = "38D207164FD12DF5F78EC6B35C9F85D4"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"
ADD_COMP = "4105BB2B41B6638EC11B34B85FE9A792"
SET_MESH = "7221A4844CA81D97B3AE2B938CD87279"
MAKE_TF = "8B86D4EA427CD3372B00C8B0EC212C6A"
RAND_X = "A0C6631E4EED711A6BFC4DA4EF24FCF6"
RAND_Y = "7E8EF3E840365BA7F606A5AE5D1CD15C"
# Smoke-test nodes to delete
SMOKE = [
    "FA579263487AC0025B3C9B9D61AEB583",
    "50B48DB147935E0DA75CB3B38E0395E6",
    "DA79D65844735E9742A1A1B138B3B9DE",
]

def send(t, p=None):
    s = socket.socket(); s.settimeout(120); s.connect(("127.0.0.1", 55557))
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

def nid(resp):
    if not isinstance(resp, dict):
        return None
    return resp.get("node_id") or resp.get("result", {}).get("node_id") if isinstance(resp.get("result"), dict) else resp.get("node_id")

def connect(src, spit, dst, dpin, label=""):
    r = send("connect_blueprint_nodes", {
        "blueprint_name": BP,
        "source_node_id": src,
        "source_pin": spit,
        "target_node_id": dst,
        "target_pin": dpin,
    })
    ok = isinstance(r, dict) and ("error" not in r or r.get("success"))
    # success responses often just have source/target ids
    err = r.get("error") if isinstance(r, dict) else r
    print(f"  CONNECT {label}: {src[:8]}:{spit} -> {dst[:8]}:{dpin} => {r if err else 'OK'}")
    return r

def add_fn(fn, target="KismetMathLibrary", pos=(0,0), params=None):
    p = {"blueprint_name": BP, "target": target, "function_name": fn, "node_position": list(pos)}
    if params: p["params"] = params
    r = send("add_blueprint_function_node", p)
    print(f"  ADD_FN {fn} => {r}")
    return nid(r), r

def add_macro(name, pos):
    r = send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": name, "node_position": list(pos)})
    print(f"  ADD_MACRO {name} => {r}")
    return nid(r), r

def add_branch(pos):
    r = send("add_blueprint_branch", {"blueprint_name": BP, "node_position": list(pos)})
    print(f"  ADD_BRANCH => {r}")
    return nid(r), r

def add_get(var, pos):
    r = send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": var, "node_position": list(pos)})
    print(f"  ADD_GET {var} => {r}")
    return nid(r), r

def add_set(var, pos, default=None):
    p = {"blueprint_name": BP, "variable_name": var, "node_position": list(pos)}
    if default is not None:
        p["default_value"] = default
    r = send("add_blueprint_variable_set", p)
    print(f"  ADD_SET {var} => {r}")
    return nid(r), r

def set_pin(node, pin, val):
    r = send("set_node_pin_default", {"blueprint_name": BP, "node_id": node, "pin_name": pin, "default_value": str(val)})
    print(f"  SET_PIN {node[:8]}.{pin}={val} => {r}")
    return r

def main():
    print("=== DELETE SMOKE NODES ===")
    print(send("delete_blueprint_nodes", {"blueprint_name": BP, "node_ids": SMOKE}))

    print("=== ADD VARIABLES ===")
    vars_spec = [
        ("SpawnedLocations", "VectorArray", None),
        ("CandidateLocation", "Vector", "0.000000,0.000000,0.000000"),
        ("MinSpawnDistance", "Float", "200.000000"),
        ("MaxSpawnAttempts", "Integer", "10"),
        ("bFoundValidLocation", "Boolean", "false"),
        ("bTooClose", "Boolean", "false"),
    ]
    # Check existing nodes for markers
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
    already = any(n.get("title","").startswith("Clear SpawnedLocations") or n.get("function_name")=="Array_Clear" for n in nodes)
    if already:
        print("Array_Clear already present - checking if Req6 partially done")

    for name, typ, default in vars_spec:
        p = {"blueprint_name": BP, "variable_name": name, "variable_type": typ, "is_exposed": True}
        if default is not None:
            p["default_value"] = default
        r = send("add_blueprint_variable", p)
        print(f"  VAR {name}: {r}")

    print("=== BUILD CLEAR AT BEGINPLAY ===")
    get_spawned_clear, _ = add_get("SpawnedLocations", (40, 360))
    clear_id, _ = add_fn("Array_Clear", "KismetArrayLibrary", (200, 360))
    connect(BEGIN, "then", clear_id, "execute", "BeginPlay->Clear")
    connect(get_spawned_clear, "SpawnedLocations", clear_id, "TargetArray", "Spawned->Clear")
    connect(clear_id, "then", MAIN_FOR, "execute", "Clear->MainFor")

    print("=== RETRY LOOP STRUCTURE ===")
    # Main loop body currently -> AddComponent. Reroute through validation.
    set_found_false, _ = add_set("bFoundValidLocation", (420, 300), "false")
    get_max_att, _ = add_get("MaxSpawnAttempts", (520, 380))
    retry_for, _ = add_macro("ForLoop", (600, 300))
    set_pin(retry_for, "FirstIndex", "1")
    connect(MAIN_FOR, "LoopBody", set_found_false, "execute", "MainBody->SetFoundFalse")
    connect(set_found_false, "then", retry_for, "execute", "SetFoundFalse->RetryFor")
    connect(get_max_att, "MaxSpawnAttempts", retry_for, "LastIndex", "MaxAttempts->LastIndex")

    # Inside retry: Branch if already found
    get_found1, _ = add_get("bFoundValidLocation", (780, 200))
    branch_skip, _ = add_branch((900, 280))
    connect(retry_for, "LoopBody", branch_skip, "execute", "RetryBody->BranchSkip")
    connect(get_found1, "bFoundValidLocation", branch_skip, "Condition", "Found->BranchSkip")

    # False path: attempt location
    set_too_close_false, _ = add_set("bTooClose", (1100, 360), "false")
    connect(branch_skip, "else", set_too_close_false, "execute", "NotFound->SetTooCloseFalse")

    # Make candidate vector from existing RandX/RandY
    loc_vec, _ = add_fn("MakeVector", "KismetMathLibrary", (-40, 640))
    set_pin(loc_vec, "Z", "0.0")
    # Disconnect old MakeTransform location links and reuse rands
    print(send("disconnect_pin", {"blueprint_name": BP, "node_id": MAKE_TF, "pin_name": "Location_X"}))
    print(send("disconnect_pin", {"blueprint_name": BP, "node_id": MAKE_TF, "pin_name": "Location_Y"}))
    connect(RAND_X, "ReturnValue", loc_vec, "X", "RandX->LocVec")
    connect(RAND_Y, "ReturnValue", loc_vec, "Y", "RandY->LocVec")

    set_candidate, _ = add_set("CandidateLocation", (1100, 480))
    connect(set_too_close_false, "then", set_candidate, "execute", "TooCloseFalse->SetCandidate")
    connect(loc_vec, "ReturnValue", set_candidate, "CandidateLocation", "LocVec->Candidate")

    # ForEach over SpawnedLocations
    get_spawned_fe, _ = add_get("SpawnedLocations", (1280, 560))
    foreach_id, _ = add_macro("ForEachLoop", (1400, 480))
    connect(set_candidate, "then", foreach_id, "execute", "SetCandidate->ForEach")
    connect(get_spawned_fe, "SpawnedLocations", foreach_id, "Array", "Spawned->ForEach")
    # ForEachLoop pin might be "Array" or "Map" - check and fix if needed

    get_candidate_dist, _ = add_get("CandidateLocation", (1480, 640))
    dist_id, _ = add_fn("Vector_Distance", "KismetMathLibrary", (1680, 640))
    connect(get_candidate_dist, "CandidateLocation", dist_id, "V1", "Cand->Dist")
    connect(foreach_id, "Array Element", dist_id, "V2", "Elem->Dist")  # pin name may vary

    get_min_dist, _ = add_get("MinSpawnDistance", (1680, 760))
    less_id, _ = add_fn("Less_DoubleDouble", "KismetMathLibrary", (1880, 700))
    # fallback Less_FloatFloat if needed
    connect(dist_id, "ReturnValue", less_id, "A", "Dist->Less")
    connect(get_min_dist, "MinSpawnDistance", less_id, "B", "Min->Less")

    branch_close, _ = add_branch((2080, 640))
    connect(foreach_id, "LoopBody", branch_close, "execute", "ForEachBody->BranchClose")
    connect(less_id, "ReturnValue", branch_close, "Condition", "Less->BranchClose")
    set_too_close_true, _ = add_set("bTooClose", (2280, 600), "true")
    connect(branch_close, "then", set_too_close_true, "execute", "TooCloseTrue")

    # After ForEach Completed: if not too close, found valid
    get_too_close, _ = add_get("bTooClose", (1400, 820))
    branch_ok, _ = add_branch((1600, 820))
    connect(foreach_id, "Completed", branch_ok, "execute", "ForEachDone->BranchOk")
    connect(get_too_close, "bTooClose", branch_ok, "Condition", "TooClose->BranchOk")
    set_found_true, _ = add_set("bFoundValidLocation", (1800, 900), "true")
    # If NOT too close (else), set found true
    connect(branch_ok, "else", set_found_true, "execute", "NotTooClose->FoundTrue")

    print("=== AFTER RETRY: SPAWN IF VALID ===")
    get_found2, _ = add_get("bFoundValidLocation", (600, 520))
    branch_spawn, _ = add_branch((750, 520))
    connect(retry_for, "Completed", branch_spawn, "execute", "RetryDone->BranchSpawn")
    connect(get_found2, "bFoundValidLocation", branch_spawn, "Condition", "Found->BranchSpawn")
    connect(branch_spawn, "then", ADD_COMP, "execute", "Valid->AddComponent")

    # CandidateLocation -> MakeTransform Location
    get_cand_tf, _ = add_get("CandidateLocation", (40, 768))
    connect(get_cand_tf, "CandidateLocation", MAKE_TF, "Location", "Cand->MakeTF.Location")

    # After SetStaticMesh, Array_Add CandidateLocation to SpawnedLocations
    get_spawned_add, _ = add_get("SpawnedLocations", (1600, 400))
    get_cand_add, _ = add_get("CandidateLocation", (1600, 480))
    add_arr, _ = add_fn("Array_Add", "KismetArrayLibrary", (1800, 400))
    connect(SET_MESH, "then", add_arr, "execute", "SetMesh->ArrayAdd")
    connect(get_spawned_add, "SpawnedLocations", add_arr, "TargetArray", "Spawned->ArrayAdd")
    connect(get_cand_add, "CandidateLocation", add_arr, "NewItem", "Cand->ArrayAdd")

    print("=== COMPILE ===")
    comp = send("compile_blueprint", {"blueprint_name": BP})
    print("COMPILE", comp)

    # Dump pins for ForEach to verify pin names if compile failed
    nodes2 = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
    print("NODE_COUNT", len(nodes2))
    for n in nodes2:
        if n.get("function_name") in ("ForEachLoop", "Array_Clear", "Array_Add", "Vector_Distance") or "Branch" in (n.get("title") or "") or "ForEach" in (n.get("title") or ""):
            print(" ", n.get("title"), n.get("node_guid"), n.get("class"))

if __name__ == "__main__":
    main()
