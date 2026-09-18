import json, socket, time
s = socket.socket(); s.settimeout(60)
try:
    s.connect(("127.0.0.1", 55557))
    s.sendall((json.dumps({"type":"get_actors_in_level","params":{}}) + "\n").encode())
    data = b""
    while True:
        c = s.recv(65536)
        if not c: break
        data += c
        try:
            r = json.loads(data.decode())
            print("RESP", str(r)[:500])
            break
        except Exception:
            pass
except Exception as e:
    print("ERR", type(e).__name__, e)
