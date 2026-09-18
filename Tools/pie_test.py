"""PIE verification: look for LostPackage actors in play world across runs."""
import json
import socket
import time
from collections import defaultdict

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
    return {"error": "empty"}


def summarize(actors):
    by_class = defaultdict(int)
    packages = []
    gens = []
    for a in actors:
        cls = a.get("class", "?")
        by_class[cls] += 1
        if "LostPackage" in cls or "LostPackage" in a.get("name", ""):
            packages.append(a)
        if "ProceduralTown" in cls:
            gens.append(a)
    return by_class, packages, gens


# Ensure meshes/compile ok first
print("compile gen", send("compile_blueprint", {"blueprint_name": "BP_ProceduralTownGenerator"}))
print("compile pkg", send("compile_blueprint", {"blueprint_name": "BP_LostPackage"}))

locations = []
for i in range(3):
    print(f"\n=== PIE {i+1} ===", flush=True)
    send("stop_play_in_editor", {})
    time.sleep(1)
    print("play", send("play_in_editor", {}))
    # wait for BeginPlay spawning
    time.sleep(5)
    actors = send("get_actors_in_level", {})
    print("from_play_world", actors.get("from_play_world"), "count", len(actors.get("actors", [])))
    by_class, packages, gens = summarize(actors.get("actors", []))
    print("classes sample", dict(list(by_class.items())[:15]))
    print("packages", [(p.get("name"), p.get("location")) for p in packages])
    print("generators", [(g.get("name"), g.get("location")) for g in gens])
    if packages:
        locations.append(tuple(packages[0].get("location") or []))
    send("stop_play_in_editor", {})
    time.sleep(2)

print("\nPACKAGE_LOCATIONS_ACROSS_RUNS", locations)
unique = len(set(locations))
print("UNIQUE_PACKAGE_LOCS", unique)
print("TEST_PACKAGE_SPAWNS", len(locations) >= 1)
print("TEST_PACKAGE_MOVES", unique >= 2 if len(locations) >= 2 else "insufficient_runs")
