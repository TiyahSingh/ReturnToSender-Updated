"""Inspect PlayerStart and BeginPlay Clear->ForLoop chain."""
import json
import socket

BP = "BP_ProceduralTownGenerator"


def send(t, p=None, timeout=45):
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
    data = b""
    while True:
        c = s.recv(65536)
        if not c:
            break
        data += c
        try:
            return json.loads(data.decode()).get("result", json.loads(data.decode()))
        except Exception:
            pass


actors = send("get_actors_in_level", {}).get("actors", [])
starts = [a for a in actors if "PlayerStart" in a.get("class", "") or "PlayerStart" in a.get("name", "")]
print("PLAYER_STARTS", starts)
for a in actors:
    if "Procedural" in a.get("name", "") or "Town" in a.get("class", ""):
        print("GENERATOR", a)

# BeginPlay chain
bp = send("get_node_pins", {"blueprint_name": BP, "node_id": "38D207164FD12DF5F78EC6B35C9F85D4"})
print("BeginPlay.then", [p.get("linked_to") for p in bp.get("pins", []) if p["name"] == "then"])

nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
for n in nodes:
    fn = n.get("function_name") or ""
    title = n.get("title") or ""
    if fn in ("Array_Clear", "Array_Add") or "Clear" in title or title.startswith("Add") and "Static" not in title:
        pins = send("get_node_pins", {"blueprint_name": BP, "node_id": n["node_guid"]})
        print("\nNODE", title, n.get("class"), n["node_guid"], "pos", n.get("pos_x"), n.get("pos_y"))
        for p in pins.get("pins", []):
            if p.get("linked_to") or p["name"] in ("execute", "then", "TargetArray", "NewItem"):
                print(" ", p["direction"], p["name"], "->", p.get("linked_to"))
