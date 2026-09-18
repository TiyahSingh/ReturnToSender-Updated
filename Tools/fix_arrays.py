import json, socket, time

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

BP="BP_ProceduralTownGenerator"
# Reconnect Array_Clear and both Array_Adds to force type propagation
pairs = [
    ("5A4C5FA04A0DA2B2140102901190F955", "SpawnedLocations", "34DFDA084EA6FD47E0BC23ACF64F3265", "TargetArray"),
    ("C1DD0F774685B37CCC732092AB1EC7FC", "SpawnedLocations", "75004589462661442518CCB528082153", "TargetArray"),
    ("8F1ED0A947C36B3F5B2B68820284C15E", "CandidateLocation", "75004589462661442518CCB528082153", "NewItem"),
    ("8C015461410D92FFB3361DABCC87DE57", "SpawnedLocations", "A4C7C5494B23E4B49813F3B6B20C1DD9", "TargetArray"),
    ("A9567961472816584885229D9FAE7673", "CandidateLocation", "A4C7C5494B23E4B49813F3B6B20C1DD9", "NewItem"),
]
for src, spit, dst, dpin in pairs:
    print("reconnect", spit, "->", dpin, send("connect_blueprint_nodes", {
        "blueprint_name": BP, "source_node_id": src, "source_pin": spit,
        "target_node_id": dst, "target_pin": dpin
    }))

# Ensure spawn class still set
print("spawn class pin", send("get_node_pins", {"blueprint_name": BP, "node_id": "BAAEFA5B432AB0D8D80DBF95577F2923"}).get("pins",[])[2:4])

comp = send("compile_blueprint", {"blueprint_name": BP})
print("COMPILE", comp)
time.sleep(1)
# Check clear pin category after
pins = send("get_node_pins", {"blueprint_name": BP, "node_id": "34DFDA084EA6FD47E0BC23ACF64F3265"})
for p in pins.get("pins",[]):
    if p["name"]=="TargetArray":
        print("Clear.TargetArray cat=", p.get("category"), p.get("subcategory"), "links", p.get("linked_to"))
pins = send("get_node_pins", {"blueprint_name": BP, "node_id": "75004589462661442518CCB528082153"})
for p in pins.get("pins",[]):
    if p["name"] in ("TargetArray","NewItem"):
        print("Add."+p["name"], "cat=", p.get("category"), "links", bool(p.get("linked_to")))
