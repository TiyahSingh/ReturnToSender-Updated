import json, socket
s = socket.socket(); s.settimeout(15); s.connect(("127.0.0.1", 55557))
s.sendall((json.dumps({"type": "ping", "params": {}}) + "\n").encode())
data = b""
while True:
    c = s.recv(65536)
    if not c: break
    data += c
    try:
        print(json.loads(data.decode()))
        break
    except Exception:
        pass
