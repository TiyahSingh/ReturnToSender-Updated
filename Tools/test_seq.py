import json, socket, time

def send(t, p=None, timeout=20):
    s = socket.socket(); s.settimeout(timeout); s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
    data = b""
    t0=time.time()
    while True:
        try:
            c = s.recv(65536)
        except Exception as e:
            print(t, "TIMEOUT/ERR", e, "elapsed", time.time()-t0)
            return None
        if not c:
            print(t, "CLOSED", data[:200]); return None
        data += c
        try:
            r = json.loads(data.decode())
            print(t, "OK", time.time()-t0, str(r)[:200])
            return r
        except Exception:
            pass

send("get_actors_in_level", {})
send("find_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_type":"All"})
send("delete_blueprint_nodes", {"blueprint_name":"BP_ProceduralTownGenerator","node_ids":["FA579263487AC0025B3C9B9D61AEB583"]})
send("add_blueprint_variable", {"blueprint_name":"BP_ProceduralTownGenerator","variable_name":"MinSpawnDistance","variable_type":"Float","default_value":"200.0","is_exposed":True})
