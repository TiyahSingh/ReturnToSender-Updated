import json, socket, time, threading, math, hashlib

def send(t, p=None, timeout=20):
    try:
        s = socket.socket(); s.settimeout(timeout); s.connect(("127.0.0.1", 55557))
        s.sendall((json.dumps({"type": t, "params": p or {}}) + "\n").encode())
        data = b""
        while True:
            c = s.recv(65536)
            if not c: break
            data += c
            try:
                return json.loads(data.decode()).get("result", json.loads(data.decode()))
            except Exception:
                pass
    except Exception as e:
        return {"error": str(e)}

def xy_dist(a, b=(0.0, 0.0)):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def sha1(p):
    h=hashlib.sha1()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20), b''): h.update(c)
    return h.hexdigest()

# ensure level
a=send('get_actors_in_level',{})
if not any(x.get('class')=='PlayerStart' for x in (a.get('actors') or [])):
    print(send('load_level',{'path':'/Game/ThirdPerson/Lvl_ThirdPerson'})); time.sleep(8)

ps_xy=(0.0,0.0)
starts=[x for x in send('get_actors_in_level',{}).get('actors',[]) if x.get('class')=='PlayerStart']
if starts: ps_xy=(starts[0]['location'][0], starts[0]['location'][1])
print('PS', starts, 'xy', ps_xy)

pkg_locs=[]; tree_ok=[]; pair_ok=[]; details=[]
for i in range(3):
    print('===', i+1, flush=True)
    send('stop_play_in_editor',{})
    time.sleep(2)
    threading.Thread(target=lambda: send('play_in_editor',{}), daemon=True).start()
    time.sleep(8)
    a=None
    for t in range(15):
        a=send('get_actors_in_level',{})
        if a.get('from_play_world'):
            break
        time.sleep(1)
    if not a or not a.get('from_play_world'):
        print('no play world', a.get('from_play_world') if a else None, 'n', len((a or {}).get('actors') or []))
        tree_ok.append(False); pair_ok.append(False)
        send('stop_play_in_editor',{}); time.sleep(2); continue
    actors=a.get('actors') or []
    pkgs=[x for x in actors if 'LostPackage' in str(x.get('class',''))]
    gens=[x for x in actors if 'ProceduralTown' in str(x.get('class',''))]
    comps=(send('get_actor_components',{'name':gens[0]['name']}).get('components') if gens else []) or []
    meshes=[]
    for c in comps:
        if 'StaticMesh' not in c.get('class',''): continue
        if c.get('name') in ('DefaultSceneRoot','Root','RootComponent'): continue
        w=c.get('world_location') or [0,0,0]
        meshes.append((c.get('name'), w, xy_dist((w[0],w[1]), ps_xy)))
    too=[m for m in meshes if m[2]<200]
    closes=[]
    for i1 in range(len(meshes)):
        for i2 in range(i1+1,len(meshes)):
            d=xy_dist((meshes[i1][1][0],meshes[i1][1][1]),(meshes[i2][1][0],meshes[i2][1][1]))
            if d<200: closes.append(d)
    pkg_info=[]
    for p in pkgs:
        loc=p.get('location') or [0,0,0]
        d=xy_dist((loc[0],loc[1]), ps_xy)
        pkg_info.append(( [round(v,1) for v in loc], round(d,1), d>=200))
        pkg_locs.append(tuple(loc))
    print('meshes', len(meshes), 'too_close', [(n,[round(x,1) for x in w],round(d,1)) for n,w,d in too], 'pairs', len(closes), 'pkgs', pkg_info, flush=True)
    tree_ok.append(len(too)==0 and len(meshes)>0)
    pair_ok.append(len(closes)==0)
    details.append({'meshes':len(meshes),'too':len(too),'pairs':len(closes),'pkgs':len(pkgs)})
    send('stop_play_in_editor',{}); time.sleep(2)

print('SUMMARY tree_ok', tree_ok, all(tree_ok))
print('SUMMARY pair_ok', pair_ok, all(pair_ok))
print('SUMMARY pkgs', [[round(x,1) for x in l] for l in pkg_locs], 'unique', len(set(pkg_locs)))
print('SUMMARY pkgs_clear', all(xy_dist((l[0],l[1]),ps_xy)>=200 for l in pkg_locs) if pkg_locs else False)
print('orig', sha1(r'C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset'))
print('bak', sha1(r'C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset'))
print('details', details)
