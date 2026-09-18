"""Make BP_LostPackage walkable/collectable via CollectSphere overlap."""
import json
import socket
import time


BP = "BP_LostPackage"


def send(t, p=None, timeout=90):
    try:
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
    except Exception as e:
        return {"error": str(e)}


def nid(r):
    return r.get("node_id") if isinstance(r, dict) else None


def connect(src, spit, dst, dpin, label=""):
    r = send(
        "connect_blueprint_nodes",
        {
            "blueprint_name": BP,
            "source_node_id": src,
            "source_pin": spit,
            "target_node_id": dst,
            "target_pin": dpin,
        },
    )
    ok = isinstance(r, dict) and "source_node_id" in r
    print(f"  C {label}: {'OK' if ok else r}", flush=True)
    return ok


def main():
    print("ping", send("ping"), flush=True)
    print("comps", send("get_blueprint_components", {"blueprint_name": BP}), flush=True)

    # 1) Add CollectSphere (idempotent)
    add = send(
        "add_component_to_blueprint",
        {
            "blueprint_name": BP,
            "component_type": "SphereComponent",
            "component_name": "CollectSphere",
            "location": [0, 0, 40],
            "sphere_radius": 100,
        },
    )
    print("add sphere", add, flush=True)
    print("compile1", send("compile_blueprint", {"blueprint_name": BP}), flush=True)
    time.sleep(1)

    # 2) Collision: mesh no-block; sphere query+overlap pawn
    print(
        "mesh coll",
        send(
            "set_primitive_collision",
            {
                "blueprint_name": BP,
                "component_name": "PackageMesh",
                "collision_profile": "NoCollision",
                "collision_enabled": "NoCollision",
                "generate_overlap_events": False,
            },
        ),
        flush=True,
    )
    print(
        "sphere coll",
        send(
            "set_primitive_collision",
            {
                "blueprint_name": BP,
                "component_name": "CollectSphere",
                "collision_enabled": "QueryOnly",
                "generate_overlap_events": True,
                "pawn_response": "Overlap",
                "sphere_radius": 100,
            },
        ),
        flush=True,
    )
    print("compile2", send("compile_blueprint", {"blueprint_name": BP}), flush=True)
    time.sleep(1)

    # 3) Disconnect ActorBeginOverlap then-chain (avoid double fire)
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get(
        "nodes", []
    )
    actor_overlap = None
    print_node = None
    destroy_node = None
    for n in nodes:
        title = n.get("title") or ""
        fn = n.get("function_name") or ""
        if "ActorBeginOverlap" in title:
            actor_overlap = n["node_guid"]
        if fn == "PrintString" or title.startswith("Print String"):
            print_node = n["node_guid"]
        if fn == "K2_DestroyActor" or "Destroy Actor" in title:
            destroy_node = n["node_guid"]

    if actor_overlap:
        print(
            "disc actor",
            send(
                "disconnect_pin",
                {"blueprint_name": BP, "node_id": actor_overlap, "pin_name": "then"},
            ),
            flush=True,
        )

    # Ensure print text
    if print_node:
        send(
            "set_node_pin_default",
            {
                "blueprint_name": BP,
                "node_id": print_node,
                "pin_name": "InString",
                "default_value": "Package found!",
            },
        )
        send(
            "set_node_pin_default",
            {
                "blueprint_name": BP,
                "node_id": print_node,
                "pin_name": "bPrintToScreen",
                "default_value": "true",
            },
        )

    # 4) Component overlap event + once guard
    existing_bound = None
    for n in nodes:
        if "CollectSphere" in (n.get("title") or "") and "Overlap" in (n.get("title") or ""):
            existing_bound = n["node_guid"]

    if not existing_bound:
        ev = send(
            "add_blueprint_component_event",
            {
                "blueprint_name": BP,
                "component_name": "CollectSphere",
                "event_name": "OnComponentBeginOverlap",
                "node_position": [0, 600],
            },
        )
        print("bound", ev, flush=True)
        existing_bound = nid(ev)
    else:
        print("bound exists", existing_bound, flush=True)

    print(
        "var",
        send(
            "add_blueprint_variable",
            {
                "blueprint_name": BP,
                "variable_name": "bCollected",
                "variable_type": "Boolean",
                "is_exposed": False,
            },
        ),
        flush=True,
    )

    # Refresh nodes after adds
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get(
        "nodes", []
    )
    branch = None
    getb = None
    setb = None
    for n in nodes:
        title = n.get("title") or ""
        cls = n.get("class") or ""
        if cls.endswith("IfThenElse") or title == "Branch":
            if abs(n.get("pos_y", 0) - 600) < 200:
                branch = n["node_guid"]
        if "Get bCollected" in title or (
            title == "Get bCollected" or (title.endswith("bCollected") and "Get" in title)
        ):
            getb = n["node_guid"]
        if "Set bCollected" in title:
            setb = n["node_guid"]

    if not branch:
        branch = nid(
            send("add_blueprint_branch", {"blueprint_name": BP, "node_position": [220, 600]})
        )
    if not getb:
        getb = nid(
            send(
                "add_blueprint_variable_get",
                {
                    "blueprint_name": BP,
                    "variable_name": "bCollected",
                    "node_position": [40, 700],
                },
            )
        )
    if not setb:
        setb = nid(
            send(
                "add_blueprint_variable_set",
                {
                    "blueprint_name": BP,
                    "variable_name": "bCollected",
                    "node_position": [440, 600],
                },
            )
        )

    print("ids", existing_bound, branch, getb, setb, print_node, destroy_node, flush=True)

    if existing_bound and branch and getb and setb and print_node and destroy_node:
        connect(existing_bound, "then", branch, "execute", "ev->branch")
        # Condition pin may be named Condition
        connect(getb, "bCollected", branch, "Condition", "get->cond")
        connect(branch, "else", setb, "execute", "else->set")
        send(
            "set_node_pin_default",
            {
                "blueprint_name": BP,
                "node_id": setb,
                "pin_name": "bCollected",
                "default_value": "true",
            },
        )
        connect(setb, "then", print_node, "execute", "set->print")
        connect(print_node, "then", destroy_node, "execute", "print->destroy")

    print("compile3", send("compile_blueprint", {"blueprint_name": BP}), flush=True)
    print("comps final", send("get_blueprint_components", {"blueprint_name": BP}), flush=True)

    # Show final graph titles
    nodes = send("find_blueprint_nodes", {"blueprint_name": BP, "node_type": "All"}).get(
        "nodes", []
    )
    for n in nodes:
        print("NODE", (n.get("title") or "")[:70], flush=True)


if __name__ == "__main__":
    main()
