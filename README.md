# ffxicrafting.com

Crafting data for FFXI era-75 private servers, read from the **LandSandBoat server source** rather than from wikis.

Everything on the site is generated from a SQLite database that is itself built by parsing the server's own SQL, Lua and C++. No hand-entered rates.

## Layout

```
data/     ffxi_crafting.db      the database (build it, or copy the prebuilt one in)
tools/    build_db.py           rebuilds the database from a LandSandBoat checkout
          wiki.py               item name -> wiki link helpers
          build_calculator.py   renders public/calculator.html from the database
          templates/            head/body/app source for the calculator
public/   index.html            landing page
          calculator.html       generated
```

`public/` is what gets deployed. Nothing is built on Vercel: the pages are generated locally and committed, so a deploy is a static file copy.

## Rebuilding

```bash
pip install pyyaml
git clone --depth 1 https://github.com/LandSandBoat/server.git ../lsb-server
python tools/build_db.py ../lsb-server data/ffxi_crafting.db
python tools/build_calculator.py
```

`build_db.py` covers items, recipes (synthesis and desynthesis), and every acquisition source the server implements: mob drops and steals, chests and coffers, battlefields, shops, guild shops and rank vendors, regional, conquest and besieged vendors, HELM gathering, chocobo digging, gardening, fishing, clamming, crystals, guild points, and quest rewards.

## Deploying

Vercel project settings:

- Framework preset: **Other**
- Build command: *(leave empty)*
- Output directory: **public**

Then point the Cloudflare DNS for the domain at Vercel.

## Data and licensing

- The server code this is parsed from ([LandSandBoat](https://github.com/LandSandBoat/server)) is **GPLv3**.
- The underlying game data belongs to **Square Enix**. This is a fan resource. Nothing here is sold, and the site carries no game art unless explicitly added.
- The tooling in `tools/` is the part worth calling original work.

## Accuracy

Numbers come from upstream LandSandBoat. Individual servers run forks with their own settings, so anything server-specific (HQ and drop multipliers, which expansions are enabled, skill caps) is flagged in the UI rather than assumed. The server profile picker exists for exactly this reason.
