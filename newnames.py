import json
from io import StringIO
import re
import collections

with open("./canon_names.json", 'r') as name_in:
        names = json.load(name_in)
name_map = {}
badnames = []
ambiguous = []
nomatch = []
nomatch2 = []
duplicates = collections.defaultdict(list)
collisions = collections.defaultdict(list)

alphas = re.compile(r'[^\w ]+', re.UNICODE)

for dupe_name in [name for name, count in collections.Counter([alphas.sub('',n.lower()) for n in names.values()]).items() if count > 1]:
    for id in names:
        if alphas.sub('',names[id]).lower() == dupe_name:
            duplicates[dupe_name].append(id)

for id in names:
    if re.match(r'^[a-z]{6}[^a-z|$]*', id):
        nsplit = alphas.sub('',names[id]).lower().split(" ")
        startswithid = list(filter(lambda x: x.startswith(id[:3]), nsplit))

        if len(startswithid)>1:
            ambiguous.append(id)
            # Note the ambiguity, but assume that the sort-name is the last split
        
        elif len(startswithid)<1:
            nomatch.append(id)
            continue
        
        new_id1 = startswithid[-1]
        nsplit.remove(new_id1)
        new_id = [new_id1]

        if len(nsplit):
            # Sometimes the secondary ID prefix occupies index 4-6 of the old ID rather than 3-6
            startswithid3 = list(filter(lambda x: x.startswith(id[3:6]), nsplit))
            startswithid4 = list(filter(lambda x: x.startswith(id[4:6]), nsplit))
            if len(startswithid3)>0:
                new_id.append(startswithid3[0])
                nsplit.remove(startswithid3[0])
                new_id.extend(nsplit)
            elif len(startswithid4)>0:
                new_id.append(startswithid4[0])
                nsplit.remove(startswithid4[0])
                new_id.extend(nsplit)
            else:
                nomatch2.append(id)
                continue

        name_map[id]=".".join(new_id)
        
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

print("\n\nNo match ID1 names:")
for nom in nomatch:
    print(nom+" ("+names[nom]+")")

print("\n\nNo match ID2 names:")
for nom in nomatch2:
    print(nom+" ("+names[nom]+")")

print("\n\nDuplicate names:")
duplicate_ids = []
for dup in duplicates:
    print(dup+":")
    for d in duplicates[dup]:
        print("\t"+d+" ("+names[d]+")")
        duplicate_ids.append(d)

print("\n\nCollision names:")
collision_ids = list(filter(lambda x: len(collisions[x])>1, collisions))
for col in collision_ids:
    matched_in_duplicates = False
    for c in collisions[col]:
        if c in duplicate_ids:
            matched_in_duplicates = True
            break
    if matched_in_duplicates:
        continue
    print(col+":")
    for c in collisions[col]:
        print("\t"+c+" ("+names[c]+")")