import json, socket, time

PKG = "BP_LostPackage"
BP = "BP_ProceduralTownGenerator"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"
MESH = "/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"
EV = "63D1FF314A8CDBF2E51CF78F6FD0CAC0"

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

def nid(r):
    return r.get("node_id") if isinstance(r, dict) else None

def connect(bp, src, spit, dst, dpin, label=""):
    r = send("connect_blueprint_nodes", {
        "blueprint_name": bp, "source_node_id": src, "source_pin": spit,
        "target_node_id": dst, "target_pin": dpin,
    })
    print(f"  C {label}: {r if isinstance(r,dict) and ('error' in r or 'Failed' in str(r)) else 'OK'}", flush=True)
    return r

print("1 scale", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "property_name": "RelativeScale3D", "property_value": [2.0, 2.0, 2.0]
}), flush=True)

print("2 mesh again", send("set_static_mesh_properties", {
    "blueprint_name": PKG, "component_name": "PackageMesh", "static_mesh": MESH
}), flush=True)

print("3 print", flush=True)
pr = send("add_blueprint_function_node", {
    "blueprint_name": PKG, "target": "KismetSystemLibrary", "function_name": "PrintString",
    "node_position": [280, 0]
})
print(pr, flush=True)
print_id = nid(pr)
if print_id:
    print(send("set_node_pin_default", {"blueprint_name": PKG, "node_id": print_id, "pin_name": "InString", "default_value": "Package found!"}), flush=True)

print("4 self", flush=True)
self_id = nid(send("add_blueprint_self_reference", {"blueprint_name": PKG, "node_position": [280, 120]}))
print("self", self_id, flush=True)

print("5 destroy", flush=True)
# DestroyActor via GameplayStatics? Better: call function on Actor
destroy = nid(send("add_blueprint_function_node", {
    "blueprint_name": PKG, "target": "Actor", "function_name": "K2_DestroyActor",
    "node_position": [560, 0]
}))
print("destroy", destroy, flush=True)

if print_id:
    connect(PKG, EV, "then", print_id, "execute", "overlap->print")
if print_id and destroy:
    connect(PKG, print_id, "then", destroy, "execute", "print->destroy")
if self_id and destroy:
    # Target pin may be "self"
    connect(PKG, self_id, "self", destroy, "self", "self->destroy")

print("6 compile pkg", send("compile_blueprint", {"blueprint_name": PKG}), flush=True)
print("PKG_EVENT_OK", flush=True)
