"""Insert PlayerStart protected location into SpawnedLocations after Clear, before main ForLoop.

Uses runtime PlayerStart X/Y with Z=0 so Vector_Distance on the spawn plane (Z=0)
correctly rejects candidates within MinSpawnDistance=200 of the player XY.
"""
import json
import socket
import time

BP = "BP_ProceduralTownGenerator"
BEGIN = "38D207164FD12DF5F78EC6B35C9F85D4"
CLEAR = "B35F5F914BF0BDAA7379D1BE05BB702D"
MAIN_FOR = "A3A2E7BC44AD85B25314158578E5AF9E"


def send(t, p=None, timeout=60):
    for attempt in range(3):
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
            return {"error": "empty"}
        except Exception as e:
            print("retry", t, e, flush=True)
            time.sleep(1)
    return {"error": "fail " + t}


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
    return r


def main():
    # Confirm PlayerStart in level
    actors = send("get_actors_in_level", {}).get("actors", [])
    starts = [a for a in actors if a.get("class") == "PlayerStart"]
    print("PLAYER_START", starts, flush=True)
    if not starts:
        raise SystemExit("No PlayerStart found in level")

    # Idempotency: if Clear already goes to something other than main ForLoop mentioning Player/GetActor, skip rebuild
    clear_pins = send("get_node_pins", {"blueprint_name": BP, "node_id": CLEAR})
    then_links = []
    for p in clear_pins.get("pins", []):
        if p["name"] == "then":
            then_links = p.get("linked_to") or []
    print("Clear.then ->", then_links, flush=True)

    already = any(
        "Player" in (l.get("node_title") or "")
        or "Get Actor" in (l.get("node_title") or "")
        or "Add" == (l.get("node_title") or "")
        for l in then_links
    )
    # If Clear already goes to an Add (our insert), don't duplicate
    if then_links and then_links[0].get("node_title") == "Add":
        print("Looks like protection Add may already be inserted; verifying...", flush=True)

    # Disconnect Clear -> MainFor so we can insert
    print(send("disconnect_pin", {"blueprint_name": BP, "node_id": CLEAR, "pin_name": "then"}), flush=True)

    # Layout near Clear (200,360)
    get_actor = nid(
        send(
            "add_blueprint_function_node",
            {
                "blueprint_name": BP,
                "target": "GameplayStatics",
                "function_name": "GetActorOfClass",
                "node_position": [320, 280],
            },
        )
    )
    print("GetActorOfClass", get_actor, flush=True)
    # Set class pin to PlayerStart
    # Try common pin names / defaults
    for pin_name, val in (
        ("ActorClass", "/Script/Engine.PlayerStart"),
        ("ActorClass", "PlayerStart"),
    ):
        r = send(
            "set_node_pin_default",
            {
                "blueprint_name": BP,
                "node_id": get_actor,
                "pin_name": pin_name,
                "default_value": val,
            },
        )
        print("set ActorClass", val, r, flush=True)

    get_loc = nid(
        send(
            "add_blueprint_function_node",
            {
                "blueprint_name": BP,
                "target": "Actor",
                "function_name": "K2_GetActorLocation",
                "node_position": [560, 280],
            },
        )
    )
    print("GetActorLocation", get_loc, flush=True)

    # Break vector to take X/Y; MakeVector with Z=0 for spawn-plane protection
    brk = nid(
        send(
            "add_blueprint_function_node",
            {
                "blueprint_name": BP,
                "target": "KismetMathLibrary",
                "function_name": "BreakVector",
                "node_position": [780, 240],
            },
        )
    )
    mk = nid(
        send(
            "add_blueprint_function_node",
            {
                "blueprint_name": BP,
                "target": "KismetMathLibrary",
                "function_name": "MakeVector",
                "node_position": [1000, 240],
            },
        )
    )
    send(
        "set_node_pin_default",
        {"blueprint_name": BP, "node_id": mk, "pin_name": "Z", "default_value": "0.0"},
    )

    g_spawned = nid(
        send(
            "add_blueprint_variable_get",
            {
                "blueprint_name": BP,
                "variable_name": "SpawnedLocations",
                "node_position": [1000, 360],
            },
        )
    )
    add_ps = nid(
        send(
            "add_blueprint_function_node",
            {
                "blueprint_name": BP,
                "target": "KismetArrayLibrary",
                "function_name": "Array_Add",
                "node_position": [1220, 320],
            },
        )
    )
    print("Array_Add PlayerStart protect", add_ps, flush=True)
    print(
        "Add class",
        send("get_node_pins", {"blueprint_name": BP, "node_id": add_ps}).get("class"),
        flush=True,
    )

    # Exec: Clear -> GetActorOfClass -> GetActorLocation -> Array_Add -> MainFor
    # GetActorLocation is often pure; GetActorOfClass may be pure too in some versions.
    # Check pins:
    for label, node in (("GetActor", get_actor), ("GetLoc", get_loc), ("Add", add_ps)):
        pins = send("get_node_pins", {"blueprint_name": BP, "node_id": node})
        print(
            label,
            [(p["name"], p["direction"], p.get("category")) for p in pins.get("pins", [])],
            flush=True,
        )

    # Wire based on whether nodes have exec pins
    get_actor_pins = send("get_node_pins", {"blueprint_name": BP, "node_id": get_actor})
    get_loc_pins = send("get_node_pins", {"blueprint_name": BP, "node_id": get_loc})
    actor_has_exec = any(p["name"] == "execute" for p in get_actor_pins.get("pins", []))
    loc_has_exec = any(p["name"] == "execute" for p in get_loc_pins.get("pins", []))

    if actor_has_exec:
        connect(CLEAR, "then", get_actor, "execute", "Clear->GetActor")
        if loc_has_exec:
            connect(get_actor, "then", get_loc, "execute", "GetActor->GetLoc")
            connect(get_loc, "then", add_ps, "execute", "GetLoc->Add")
        else:
            connect(get_actor, "then", add_ps, "execute", "GetActor->Add")
    else:
        # Pure GetActorOfClass: Clear directly to Array_Add
        connect(CLEAR, "then", add_ps, "execute", "Clear->AddProtect")

    connect(add_ps, "then", MAIN_FOR, "execute", "AddProtect->MainFor")

    # Data wires
    # ActorClass may need special handling - inspect after set
    class_pin = next(
        (p for p in get_actor_pins.get("pins", []) if "Class" in p["name"]), None
    )
    print("Class pin detail", class_pin, flush=True)

    # ReturnValue of GetActorOfClass -> self/target of GetActorLocation
    for tpin in ("self", "Target"):
        r = connect(get_actor, "ReturnValue", get_loc, tpin, f"actor->{tpin}")
        if isinstance(r, dict) and "source_node_id" in r:
            break

    connect(get_loc, "ReturnValue", brk, "InVec", "loc->break")
    # BreakVector pin names may be InVec or A
    if True:
        # try alternate if needed
        brk_pins = send("get_node_pins", {"blueprint_name": BP, "node_id": brk})
        print(
            "Break pins",
            [(p["name"], p["direction"]) for p in brk_pins.get("pins", [])],
            flush=True,
        )
        in_name = "InVec"
        for p in brk_pins.get("pins", []):
            if p["direction"] == "input" and p["name"] not in ("self",):
                in_name = p["name"]
                break
        # reconnect if needed
        connect(get_loc, "ReturnValue", brk, in_name, f"loc->{in_name}")

    connect(brk, "X", mk, "X", "X")
    connect(brk, "Y", mk, "Y", "Y")
    # Z stays 0.0 default

    connect(g_spawned, "SpawnedLocations", add_ps, "TargetArray", "arr")
    connect(mk, "ReturnValue", add_ps, "NewItem", "protected->NewItem")

    print("COMPILE", send("compile_blueprint", {"blueprint_name": BP}), flush=True)

    # Verify chain
    clear_pins2 = send("get_node_pins", {"blueprint_name": BP, "node_id": CLEAR})
    for p in clear_pins2.get("pins", []):
        if p["name"] == "then":
            print("Clear.then now ->", p.get("linked_to"), flush=True)
    add_pins = send("get_node_pins", {"blueprint_name": BP, "node_id": add_ps})
    for p in add_pins.get("pins", []):
        if p["name"] in ("execute", "then", "TargetArray", "NewItem"):
            print("ProtectAdd", p["name"], "->", p.get("linked_to"), "cat", p.get("category"), flush=True)

    # Actor class pin final
    get_actor_pins2 = send("get_node_pins", {"blueprint_name": BP, "node_id": get_actor})
    for p in get_actor_pins2.get("pins", []):
        if "Class" in p["name"]:
            print(
                "ActorClass default_object=",
                p.get("default_object"),
                "default_value=",
                p.get("default_value"),
                flush=True,
            )


if __name__ == "__main__":
    main()
