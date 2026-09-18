import json, socket, time

def send(t, p=None, timeout=120):
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

PKG="BP_LostPackage"
print("scale", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "property_name": "RelativeScale3D", "property_value": [2.0, 2.0, 2.0]
}))
print("mesh overlap", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "PackageMesh",
    "property_name": "bGenerateOverlapEvents", "property_value": True
}))
# Collision enabled for query
print("sphere overlap", send("set_component_property", {
    "blueprint_name": PKG, "component_name": "OverlapSphere",
    "property_name": "bGenerateOverlapEvents", "property_value": True
}))
print("compile pkg", send("compile_blueprint", {"blueprint_name": PKG}))
print("compile gen", send("compile_blueprint", {"blueprint_name": "BP_ProceduralTownGenerator"}))

# Verify generator structure
nodes = send("find_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_type":"All"}).get("nodes",[])
print("GEN nodes", len(nodes))
need = ["MakeRotator","MakeVector","Array_Clear","ForEachLoop","Vector_Distance","Array_Add","SpawnActorFromClass"]
# Spawn might show as class not function
titles = [n.get("title","") for n in nodes]
fns = [n.get("function_name","") for n in nodes]
classes = [n.get("class","") for n in nodes]
print("has MakeRotator", "MakeRotator" in fns)
print("has MakeVector", fns.count("MakeVector"))
print("has Array_Clear", "Array_Clear" in fns)
print("has ForEach", "ForEachLoop" in fns)
print("has Distance", "Vector_Distance" in fns)
print("has Array_Add", "Array_Add" in fns)
print("has Spawn", any("Spawn" in t for t in titles) or "K2Node_SpawnActorFromClass" in classes)
print("has RandomFloat", fns.count("RandomFloatInRange"))

# Check BeginPlay chain
bp = send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":"38D207164FD12DF5F78EC6B35C9F85D4"})
print("BeginPlay", [p.get("linked_to") for p in bp.get("pins",[]) if p["name"]=="then"])
mf = send("get_node_pins", {"blueprint_name":"BP_ProceduralTownGenerator","node_id":"A3A2E7BC44AD85B25314158578E5AF9E"})
for pin in mf.get("pins",[]):
    if pin["name"] in ("LoopBody","Completed","execute"):
        print("MainFor."+pin["name"], pin.get("linked_to"))
