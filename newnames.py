import json
from io import StringIO
import re

with open("./canon_names.json", 'r') as name_in:
        names = json.load(name_in)
name_map = {}
badnames = []
ambiguous = []
nomatch = []
collisions = {}

alphas = re.compile(r'[^\w ]+', re.UNICODE)

for id in names:
    if re.match(r'^[a-z]{6}[^a-z|$]*', id):
        nsplit = alphas.sub('',names[id]).lower().split(" ")
        print(nsplit)
        startswithid = list(filter(lambda x: x.startswith(id[:3]), nsplit))
        if len(startswithid)>1:
            ambiguous.append(id)
            continue
        elif len(startswithid)<1:
            nomatch.append(id)
            continue
        nsplit.remove(startswithid[0])
        if len(nsplit):
            name_map[id]=startswithid[0]+"."+".".join(nsplit)
        else:
            name_map[id]=startswithid[0]
        
        if name_map[id] not in collisions:
            collisions[name_map[id]] = [id]
        else:
            collisions[name_map[id]].append(id)
    else:
        badnames.append(id)

with open("./new_id_map.json", 'w') as output:
        json.dump(name_map,output)

print("\n\nBad names:")
for bad in badnames:
    print(bad+" ("+names[bad]+")")
print("\n\nAmbiguous names:")
for amb in ambiguous:
    print(amb+" ("+names[amb]+")")
print("\n\nNo match names:")
for nom in nomatch:
    print(nom+" ("+names[nom]+")")
print("\n\nCollision names:")
collision_ids = list(filter(lambda x: len(collisions[x])>1, collisions))
for col in collision_ids:
    print(col+":")
    for c in collisions[col]:
        print("\t"+c+" ("+names[c]+")")