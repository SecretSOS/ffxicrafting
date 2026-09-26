# PHOENIX_DIFF.md — Phoenix vs LandSandBoat Differences Affecting ffxicrafting.com

> **Generated**: 2026-09-26
> **Phoenix repo**: `C:\Users\MEE87\Documents\phoenix-server\`
> **LSB repo**: `C:\Users\MEE87\Documents\lsb-server\`
> **Site repo**: `C:\Users\MEE87\Documents\ffxicrafting\`
> **NOT for deployment** — this file lives outside `public/` and is never deployed.

---

## How to read this document

Each section maps to a data category that `build_db.py` feeds into the site's SQLite DB.
For every change:
- **File**: the Phoenix module file and line
- **LSB value → Phoenix value**: what changed
- **Site impact**: which page(s) / data this affects
- **Confidence**: CONFIRMED (traceable to file+line) or UNVERIFIED (depends on live `xi.settings.main.*`)

---

## 1. SYNTHESIS RECIPES

**No changes.** Grep for `synth_recipe` across all Phoenix/era SQL and Lua modules returned zero hits. Phoenix does NOT modify any recipes from the base LSB `sql/synth_recipes.sql`.

**Site impact**: None — recipe data can be pulled from base LSB unchanged.

---

## 2. ITEMS (item_basic, item_equipment, item_usable)

### 2a. Item Flags (`pxi_item_basic.sql`)
**File**: `modules/phoenix/sql/pxi_item_basic.sql`

**Global change**: Removes `CAN_SEND_ACCT` (mail-to-account) flag from ALL items (line 25).

**Individual flag changes** (~90 items): Adds Rare, Ex, NoAuction, NoDelivery, NoSale, Inscribable flags to specific items. Examples:
- Meteorite (582): +Rare
- Wyvern Skull (905): +Ex, NoAuction, NoDelivery, Rare
- Batagreens (4367): +Ex, NoAuction, NoDelivery, NoSale
- All Dynamis currency (1449-1457): +NoAuction, NoDelivery
- Relic crafting materials (1930-1959): +Rare

**Stack size changes** (~300+ items): Reverts retail stack increases back to era values.
- All ores (640-647, 736-739): 12 → 1
- All logs (688-703, 722-729): 12 → 1
- All hides/skins (~25 items): 12 → 1
- All shells/bones (~20 items): 12 → 1
- Pickaxe (605): 99 → 12
- Sickle (1020): 99 → 12
- Hatchet (1021): 99 → 12
- Crystals (4096-4103): 12 → 1
- Clusters (4104-4111): 12 → 1
- Many more food, crafting, and misc items

**Site impact**: **HIGH** — `build_db.py` stores `stack`, `ex`, `rare`, `no_auction`, and `base_price` in the `items` table. Phoenix flag changes alter Ex/Rare/NoAuction for ~16 items in the site's DB. Stack size changes affect ~368 items in the DB (most 12→1 for ores, logs, hides, crystals). The `item_source_summary` view uses `ex`/`rare` to classify items, and the profit calculator uses `base_price`.

### 2b. Item Equipment (`pxi_item_equipment.sql`)
**File**: `modules/phoenix/sql/pxi_item_equipment.sql`

Changes `jobs` bitmask on equipment to remove post-era job access:
- ~35 shields: remove WAR access (added May 2015 retail update)
- Flame Shield (12317): restrict to WAR RDM PLD BST SAM
- Arrows/Bolts/Bullets: restore era job restrictions
- Knuckle of Trial (17507): MNK only (removes PUP)

**Site impact**: None — the site doesn't display job restrictions per item.

### 2c. Item Usable (`pxi_item_usable.sql`)
**File**: `modules/phoenix/sql/pxi_item_usable.sql`

- Warp Cudgel: 24-hour cooldown, 30-second use delay
- Chariot/Empress/Emperor Band: 16-hour cooldown, 15-second use delay

**Site impact**: None — the site doesn't display cooldown data.

### 2d. Vendor Sell Prices (`pre_rmt_basesell_vendor_revert.sql`)
**File**: `modules/phoenix/sql/pre_rmt_basesell_vendor_revert.sql` (~300+ lines)

Reverts NPC vendor sell prices (baseSell) to pre-RMT-nerf values for hundreds of items. Examples:
- Max Potion (4124): baseSell → 14749
- Juji Shuriken (17302): baseSell → 82
- Black Ink (929): baseSell → 299
- Many crafted items restored to higher sell prices

**Site impact**: The site's profit calculator uses NPC sell prices. If `build_db.py` reads `baseSell` from `item_basic.sql`, these Phoenix prices will differ from LSB. **This affects the profit page.**

---

## 3. GUILD SHOPS

### 3a. Era Guild Shop Stock (`era_guild_shops.lua`)
**File**: `modules/phoenix/lua/data/era_guild_shops.lua` (707 lines)

**Massive overhaul** of all guild shop inventories. Changes include:

#### Stock adjustments per guild:
| Guild | Changes Summary |
|-------|----------------|
| Smithing | Adds Copper Ore to Vicious_Eye & Amulya (shared stock), adjusts initial stock levels |
| Goldsmithing | Adds Copper Ore, adjusts stock levels, adds sharedStock (Teerth↔Celestina) |
| Woodworking | Adds Copper Ore, adjusts stock, adds sharedStock (Chomo_Jinjahl↔Cauzeriste) |
| Clothcraft | Adds Copper Ore, adjusts stock, adds sharedStock (Cletae↔Gibol) |
| Leathercraft | Adds Copper Ore, adjusts stock, adds sharedStock (Odoba↔Retto-Marutto) |
| Bonecraft | Adds Copper Ore, adjusts stock |
| Alchemy | Adds Copper Ore, adjusts stock |
| Cooking | Adds Copper Ore, adjusts stock |
| Fishing | Adds Copper Ore, adjusts stock |
| Tenshodo | Creates guild shops for Akamafula and Amalasanda (reverted from normal NPC shops back to guild shops) |

#### New items added to guild shops:
- Mandrel (1624) — Smithing
- Workshop Anvil (6289) — Smithing
- Tanning Vat (6290) — Leatherwork
- Copper Ore (640) — Added to almost every guild shop

#### Items removed:
- JUJI_SHURIKEN removed from Silver_Owl (Bonecraft)
- PENDANT_COMPASS removed from linkshell vendors

#### Shared stock pairs (new mechanic):
- Vicious_Eye ↔ Amulya (Smithing)
- Lucretia ↔ Doggomehr (implied from shared stocks file)
- Teerth ↔ Celestina (Goldsmithing)
- Chomo_Jinjahl ↔ Cauzeriste (Woodworking)
- Cletae ↔ Gibol (Clothcraft)
- Odoba ↔ Retto-Marutto (Leatherwork)
- Mololo (Mhaura Smithing, shared)
- Meriri (Windurst, shared)

**File**: `modules/phoenix/lua/zones/era_guild_shared_stocks.lua` (111 lines)
Wires up the NPC triggers for all shared stock pairs.

**Site impact**: **HIGH** — Guild shop data feeds the site's shopping page and item source listings. Stock levels, prices, new/removed items, and the shared-stock mechanic all affect which items players can buy from guilds.

### 3b. Guild Shop Persistence (`guild_shop_persistence.lua`)
**File**: `modules/phoenix/lua/custom/guild_shop_persistence.lua` (137 lines)

Saves/restores guild shop state across server restarts. This is server infrastructure, not data.

**Site impact**: None directly — but explains why guild stock levels matter on Phoenix.

---

## 4. GUILD POINT TURN-INS & REWARDS

### 4a. GP Turn-in Item/Value Changes (`guild_item_points.sql`)
**File**: `modules/era/sql/abyssea/guild_item_points.sql` (530 lines)

**Massive overhaul** of guild point turn-in items and values, reverting to pre-October 2011 historical data. Changes every guild:

- **Fishing**: Moat Carp → Phanauet Newt, Bastore Sweeper → Greedie, many item swaps
- **Woodworking**: Humus → Maple Wand, Bamboo Fishing Rod → Ash Clogs, many item/value changes
- **Smithing**: Hatchet → Bronze Dagger, item/value corrections
- **Goldsmithing**: Brass Leggings → Brass Ring, value corrections
- **Clothcraft**: Kyahan → Robe, value corrections
- **Leathercraft**: Leather Trousers → Rabbit Mantle, value corrections
- **Bonecraft**: Scorpion Ring → Blood Stone, value corrections
- **Alchemy**: Tsurara → Wax Sword, value corrections
- **Cooking**: Orange Juice → Pebble Soup, ALL values significantly reduced (pre-Oct 2011 nerf)

Almost every guild rank's turn-in items and point values are changed.

**Site impact**: **HIGH** — The site has `gp_turnins` and `gp_rewards` tables. All turn-in items, point values, and max points need to be updated.

### 4b. GP Max Points Divisor (`rov/guild_item_points.sql`)
**File**: `modules/era/sql/rov/guild_item_points.sql` (12 lines)

Single statement: `UPDATE guild_item_points SET max_points = max_points / 3`

Divides ALL max_points by 3, reverting the November 2016 triple that retail applied.

**Site impact**: **HIGH** — Compounds with the Abyssea changes above. All max_points values are 1/3 of LSB base.

### 4c. GP Shop Reward Changes (`guild_point_shop.lua`)
**File**: `modules/phoenix/lua/globals/hobbies/crafting/guild_point_shop.lua` (168 lines)

- Aurora Crystal: GP cost 200 → 500
- Twilight Crystal: GP cost 200 → 500
- Analysis Crystals: **disabled** (rank set to 99)
- Per-guild disabled items (rank=99):
  - All "Way of the X" key items (Carpenter, Blacksmith, Goldsmith, etc.)
  - All guild tool items (Kit/Net, Stone Hearth, Gemscope, etc.)
  - All guild Emblems (Blacksmiths', Goldsmiths', etc.)
  - Angler's Almanac
- **UNVERIFIED (live config)**: When `xi.settings.main.ENABLE_WOTG == 0`:
  - All Signboards disabled
  - All guild Rings disabled

**Site impact**: **HIGH** — The `gp_rewards` data needs to reflect disabled items and changed costs.

---

## 5. CRAFTING RANK CAP

**File**: `modules/phoenix/lua/globals/hobbies/crafting/guild_master_rank_cap.lua` (34 lines)

Caps all crafting at **Veteran** rank (skill 110). Players cannot advance past Veteran.

**Site impact**: **MEDIUM** — The site could note this cap. Affects which recipes are accessible (recipes requiring higher skill won't be craftable, but they still exist in the DB).

---

## 6. NPC VENDORS (non-guild)

### 6a. Conquest Vendors
**File**: `modules/phoenix/lua/globals/era_conquest_costs.lua` (101 lines)

- Instant Reraise scroll: 7 CP → 500 CP
- Instant Warp scroll: 10 CP → 750 CP
- **Removed**: Emperor Band, Warp Ring, Trust Ciphers

**File**: `modules/era/lua/globals/conquest.lua`
- Removes conquest points as payment for outpost teleportation (gated by `xi.pre(xi.expansion.VOIDWATCH)`)

**Site impact**: **MEDIUM** — Conquest vendor items feed the `sources` table. Removed items and price changes affect item source listings.

### 6b. Era Vendor Overrides (~55 NPCs across 20+ zones)

Spread across `modules/era/lua/zones/*/npcs/*.lua` (14 zone vendor files + 12 individual NPC files). Each file is a Lua module gated by an expansion precondition.

**Modules gated by `xi.pre(xi.expansion.ABYSSEA)`** (active on Phoenix):

| Zone | File | NPCs | Key Changes |
|------|------|------|-------------|
| Bastok Mines | `bastok_mines_vendors.lua` | Boytz, Zemedars, Neigepance | Remove Republic Waystone; full armor stock rework; broth price corrections |
| N. San d'Oria | `northern_san_doria_vendors.lua` | Arlenne, Tavourine, Pirvidiauce | Full weapon stock rework; remove Kingdom Waystone |
| Port Windurst | `port_windurst_vendors.lua` | Hohbiba-Mubiba, Taniko-Maniko, Guruna-Maguruna, Kumama | Full weapon/armor stock rework |
| Kazham | `kazham_vendors.lua` | Toji_Mumosulah, Ghemi_Sinterilo, Mamerie | Remove OOE scrolls, Aquilaria Log, Kazham Waystone; broth prices; conditional Monomi Ichi/Pachira Fruit (WotG) |
| Windurst Woods | `windurst_woods_vendors.lua` | Mono_Nchaa, Wije_Tiren, Quesse | Remove Fed. Waystone; arrow stock rework; broth prices |
| Rabao | `rabao_vendors.lua` | Brave_Ox, Scamplix, Generoit | Remove Cure VI/Protect V/Shell V/Crusade, Rabao Waystone; broth prices; conditional Cura/Sacrifice/Esuna/Auspice (WotG) |
| Selbina | `dohdjuma.lua` | Dohdjuma | Remove Selbina Waystone |
| Port Bastok | `numa.lua` | Numa | Remove ninjutsu toolbags |
| Windurst Waters | `orez-ebrez.lua` | Orez-Ebrez | Full headgear stock rework |

**Modules gated by `xi.pre(xi.expansion.WOTG)`** (active on Phoenix):

| Zone | File | NPCs | Key Changes |
|------|------|------|-------------|
| Al Zahbi | `al_zahbi_vendors.lua` | Zafif, Chayaya | Remove Reprisal, OOE Corsair rolls |
| Metalworks | `nogga.lua` | Nogga | Stock reduced to Bomb Arm + Grenade only |
| Port Jeuno | `gekko.lua` | Gekko | Remove Regen IV scroll |
| Port San d'Oria | `coullave.lua` | Coullave | Full stock replacement |
| Global | `valeriano_shop_adjust.lua` | 3 Valeriano NPCs | Remove OOE bard stock |

**Modules gated by `xi.pre(xi.expansion.SOA)`** (active on Phoenix):

| Zone | File | NPCs | Key Changes |
|------|------|------|-------------|
| Tavnazian Safehold | `tavnazian_safehold_vendors.lua` | Nilerouche, Mazuro-Oozuro | Remove OOE spells, Safehold Waystone |
| Mhaura | `pikini-mikini.lua` | Pikini-Mikini | Full potion/scroll/bait stock rework |
| Norg | `solby-maholby.lua` | Solby-Maholby | Remove OOE NIN scrolls; stock reduced to Lugworm + Earth Spirit Pact |
| N. San d'Oria | `mulaujeant.lua` | Mulaujeant | Quest mechanic only (not a shop change) |
| Windurst Waters | `churano-shurano.lua` | Churano-Shurano | Quest mechanic only (not a shop change) |

**Modules with internal per-NPC expansion gating** (in files with no top-level precondition):

| Zone | File | NPCs | Key Changes |
|------|------|------|-------------|
| Bastok Markets | `bastok_markets_vendors.lua` | Harmodios, Ciqala, Hortense, Peritrage, Zhikkom, Charging_Chocobo, Mjoll, Sororo | Full stock rework per NPC (gated ABYSSEA/ROV/WOTG per-NPC); Sororo adds Aquaveil |
| S. San d'Oria | `southern_san_doria_vendors.lua` | Ashene, Carautia, Ferdoulemiont, Ostalie, Benaige | Full stock rework; remove Minne V, Paprika/Zucchini |
| Aht Urhgan | `aht_urhgan_whitegate_vendors.lua` | Dwago, Gavrie, Hagakoff, Mazween, Khaf_Jhifanm | Remove Auto Oil +3, Empire Waystone; conditional Absorb-ACC (WotG) |
| Lower Jeuno | `lower_jeuno_vendors.lua` | Pawkrix, Creepstix, Hasim, Susu, Stinknix, Taza, Chetak, Yoskolo, Ghebi_Damomohe | Remove OOE spells, Duchy Waystone, Bronzite, Goblin Stew 880 |
| Upper Jeuno | `upper_jeuno_vendors.lua` | Antonia, Coumuna, Areebah | Remove job point weapons; conditional Flower Seeds (WotG), Water Lily (Abyssea) |
| Nashmau | `nashmau_vendors.lua` | Yoyoroon, Poporoon, Pipiroon, Mamaroon, Jajaroon | Remove PUP attachments, Enlight/Endark, Nashmau Waystone, Trump Card Case |

**Key items removed across many shops**: Waystones (Republic, Kingdom, Federation, Duchy, Empire, Kazham, Selbina, Rabao, Safehold, Nashmau), OOE spell scrolls, Trust Ciphers, ninjutsu toolbags, Trump Card Case, Automaton Oil +3, Goblin Stew 880, Bronzite.

**UNVERIFIED (live config)** — WotG-conditional additions (active only when `ENABLE_WOTG` setting is on):
- Absorb-ACC (Mazween, Whitegate)
- Monomi: Ichi (Toji_Mumosulah, Kazham)
- Elshimo Pachira Fruit (Ghemi_Sinterilo, Kazham)
- Cura/Sacrifice/Esuna/Auspice (Brave_Ox, Rabao)
- Flower Seeds (Areebah, Upper Jeuno)

### 6c. Outpost Teleportation
**File**: `modules/era/lua/globals/conquest.lua` (67 lines, gated `xi.pre(xi.expansion.VOIDWATCH)`)

Removes conquest points as payment option for outpost teleportation (added Dec 2011 retail).

**Site impact**: None — the site doesn't track outpost teleportation mechanics.

**Site impact (6b overall)**: **HIGH** — Every vendor stock change affects `sources` entries of type `npc_shop`. ~55 NPCs across 20+ zones have items added, removed, or repriced.

---

## 7. MOB DROPS

### 7a. Phoenix Drop Overrides
**File**: `modules/phoenix/data/drops/zones/` — **29 zones** with modified drop tables

Zones with Phoenix-specific drop changes:
Arrapago Reef, Behemoth's Dominion, Bhaflau Thickets, Bibiki Bay, Caedarva Mire, Crawler's Nest, Dragon's Aery, East Sarutabaruta, Giddeus, Halvung, Konschtat Highlands, Korroloka Tunnel, La Theine Plateau, Mamook, Mount Zhayolm, Palborough Mines, Ranguemont Pass, Sea Serpent Grotto, Tahrongi Canyon, The Boyahda Tree, The Eldieme Necropolis, The Sanctuary of Zitah, Uleguerand Range, Valley of Sorrows, Wajaom Woodlands, West Sarutabaruta, Western Altepa Desert, Yhoator Jungle, Yuhtunga Jungle

Example: East Sarutabaruta removes Skull Locust from Yagudo Initiates (added March 2010 retail).

### 7b. Era Abyssea Drop Removals
**File**: `modules/era/data/abyssea/mob_droplist_removal/zones/` — **28 zones**

Removes post-Abyssea drops from mobs in zones like Davoi, Fort Ghelsba, Garlaige Citadel, Giddeus, Gustav Tunnel, etc.

### 7c. Era TOAU Pre-RMT Drop Reverts
**File**: `modules/era/data/toau/pre_rmt_drops/zones/` — **13 zones**

Restores pre-RMT-nerf drop tables in Castle Oztroja, Fei'Yin, Jugner Forest, Labyrinth of Onzozo, Maze of Shakhrami, Ordelles Caves, Quicksand Caves, Rolanberry Fields, Sauromugue Champaign, Sea Serpent Grotto, South Gustaberg, The Boyahda Tree, Valkurm Dunes.

### 7d. Era SOA Drop Adjustments
**File**: `modules/era/data/soa/mob_droplist_adjust/zones/attohwa_chasm/mobs.yaml` — 1 zone

**Site impact**: **HIGH** — Drop data feeds `sources` entries of type `mob_drop`. ~70 zone-level YAML overrides affect which items drop and at what rates. Each YAML file in the module system overrides the base YAML for that zone.

---

## 8. BATTLEFIELD / BCNM LOOT

**File**: `modules/phoenix/lua/battlefields/up_in_arms_kraken_club.lua` (37 lines)

- Up in Arms BCNM: Kraken Club drop weight 1/10000 → 10/10000 (10x more common)

**Site impact**: **LOW** — If the site lists BCNM rewards with drop rates, this specific rate would differ.

---

## 9. FISHING

### 9a. Fishing Rod Changes
**File**: `modules/phoenix/sql/fishing_rod.sql` (5 lines)

| Rod | max_rank LSB → Phoenix |
|-----|----------------------|
| Clothespole (17383) | 16 → 12 |
| Single Hook Fishing Rod (17382) | 22 → 13 |
| Hume Fishing Rod (17014) | 10 → 15 |
| Bamboo Fishing Rod (17389) | 8 → 7 |
| Fastwater Fishing Rod (17388) | 7 → 8 |

**Site impact**: **LOW** — The site displays fishing rod data. Max rank values would differ.

### 9b. No Other Fishing Overrides

No Lua modules override fish tables, bait tables, or fishing zone data. The fishing SQL tables (`fishing_mob`, `fishing_bait`, `fishing_lure`, `fishing_zone`) are unchanged from base LSB.

---

## 10. CHOCOBO DIGGING

**File**: `modules/phoenix/lua/globals/hobbies/chocobo_digging/pxi_digging_data.lua` (637 lines)
**File**: `modules/phoenix/lua/globals/hobbies/chocobo_digging/pxi_digging_logic.lua` (199 lines)
**File**: `modules/phoenix/lua/globals/hobbies/chocobo_digging/chocobo_account_fatigue.lua` (20 lines)

**Complete replacement** of the chocobo digging system:
- Custom XP-based leveling system (100 levels)
- Rank-based accuracy (30-55%)
- Position-based repeat dig prevention (4 yalm check)
- Weather-based crystal/cluster/elemental ore drops
- Night-only items (seeds)
- **22 zone tables** with per-item, per-rank weights (11 weight columns)
- Account-wide fatigue instead of per-character
- **UNVERIFIED (live config)**: `xi.settings.main.DIG_FATIGUE` controls daily limit

Covered zones: Batallia Downs, Buburimu, E/W Ronfaure, E/W Sarutabaruta, Jugner, Konschtat, La Theine, Meriphataud, N/S Gustaberg, Pashhow, Rolanberry, Sauromugue, Tahrongi, Valkurm, E/W Altepa, Sanctuary of Zitah, Yhoator/Yuhtunga Jungle, Bibiki Bay, Carpenter's Landing, Bhaflau Thickets, Wajaom Woodlands

**Site impact**: **HIGH** — The site has chocobo digging data showing which items can be dug in which zones. The entire zone-item mapping is different on Phoenix.

---

## 11. HELM (Harvesting, Excavation, Logging, Mining)

**File**: `modules/era/lua/globals/helm/helm_adjustments.lua` (119 lines)

Removes post-era HELM items, gated by expansion:
- **ABYSSEA gate**: removes Butterpear, Aquilaria Log, Kapor Log from Yhoator/Yuhtunga logging
- **WOTG gate**: removes Eastern Ginger Root from Bhaflau/Wajaom harvesting, Dyer's Woad from Giddeus/W.Sarutabaruta harvesting, Slab of Plumbago from Halvung/Mt.Zhayolm mining

**Site impact**: **MEDIUM** — HELM items feed `sources` entries. These specific items would be removed from their respective zone gathering tables.

---

## 12. SCAVENGE DATA

**File**: `modules/era/lua/data/scavenge_data.lua`

Defines zone-specific Scavenge (Ranger ability) loot pools with ammunition containers by tier.

**Site impact**: **NONE** — Scavenge is not tracked by `build_db.py`.

---

## 13. SETTINGS-DEPENDENT BEHAVIOR (UNVERIFIED)

These changes depend on Phoenix's live `xi.settings.main.*` values, which are NOT in the repo:

| Setting | Effect | File |
|---------|--------|------|
| `ENABLE_WOTG` | If 0: disables Signboards and Rings from GP shop | `guild_point_shop.lua:148` |
| `DIG_FATIGUE` | Daily chocobo dig limit (if > 0) | `pxi_digging_logic.lua:137` |

**Recommendation**: Ask the Phoenix server admin for these values, or flag them on the site as "may vary by server config."

---

## SUMMARY: What needs to change in build_db.py

### Must change (affects displayed data):
1. **Items (flags/stacks/baseSell)**: Apply `pxi_item_basic.sql` (~16 flag changes + ~368 stack changes in DB) + `pre_rmt_basesell_vendor_revert.sql` (~201 price changes in DB)
2. **Guild shops**: Parse `era_guild_shops.lua` for stock/price/item changes, shared stock pairs, new Tenshodo guild shops
3. **NPC vendors**: Parse ~27 era vendor override files + `era_conquest_costs.lua` for stock changes (~55 NPCs)
4. **GP turn-ins**: Apply `abyssea/guild_item_points.sql` then `rov/guild_item_points.sql` (÷3 max_points)
5. **GP rewards**: Apply `guild_point_shop.lua` changes (Aurora/Twilight cost, disabled items)
6. **Chocobo digging**: Replace digging zone tables with `pxi_digging_data.lua` (complete rewrite, 22 zones)
7. **Mob drops**: Layer Phoenix + era YAML drop overrides on top of base data (~70 zone files)
8. **HELM**: Apply `helm_adjustments.lua` removals (6 items from gathering tables)
9. **Fishing rods**: Apply `fishing_rod.sql` max_rank changes (5 rods)
10. **Conquest vendors**: Apply `era_conquest_costs.lua` (2 price changes + 4 item removals)

### Should change (affects accuracy):
11. **Battlefield loot**: Update Kraken Club rate for Up in Arms (1/10000 → 10/10000)
12. **Crafting rank cap**: Note Veteran cap on the site (skill 110 max)

### No change needed:
- Recipes (byte-identical between LSB and Phoenix)
- Item equipment/job restrictions (site doesn't display these)
- Item usable cooldowns (not displayed)
- Fishing tables (unchanged except rods)
- Scavenge data (not tracked)
- Outpost teleportation (not tracked)

---

## NEXT STEPS

**STOP** — waiting for your approval before making any code changes.

When approved, the approach for `build_db.py`:
1. Add a second CLI arg for the Phoenix modules path (optional, so the script still works with LSB-only)
2. After parsing each base data source, apply Phoenix SQL/Lua overrides in module load order
3. For SQL modules: replay UPDATEs/INSERTs/DELETEs against the in-memory data
4. For Lua modules: parse the patchStock/removeStock/table.insert calls and apply to guild shop data
5. For YAML modules: load override YAML and deep-merge (JSON Merge Patch semantics) onto base zone data
6. For chocobo digging: detect the `pxi_digging_data.lua` and use it instead of base `data.lua`
7. Rebuild the SQLite DB, then all site pages
8. Write a repeatable `sync.sh` / `sync.py` that pulls both repos and rebuilds
