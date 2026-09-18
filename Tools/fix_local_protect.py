"""Fix PlayerStart protection to use generator-local coordinates."""
import json, socket, time

BP = "BP_ProceduralTownGenerator"

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
    print(f"  C {label}: {'OK' if isinstance(r,dict) and 'source_node_id' in r else r}", flush=True)
    return r

# Find existing protect nodes
nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
get_actor = None
get_loc = None
brk = None
mk = None
add_ps = None
for n in nodes:
    title = n.get("title") or ""
    fn = n.get("function_name") or ""
    if fn == "GetActorOfClass" or "Get Actor Of Class" in title:
        get_actor = n["node_guid"]
    if fn == "K2_GetActorLocation" or title.startswith("Get Actor Location"):
        # may be more than one; prefer one near get_actor
        if get_loc is None or abs(n.get("pos_x",0)-560)<100:
            get_loc = n["node_guid"]
    if fn == "BreakVector" and abs(n.get("pos_x",0)-780)<80:
        brk = n["node_guid"]
    if fn == "MakeVector" and abs(n.get("pos_x",0)-1000)<80 and abs(n.get("pos_y",0)-240)<80:
        mk = n["node_guid"]

# Find protect Array_Add: the one between Clear and Main For
clear = None
main_for = "A3A2E7BC44AD85B25314158578E5AF9E"
for n in nodes:
    if n.get("function_name") == "Array_Clear" or n.get("title") == "Clear":
        clear = n["node_guid"]

# Trace Clear.then chain to find protect add
if clear:
    pins = send("get_node_pins", {"blueprint_name": BP, "node_id": clear})
    for p in pins.get("pins", []):
        if p["name"] == "then" and p.get("linked_to"):
            print("Clear.then", p["linked_to"])

# Find Array_Add whose then goes to Main For
for n in nodes:
    if n.get("function_name") == "Array_Add" or n.get("title") == "Add":
        pins = send("get_node_pins", {"blueprint_name": BP, "node_id": n["node_guid"]})
        for p in pins.get("pins", []):
            if p["name"] == "then":
                for l in p.get("linked_to") or []:
                    if l.get("node_id") == main_for:
                        add_ps = n["node_guid"]
                        print("Found protect Add", add_ps)

print("nodes", get_actor, get_loc, brk, mk, add_ps)

# Replace MakeVector path with: GetPlayerLoc - GetSelfLoc -> MakeVector Z=0
# Add Self GetActorLocation and Subtract_VectorVector

self_ref = nid(send("add_blueprint_self_reference", {"blueprint_name": BP, "node_position": [560, 400]}))
self_loc = nid(send("add_blueprint_function_node", {
    "blueprint_name": BP, "target": "Actor", "function_name": "K2_GetActorLocation",
    "node_position": [780, 400]
}))
sub = nid(send("add_blueprint_function_node", {
    "blueprint_name": BP, "target": "KismetMathLibrary", "function_name": "Subtract_VectorVector",
    "node_position": [1000, 320]
}))
print("self", self_ref, "self_loc", self_loc, "sub", sub)

# Disconnect old Break/Make from NewItem if needed; wire Subtract -> Break or directly Make from Subtract
# Simpler: PlayerLoc - SelfLoc = relative; then Break relative, MakeVector X,Y Z=0

connect(self_ref, "self", self_loc, "self", "self->selfLoc")

# Find player get_loc - the one connected from get_actor
# Re-find get_loc linked from get_actor ReturnValue
if get_actor:
    pins = send("get_node_pins", {"blueprint_name": BP, "node_id": get_actor})
    for p in pins.get("pins", []):
        if p["name"] == "ReturnValue":
            print("GetActor.ReturnValue ->", p.get("linked_to"))

# Disconnect MakeVector inputs from Break; connect Subtract to Break instead
if brk:
    send("disconnect_pin", {"blueprint_name": BP, "node_id": brk, "pin_name": "InVec"})
if mk:
    send("disconnect_pin", {"blueprint_name": BP, "node_id": mk, "pin_name": "X"})
    send("disconnect_pin", {"blueprint_name": BP, "node_id": mk, "pin_name": "Y"})

# Player world loc -> Subtract A; Self world loc -> Subtract B
connect(get_loc, "ReturnValue", sub, "A", "player->A")
connect(self_loc, "ReturnValue", sub, "B", "self->B")
# Check subtract pin names
sp = send("get_node_pins", {"blueprint_name": BP, "node_id": sub})
print("Sub pins", [(p["name"], p["direction"]) for p in sp.get("pins", [])])
# try A/B or V1/V2
for a_pin, b_pin in (("A","B"), ("V1","V2"), ("X","Y")):
    r1 = connect(get_loc, "ReturnValue", sub, a_pin, f"player->{a_pin}")
    r2 = connect(self_loc, "ReturnValue", sub, b_pin, f"self->{b_pin}")
    if isinstance(r1, dict) and "source_node_id" in r1:
        break

connect(sub, "ReturnValue", brk, "InVec", "rel->break")
connect(brk, "X", mk, "X", "X")
connect(brk, "Y", mk, "Y", "Y")
send("set_node_pin_default", {"blueprint_name": BP, "node_id": mk, "pin_name": "Z", "default_value": "0.0"})

# Ensure NewItem still from MakeVector
if add_ps and mk:
    connect(mk, "ReturnValue", add_ps, "NewItem", "localProtected->Add")

print("COMPILE", send("compile_blueprint", {"blueprint_name": BP}))

# Show generator + player for expected local protect point
actors = send("get_actors_in_level", {}).get("actors", [])
ps = next(a for a in actors if a.get("class")=="PlayerStart")
gen = next(a for a in actors if "ProceduralTown" in a.get("class",""))
plx,ply,_ = ps["location"]; gx,gy,_ = gen["location"]
print("Expected local protect XY", (plx-gx, ply-gy), "from world PS", ps["location"], "gen", gen["location"])
