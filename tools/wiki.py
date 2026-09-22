import re, urllib.parse
ROMAN={'ii':'II','iii':'III','iv':'IV','v':'V','vi':'VI','i':'I'}
SMALL={'of','the','and','a','to','in','on','for'}
# Words that are possessives in FFXI item names (LSB strips the apostrophe). Curated from the data; extend as needed.
POSS=set('''archers attilas balans balins bayards beaters calveleys conjurers druids esquires evokers fencers forsetis gawains gleemans grosveneurs
harlequins healers hoplites jongleurs kabrakans magicians marksmans mercenarys minstrels nursemaids ochiudos palmerins penitents philosophers
pilferers rogues singers slayers snipers soldiers sorcerers taillefers tamers templars trackers trailers trainers trimmers varlets vassagos warlocks
wizards woodvilles wrestlers ziskas legionnaires freeswords footmans decurions centurions knights guards musketeers casters captains warriors monks
mages thiefs paladins rangers samurais ninjas bards dragoons summoners hunters pilgrims seers duelists militants fighters chasers'''.split())
def poss(words):
    return [ (x[:-1]+"'s" if (x.lower() in POSS and k < len(words)-1) else x) for k,x in enumerate(words)]
def _title(s):
    w=s.replace('_',' ').split()
    out=[]
    for k,x in enumerate(w):
        lx=x.lower()
        if lx in ROMAN and k>0: out.append(ROMAN[lx])
        elif k and lx in SMALL: out.append(lx)
        elif x.startswith('+'): out.append(x)
        else: out.append('-'.join(p[:1].upper()+p[1:] for p in x.split('-')))
    return ' '.join(poss(out))
def wiki_title(name, sortname):
    if name.startswith('scroll_of_'): return _title(name)
    if sortname and '.' not in sortname: return _title(sortname)
    return _title(re.sub(r'^(chunk|pinch|handful|bag|jar|flask|square|piece|slice|vial|bottle|pot|bunch|clump|sprig|bulb|sheet|lump|spool|coil|strip|block|stick|loaf|plate|cluster|pair|set|box|bolt|quiver|stack|tin|can|bowl|dish|serving|cup|glass|head|lock|sack|jug|carton|chunk)_of_','',name))
def wiki_url(title):
    return 'https://horizonffxi.wiki/w/index.php?'+urllib.parse.urlencode({'search':title,'title':'Special:Search','go':'Go'})
def db_url(name):
    return 'https://horizonxi.com/items/'+name
if __name__=='__main__':
    for n,s in [('chunk_of_copper_ore','copper_ore'),('royal_knights_belt','ryl.kgt._belt'),('scroll_of_warp_ii','warp_ii'),('dart_+1','dart_+1'),('scroll_of_absorb-vit','absorb-vit'),('wrestlers_aspis','wrestlers_aspis')]:
        t=wiki_title(n,s); print(n,'->',t,wiki_url(t))
