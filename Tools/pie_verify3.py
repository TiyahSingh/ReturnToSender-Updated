"""Stable PIE verification for PlayerStart protection."""
import json
import socket
import time
import threading
import math
import hashlib


def send(t, p=None, timeout=60):
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


def xy(a, b=(0, 0)):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def main():
    print("load", send("load_level", {"path": "/Game/ThirdPerson/Lvl_ThirdPerson"}), flush=True)
    time.sleep(12)
    a = send("get_actors_in_level", {})
    print("n", len(a.get("actors") or []), flush=True)
    starts = [x for x in (a.get("actors") or []) if x.get("class") == "PlayerStart"]
    gens = [x for x in (a.get("actors") or []) if "ProceduralTown" in x.get("class", "")]
    print("PS", starts, flush=True)
    print("GEN", gens, flush=True)
    print("compile", send("compile_blueprint", {"blueprint_name": "BP_ProceduralTownGenerator"}), flush=True)

    results = []
    for i in range(3):
        print("PIE", i + 1, flush=True)
        send("stop_play_in_editor", {})
        time.sleep(2)
        threading.Thread(target=lambda: send("play_in_editor", {}), daemon=True).start()
        time.sleep(8)
        a = None
        for _ in range(12):
            a = send("get_actors_in_level", {})
            if a.get("from_play_world"):
                break
            time.sleep(1)
        print(
            " play",
            a.get("from_play_world") if a else None,
            "n",
            len((a or {}).get("actors") or []),
            flush=True,
        )
        if a and a.get("from_play_world"):
            actors = a.get("actors") or []
            pkgs = [x for x in actors if "LostPackage" in str(x.get("class", ""))]
            gens = [x for x in actors if "ProceduralTown" in str(x.get("class", ""))]
            comps = (
                ((send("get_actor_components", {"name": gens[0]["name"]}) or {}).get("components") if gens else [])
                or []
            )
            meshes = []
            for c in comps:
                if "StaticMesh" not in c.get("class", ""):
                    continue
                if c.get("name") in ("DefaultSceneRoot", "Root", "RootComponent"):
                    continue
                w = c.get("world_location") or [0, 0, 0]
                meshes.append((c.get("name"), w, xy((w[0], w[1]))))
            too = [(n, [round(x, 1) for x in w], round(d, 1)) for n, w, d in meshes if d < 200]
            closes = 0
            for i1 in range(len(meshes)):
                for i2 in range(i1 + 1, len(meshes)):
                    if (
                        xy(
                            (meshes[i1][1][0], meshes[i1][1][1]),
                            (meshes[i2][1][0], meshes[i2][1][1]),
                        )
                        < 200
                    ):
                        closes += 1
            pkgd = []
            for p in pkgs:
                loc = p.get("location") or [0, 0, 0]
                pkgd.append(([round(v, 1) for v in loc], round(xy((loc[0], loc[1])), 1)))
            print(
                "  meshes",
                len(meshes),
                "too_close",
                too,
                "pairs",
                closes,
                "pkgs",
                pkgd,
                flush=True,
            )
            results.append({"too": len(too), "meshes": len(meshes), "pairs": closes, "pkgs": pkgd})
        send("stop_play_in_editor", {})
        time.sleep(2)

    print("RESULTS", results, flush=True)
    print(
        "PASS_TREES",
        all(r["too"] == 0 and r["meshes"] > 0 for r in results) if results else False,
        flush=True,
    )
    print("PASS_PAIRS", all(r["pairs"] == 0 for r in results) if results else False, flush=True)
    print(
        "PASS_PKG",
        all(len(r["pkgs"]) >= 1 and all(d >= 200 for _, d in r["pkgs"]) for r in results)
        if results
        else False,
        flush=True,
    )
    print(
        "UNIQUE_PKG",
        len(set(tuple(p[0]) for r in results for p in r["pkgs"])),
        flush=True,
    )
    print(
        "orig",
        hashlib.sha1(
            open(
                r"C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset",
                "rb",
            ).read()
        ).hexdigest(),
        flush=True,
    )
    print(
        "bak",
        hashlib.sha1(
            open(
                r"C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset",
                "rb",
            ).read()
        ).hexdigest(),
        flush=True,
    )


if __name__ == "__main__":
    main()
