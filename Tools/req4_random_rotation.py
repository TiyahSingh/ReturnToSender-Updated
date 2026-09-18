"""Implement Requirement 4 (random yaw) on BP_ProceduralTownGenerator via UnrealMCP TCP."""
import json
import socket
import time
import sys

HOST = "127.0.0.1"
PORT = 55557
BP = "BP_ProceduralTownGenerator"


def send(cmd_type, params, timeout=60):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((HOST, PORT))
    payload = json.dumps({"type": cmd_type, "params": params}) + "\n"
    s.sendall(payload.encode("utf-8"))
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
        try:
            obj = json.loads(data.decode("utf-8"))
            s.close()
            return obj
        except json.JSONDecodeError:
            continue
    s.close()
    return {"status": "error", "error": "no json", "raw": data.decode("utf-8", "replace")}


def wait_port(seconds=180):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            s = socket.create_connection((HOST, PORT), timeout=2)
            s.close()
            return True
        except OSError:
            time.sleep(3)
    return False


def unwrap(resp):
    if isinstance(resp, dict) and "result" in resp and isinstance(resp["result"], dict):
        return resp["result"]
    return resp


def main():
    if not wait_port():
        print("FAIL: MCP port not listening")
        sys.exit(1)

    # Harmless inspect
    begin = unwrap(send("find_blueprint_nodes", {
        "blueprint_name": BP,
        "node_type": "Event",
        "event_name": "ReceiveBeginPlay",
    }))
    print("BEGINPLAY:", json.dumps(begin)[:500])

    nodes = unwrap(send("find_blueprint_nodes", {
        "blueprint_name": BP,
        "node_type": "All",
    }))
    node_list = nodes.get("nodes", [])
    print("ALL NODES count:", len(node_list))
    make_tf = None
    for n in node_list:
        title = n.get("title", "")
        fname = n.get("function_name", "")
        print(f"  {n.get('class')} | {fname} | {title} | {n.get('node_guid')} @ ({n.get('pos_x')},{n.get('pos_y')})")
        if "MakeTransform" in fname or "Make Transform" in title:
            make_tf = n

    if not make_tf:
        print("FAIL: MakeTransform not found")
        sys.exit(2)

    print("FOUND MakeTransform:", make_tf["node_guid"])

    # Skip if already has random rotation wired (look for MakeRotator)
    already = any("MakeRotator" in (n.get("function_name") or "") or "Make Rotator" in (n.get("title") or "") for n in node_list)
    if already:
        print("MakeRotator already present — compiling/saving only")
    else:
        x = int(make_tf.get("pos_x", 0)) - 420
        y = int(make_tf.get("pos_y", 0)) + 120

        rand = unwrap(send("add_blueprint_function_node", {
            "blueprint_name": BP,
            "target": "KismetMathLibrary",
            "function_name": "RandomFloatInRange",
            "params": {"Min": 0.0, "Max": 360.0},
            "node_position": [x, y],
        }))
        print("ADD RandomFloatInRange:", json.dumps(rand)[:800])

        rot = unwrap(send("add_blueprint_function_node", {
            "blueprint_name": BP,
            "target": "KismetMathLibrary",
            "function_name": "MakeRotator",
            "node_position": [x + 220, y],
        }))
        print("ADD MakeRotator:", json.dumps(rot)[:800])

        rand_id = None
        rot_id = None
        if isinstance(rand, dict):
            rand_id = rand.get("node_id") or rand.get("node_guid")
        if isinstance(rot, dict):
            rot_id = rot.get("node_id") or rot.get("node_guid")

        # Re-find if IDs missing — pick newest MakeRotator / the RandomFloat near MakeTransform
        nodes2 = unwrap(send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}))
        randoms = []
        for n in nodes2.get("nodes", []):
            fname = n.get("function_name") or ""
            if "MakeRotator" in fname:
                rot_id = n["node_guid"]
            if "RandomFloatInRange" in fname:
                randoms.append(n)
        if not rand_id:
            # Prefer random node near MakeTransform rotation area (pos_y around make_tf+120)
            target_y = int(make_tf.get("pos_y", 0)) + 120
            randoms_sorted = sorted(randoms, key=lambda n: abs(int(n.get("pos_y", 0)) - target_y))
            # Prefer ones not at the original location random positions (-176, 784/896)
            candidates = [n for n in randoms_sorted if abs(int(n.get("pos_x", 0)) - x) < 200]
            if candidates:
                rand_id = candidates[0]["node_guid"]
            elif randoms_sorted:
                # last resort: the one closest in Y that isn't one of the two original location nodes
                originals = {"7E8EF3E840365BA7F606A5AE5D1CD15C", "A0C6631E4EED711A6BFC4DA4EF24FCF6"}
                for n in randoms_sorted:
                    if n["node_guid"] not in originals:
                        rand_id = n["node_guid"]
                        break

        print("rand_id", rand_id, "rot_id", rot_id, "tf", make_tf["node_guid"])
        if not rand_id or not rot_id:
            print("FAIL: could not resolve node ids")
            print(json.dumps(rand, indent=2)[:1000])
            print(json.dumps(rot, indent=2)[:1000])
            sys.exit(3)

        c1 = unwrap(send("connect_blueprint_nodes", {
            "blueprint_name": BP,
            "source_node_id": rand_id,
            "source_pin": "ReturnValue",
            "target_node_id": rot_id,
            "target_pin": "Z",
        }))
        print("CONNECT yaw:", json.dumps(c1)[:500])

        # Try Z then Yaw pin names
        if c1.get("status") == "error" or c1.get("success") is False or c1.get("error"):
            c1b = unwrap(send("connect_blueprint_nodes", {
                "blueprint_name": BP,
                "source_node_id": rand_id,
                "source_pin": "ReturnValue",
                "target_node_id": rot_id,
                "target_pin": "Yaw",
            }))
            print("CONNECT yaw alt:", json.dumps(c1b)[:500])

        c2 = unwrap(send("connect_blueprint_nodes", {
            "blueprint_name": BP,
            "source_node_id": rot_id,
            "source_pin": "ReturnValue",
            "target_node_id": make_tf["node_guid"],
            "target_pin": "Rotation",
        }))
        print("CONNECT rotation:", json.dumps(c2)[:500])

    # Compile
    compile_resp = unwrap(send("compile_blueprint", {"blueprint_name": BP}))
    print("COMPILE:", json.dumps(compile_resp)[:500])

    # Verify nodes present
    verify = unwrap(send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}))
    has_rot = any("MakeRotator" in (n.get("function_name") or "") for n in verify.get("nodes", []))
    # Count RandomFloatInRange — should be >= 3 after Req4 (2 location + 1 yaw)
    rand_count = sum(1 for n in verify.get("nodes", []) if "RandomFloatInRange" in (n.get("function_name") or ""))
    print("VERIFY MakeRotator:", has_rot, "RandomFloatInRange count:", rand_count)
    if has_rot and rand_count >= 3:
        print("REQ4_NODES_OK")
    else:
        print("REQ4_NODES_INCOMPLETE")
        sys.exit(4)


if __name__ == "__main__":
    main()
