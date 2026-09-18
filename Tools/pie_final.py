import json, socket, time

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

print("compile pkg", send("compile_blueprint", {"blueprint_name":"BP_LostPackage"}))
print("mesh", send("set_static_mesh_properties", {
    "blueprint_name":"BP_LostPackage","component_name":"PackageMesh",
    "static_mesh":"/Game/AssetsvilleTown/Meshes/StreetProps/SM_carton_box"
}))

locs=[]
for i in range(3):
    send("stop_play_in_editor", {})
    time.sleep(1)
    print(f"PIE{i+1}", send("play_in_editor", {}))
    # poll up to 15s for play world
    pkgs=[]
    for t in range(15):
        time.sleep(1)
        a=send("get_actors_in_level", {})
        if a.get("from_play_world"):
            pkgs=[x for x in a.get("actors",[]) if "LostPackage" in x.get("class","") or "LostPackage" in x.get("name","")]
            print(" t",t,"play",True,"actors",len(a.get("actors",[])),"pkgs",[(p.get("name"),p.get("location")) for p in pkgs])
            break
        if t in (4,9,14):
            print(" t",t,"play",a.get("from_play_world"),"n",len(a.get("actors",[])))
    if pkgs:
        locs.append(tuple(pkgs[0].get("location") or []))
    send("stop_play_in_editor", {})
    time.sleep(1.5)
print("LOCS", locs)
print("SPAWNED", len(locs)>=1, "MOVED", len(set(locs))>=2 if len(locs)>=2 else "n/a")
