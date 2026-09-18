import json, socket

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

# Known important nodes from previous dump
ids = {
  "BeginPlay": "38D207164FD12DF5F78EC6B35C9F85D4",
  "ForLoop": "A3A2E7BC44AD85B25314158578E5AF9E",
  "AddComponent": "4105BB2B41B6638EC11B34B85FE9A792",
  "SetStaticMesh": "7221A4844CA81D97B3AE2B938CD87279",
  "MakeTransform": "8B86D4EA427CD3372B00C8B0EC212C6A",
  "Array_Random": "5DF340CD4DF06DCDD36EF9ABC2E5060E",
  "RandX": "A0C6631E4EED711A6BFC4DA4EF24FCF6",
  "RandY": "7E8EF3E840365BA7F606A5AE5D1CD15C",
  "MakeRotator": "1D00FC194985814E2F93DAB83227A90C",
  "MakeVectorScale": "474D8BA841BA8BFC858F2A934922A715",
}
for name, nid in ids.items():
    pins = send("get_node_pins", {"blueprint_name": BP, "node_id": nid})
    print("====", name, pins.get("title"), pins.get("class"))
    for p in pins.get("pins", []):
        links = p.get("linked_to") or []
        if links or p.get("default_value") or p["name"] in ("then","execute","LoopBody","Completed","Location","Rotation","Scale","ReturnValue","Target","NewMesh","RelativeTransform","FirstIndex","LastIndex","Index"):
            link_s = ", ".join(f"{l['node_title']}:{l['pin']}" for l in links) if links else "-"
            print(f"  {p['direction']:6} {p['name']:28} def={p.get('default_value','')!r:20} -> {link_s}")
