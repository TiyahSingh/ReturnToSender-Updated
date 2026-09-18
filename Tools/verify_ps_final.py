import json, socket, time, threading, math, hashlib

def send(t, p=None, timeout=30):
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

actors=send('get_actors_in_level',{}).get('actors',[])
if not any(a.get('class')=='PlayerStart' for a in actors):
    print('load', send('load_level',{'path':'/Game/ThirdPerson/Lvl_ThirdPerson'}))
    time.sleep(8)
    actors=send('get_actors_in_level',{}).get('actors',[])

starts=[a for a in actors if a.get('class')=='PlayerStart']
gens=[a for a in actors if 'ProceduralTown' in a.get('class','')]
print('PLAYER_START', starts)
print('GENERATOR', gens)
ps_xy=(starts[0]['location'][0], starts[0]['location'][1]) if starts else (0.0,0.0)
print('PROTECTED_WORLD_XY', ps_xy, 'MIN_DIST', 200.0)
print('COMPILE', send('compile_blueprint',{'blueprint_name':'BP_ProceduralTownGenerator'}))

pkg_locs=[]; tree_ok=[]; pair_ok=[]
for i in range(3):
    print(f'\n=== PIE {i+1} ===', flush=True)
    send('stop_play_in_editor',{})
    time.sleep(2)
    threading.Thread(target=lambda: send('play_in_editor',{}), daemon=True).start()
    got=False
    for t in range(30):
        time.sleep(1)
        a=send('get_actors_in_level',{})
        if not a.get('from_play_world'):
            continue
        actors=a.get('actors') or []
        pkgs=[x for x in actors if 'LostPackage' in str(x.get('class',''))]
        gens=[x for x in actors if 'ProceduralTown' in str(x.get('class',''))]
        comps=send('get_actor_components',{'name': gens[0]['name']}).get('components') if gens else []
        comps=comps or []
        meshes=[]
        for c in comps:
            if 'StaticMesh' not in c.get('class',''):
                continue
            if c.get('name') in ('DefaultSceneRoot','RootComponent','Root'):
                continue
            w=c.get('world_location') or [0,0,0]
            meshes.append((c.get('name'), w, xy_dist((w[0],w[1]), ps_xy)))
        too=[m for m in meshes if m[2] < 200]
        print(f'actors={len(actors)} meshes={len(meshes)} too_close_to_player={[(n,[round(x,1) for x in loc],round(d,1)) for n,loc,d in too]}', flush=True)
        pkg_info=[]
        for p in pkgs:
            loc=p.get('location') or [0,0,0]
            d=xy_dist((loc[0],loc[1]), ps_xy)
            pkg_info.append(([round(x,1) for x in loc], round(d,1), d>=200))
            pkg_locs.append(tuple(loc))
        print('packages', pkg_info, flush=True)
        closes=[]
        for i1 in range(len(meshes)):
            for i2 in range(i1+1,len(meshes)):
                a1=meshes[i1][1]; a2=meshes[i2][1]
                d=xy_dist((a1[0],a1[1]),(a2[0],a2[1]))
                if d < 200: closes.append(round(d,1))
        print('pair_violations', len(closes), flush=True)
        tree_ok.append(len(too)==0 and len(meshes)>0)
        pair_ok.append(len(closes)==0)
        got=True
        break
    send('stop_play_in_editor',{})
    time.sleep(2)
    if not got:
        print('FAIL', flush=True)
        tree_ok.append(False); pair_ok.append(False)

print('\nSUMMARY')
print('trees_clear_of_player_start', tree_ok, all(tree_ok))
print('objects_separated', pair_ok, all(pair_ok))
print('pkg_locs', [[round(x,1) for x in l] for l in pkg_locs])
print('unique_pkgs', len(set(pkg_locs)))
print('pkgs_clear_of_player', all(xy_dist((l[0],l[1]), ps_xy)>=200 for l in pkg_locs) if pkg_locs else False)
print('orig', sha1(r'C:\Users\User\Documents\Unreal Projects\ReturnToSender\Content\Procedural\BP_ProceduralTownGenerator.uasset'))
print('bak', sha1(r'C:\Users\User\Documents\Unreal Projects\EndWhereYouStarted_BACKUP\Content\Procedural\BP_ProceduralTownGenerator.uasset'))
