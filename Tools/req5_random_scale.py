"""Requirement 5: random uniform scale 0.8-1.2 into MakeTransform Scale."""
import json, socket, sys

BP = "BP_ProceduralTownGenerator"

def send(t, p):
    s = socket.socket(); s.settimeout(60); s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p}) + "\n").encode())
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

def main():
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
    make_tf = next(n for n in nodes if n.get("function_name") == "MakeTransform")
    # Detect if scale already wired: look for MakeVector near MakeTransform used for scale
    # We'll add a dedicated MakeVector at make_tf + offset for scale
    already_scale = any(
        n.get("function_name") == "MakeVector" and abs(int(n.get("pos_y", 0)) - (int(make_tf["pos_y"]) + 200)) < 80
        for n in nodes
    )
    if already_scale:
        print("Scale MakeVector already present")
    else:
        x = int(make_tf["pos_x"]) - 420
        y = int(make_tf["pos_y"]) + 220
        srand = send("add_blueprint_function_node", {
            "blueprint_name": BP,
            "target": "KismetMathLibrary",
            "function_name": "RandomFloatInRange",
            "params": {"Min": 0.8, "Max": 1.2},
            "node_position": [x, y],
        })
        svec = send("add_blueprint_function_node", {
            "blueprint_name": BP,
            "target": "KismetMathLibrary",
            "function_name": "MakeVector",
            "node_position": [x + 220, y],
        })
        print("ADD scale rand", srand)
        print("ADD MakeVector", svec)
        sid = srand.get("node_id")
        vid = svec.get("node_id")
        # Force pin defaults in case params missed (UE5 Real pins)
        print("Min", send("set_node_pin_default", {"blueprint_name": BP, "node_id": sid, "pin_name": "Min", "default_value": "0.8"}))
        print("Max", send("set_node_pin_default", {"blueprint_name": BP, "node_id": sid, "pin_name": "Max", "default_value": "1.2"}))
        for axis in ("X", "Y", "Z"):
            print(f"connect {axis}", send("connect_blueprint_nodes", {
                "blueprint_name": BP,
                "source_node_id": sid,
                "source_pin": "ReturnValue",
                "target_node_id": vid,
                "target_pin": axis,
            }))
        print("connect Scale", send("connect_blueprint_nodes", {
            "blueprint_name": BP,
            "source_node_id": vid,
            "source_pin": "ReturnValue",
            "target_node_id": make_tf["node_guid"],
            "target_pin": "Scale",
        }))

    print("compile", send("compile_blueprint", {"blueprint_name": BP}))
    nodes2 = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
    has_vec = any(n.get("function_name") == "MakeVector" for n in nodes2)
    has_rot = any(n.get("function_name") == "MakeRotator" for n in nodes2)
    rands = sum(1 for n in nodes2 if n.get("function_name") == "RandomFloatInRange")
    print("VERIFY MakeVector", has_vec, "MakeRotator", has_rot, "RandomFloat count", rands)
    if has_vec and has_rot and rands >= 4:
        print("REQ5_OK")
    else:
        print("REQ5_INCOMPLETE")
        sys.exit(1)

if __name__ == "__main__":
    main()
