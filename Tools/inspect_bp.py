"""Inspect BP_ProceduralTownGenerator and smoke-test new MCP commands."""
import json, socket, sys

BP = "BP_ProceduralTownGenerator"

def send(t, p=None):
    s = socket.socket(); s.settimeout(90); s.connect(("127.0.0.1", 55557))
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

def main():
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get("nodes", [])
    print(f"NODE_COUNT={len(nodes)}")
    for n in nodes:
        fn = n.get("function_name") or n.get("event_name") or n.get("node_type") or "?"
        print(f"  {fn} guid={n.get('node_guid') or n.get('node_id')} pos=({n.get('pos_x')},{n.get('pos_y')}) pins={list((n.get('pins') or {}).keys())[:8]}")

    # Smoke test new commands on a disposable offset (do not connect)
    print("TEST branch", send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [-5000, -5000]}))
    print("TEST varget", send("add_blueprint_variable_get", {"blueprint_name": BP, "variable_name": "TreeMeshes", "node_position": [-5100, -5000]}))
    print("TEST macro", send("add_blueprint_macro", {"blueprint_name": BP, "macro_name": "ForLoop", "node_position": [-5200, -5000]}))

if __name__ == "__main__":
    main()
