import json, socket, time

def send(t, p=None, timeout=30):
    s = socket.socket(); s.settimeout(timeout); s.connect(("127.0.0.1", 55557))
    payload = json.dumps({"type": t, "params": p or {}}) + "\n"
    print("SEND", t, len(payload))
    s.sendall(payload.encode())
    data = b""
    t0 = time.time()
    while True:
        c = s.recv(65536)
        print("RECV", len(c), "elapsed", time.time()-t0)
        if not c: break
        data += c
        try:
            r = json.loads(data.decode())
            return r
        except Exception as e:
            print(" partial", e)

SMOKE = [
    "FA579263487AC0025B3C9B9D61AEB583",
    "50B48DB147935E0DA75CB3B38E0395E6",
    "DA79D65844735E9742A1A1B138B3B9DE",
]
print("RESULT", send("delete_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_ids":SMOKE}))
print("VAR", send("add_blueprint_variable", {"blueprint_name":"BP_ProceduralTownGenerator","variable_name":"MinSpawnDistance","variable_type":"Float","default_value":"200.000000","is_exposed":True}))
