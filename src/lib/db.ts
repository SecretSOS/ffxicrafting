import Database from 'better-sqlite3';
import { existsSync } from 'node:fs';
import path from 'node:path';

const DB_PATH = path.resolve('data', 'ffxi_crafting.db');

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH, { readonly: true });
  }
  return _db;
}

export function getMeta(key: string): string {
  const row = getDb().prepare('SELECT v FROM meta WHERE k = ?').get(key) as { v: string } | undefined;
  return row?.v ?? '';
}

export interface Item {
  id: number;
  name: string;
  stack: number | null;
  flags: string | null;
  base_sell: number | null;
}

export interface SourceRow {
  item_id: number;
  type: string;
  zone: string | null;
  where_: string | null;
  pct: number | null;
  price: number | null;
  level_lo: number | null;
  level_hi: number | null;
  gate: string | null;
  notes: string | null;
  content: string | null;
}

export interface FishAreaRow {
  fish_item_id: number;
  name: string;
  skill: number;
  rarity: number | null;
  area: string | null;
}

const ERA_CONTENT = new Set([null, '', 'rotz', 'cop', 'toau', 'wotg']);

const EXCLUDE_PREFIXES = ['abyssea', 'dynamis', 'walk_of_echoes', 'escha_', 'reisenjima'];
const EXCLUDE_ZONES = new Set([
  'ceizak_battlegrounds', 'yahse_hunting_grounds', 'foret_de_hennetiel',
  'morimar_basalt_fields', 'yorcia_weald', 'marjami_ravine', 'kamihr_drifts',
  'doh_gates', 'woh_gates', 'outer_ra_kaznar', 'inner_ra_kaznar', 'moh_gates',
  'cirdas_caverns', 'rala_waterways', 'sih_gates', 'western_adoulin', 'eastern_adoulin',
  'leafallia', 'castle_adoulin', 'mog_garden', 'celennia_memorial_library',
  'ghoyus_reverie', 'everbloom_hollow',
]);

export function isExcludedZone(z: string): boolean {
  if (EXCLUDE_ZONES.has(z)) return true;
  return EXCLUDE_PREFIXES.some(p => z.startsWith(p));
}

export function isEra(content: string | null): boolean {
  return ERA_CONTENT.has(content?.toLowerCase() ?? null);
}

export function getAllItems(): Map<number, string> {
  const db = getDb();
  const rows = db.prepare('SELECT id, name FROM items').all() as { id: number; name: string }[];
  const map = new Map<number, string>();
  for (const r of rows) map.set(r.id, r.name);
  return map;
}

export function getZoneSources(zone: string): SourceRow[] {
  const db = getDb();
  return db.prepare(
    "SELECT * FROM sources WHERE zone = ? ORDER BY type, item_id"
  ).all(zone) as SourceRow[];
}

export function getAllZones(): string[] {
  const db = getDb();
  const rows = db.prepare(
    "SELECT DISTINCT zone FROM sources WHERE zone IS NOT NULL AND zone != '' ORDER BY zone"
  ).all() as { zone: string }[];
  return rows.map(r => r.zone).filter(z => !isExcludedZone(z));
}

export function getZoneFishing(zone: string): FishAreaRow[] {
  const db = getDb();
  return db.prepare(`
    SELECT fa.fish_item_id, f.name, f.skill, fa.rarity, fa.area
    FROM fishing_areas fa JOIN fish f ON f.item_id = fa.fish_item_id
    WHERE fa.zone = ? ORDER BY f.skill, f.name
  `).all(zone) as FishAreaRow[];
}

export function iconExists(itemId: number): boolean {
  return existsSync(path.resolve('public', 'icons', `${itemId}.png`));
}

// ── Craft data ──────────────────────────────────────────────────

export const CRAFTS_ORDERED = [
  { code: 'wood',    name: 'Woodworking',  cssVar: '--wood' },
  { code: 'smith',   name: 'Smithing',     cssVar: '--smith' },
  { code: 'gold',    name: 'Goldsmithing', cssVar: '--gold' },
  { code: 'cloth',   name: 'Clothcraft',   cssVar: '--cloth' },
  { code: 'leather', name: 'Leathercraft', cssVar: '--leather' },
  { code: 'bone',    name: 'Bonecraft',    cssVar: '--bone' },
  { code: 'alchemy', name: 'Alchemy',      cssVar: '--alchemy' },
  { code: 'cook',    name: 'Cooking',      cssVar: '--cook' },
] as const;

export type CraftCode = typeof CRAFTS_ORDERED[number]['code'];

export const GUILDS: Record<CraftCode, {
  guildKey: string; display: string; location: string;
  open: number; close: number; holiday: number; vendor: string;
}> = {
  wood:    { guildKey: 'woodworking',   display: 'Woodworking Guild',   location: "Northern San d'Oria", open: 6,  close: 21, holiday: 0, vendor: 'woodworking guild vendor' },
  smith:   { guildKey: 'smithing',      display: 'Smithing Guild',      location: 'Metalworks, Bastok',  open: 8,  close: 23, holiday: 2, vendor: 'smithing guild vendor' },
  gold:    { guildKey: 'goldsmithing',  display: 'Goldsmithing Guild',  location: 'Bastok Markets',      open: 8,  close: 23, holiday: 4, vendor: 'goldsmithing guild vendor' },
  cloth:   { guildKey: 'clothcraft',    display: 'Clothcraft Guild',    location: 'Windurst Woods',      open: 6,  close: 21, holiday: 0, vendor: 'clothcraft guild vendor' },
  leather: { guildKey: 'leathercraft',  display: 'Leathercraft Guild',  location: "Southern San d'Oria", open: 3,  close: 18, holiday: 4, vendor: 'leathercraft guild vendor' },
  bone:    { guildKey: 'bonecraft',     display: 'Bonecraft Guild',     location: 'Windurst Woods',      open: 8,  close: 23, holiday: 3, vendor: 'bonecraft guild vendor' },
  alchemy: { guildKey: 'alchemy',       display: 'Alchemy Guild',       location: 'Bastok Mines',        open: 8,  close: 23, holiday: 4, vendor: 'alchemy guild vendor' },
  cook:    { guildKey: 'cooking',       display: 'Cooking Guild',       location: 'Windurst Waters',     open: 5,  close: 20, holiday: 7, vendor: 'cooking guild vendor' },
};

export const VANA_DAYS = ['Firesday', 'Earthsday', 'Watersday', 'Windsday', 'Iceday', 'Lightningsday', 'Lightsday', 'Darksday'];

const ERA_SQL = "(content_tag IS NULL OR content_tag IN ('ROTZ','COP','TOAU','WOTG'))";

export interface CraftStats { total: number; era60: number; desynth: number }

export function getCraftStats(craft: CraftCode): CraftStats {
  const db = getDb();
  const total = (db.prepare(`SELECT COUNT(*) as c FROM recipes WHERE main_craft=? AND desynth=0 AND ${ERA_SQL}`).get(craft) as {c:number}).c;
  const era60 = (db.prepare(`SELECT COUNT(*) as c FROM recipes WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62 AND ${ERA_SQL}`).get(craft) as {c:number}).c;
  const desynth = (db.prepare(`SELECT COUNT(*) as c FROM recipes WHERE main_craft=? AND desynth=1 AND ${ERA_SQL}`).get(craft) as {c:number}).c;
  return { total, era60, desynth };
}

export interface ShopItem { item_id: number; name: string; price: number; qty_lo: number; qty_hi: number }

export function getGuildShopItems(craft: CraftCode): ShopItem[] {
  const db = getDb();
  const npcs = db.prepare("SELECT DISTINCT where_ FROM sources WHERE type='guild_shop'").all() as { where_: string }[];

  const npcCraft = new Map<string, string>();
  for (const { where_: npc } of npcs) {
    const items = db.prepare("SELECT item_id FROM sources WHERE type='guild_shop' AND where_=?").all(npc) as { item_id: number }[];
    if (!items.length) continue;
    const ph = items.map(() => '?').join(',');
    const row = db.prepare(`SELECT main_craft, COUNT(*) as cnt FROM recipes WHERE id IN (SELECT recipe_id FROM recipe_ingredients WHERE item_id IN (${ph})) GROUP BY main_craft ORDER BY cnt DESC LIMIT 1`).get(...items.map(i => i.item_id)) as { main_craft: string } | undefined;
    if (row) npcCraft.set(npc, row.main_craft);
  }

  const shopNpcs = [...npcCraft.entries()].filter(([, c]) => c === craft).map(([n]) => n).sort();
  const seen = new Set<number>();
  const result: ShopItem[] = [];
  for (const npc of shopNpcs) {
    const rows = db.prepare(`
      SELECT s.item_id, i.name, s.price, s.qty_lo, s.qty_hi
      FROM sources s JOIN items i ON i.id = s.item_id
      WHERE s.type='guild_shop' AND s.where_=? ORDER BY s.price
    `).all(npc) as ShopItem[];
    for (const r of rows) {
      if (!seen.has(r.item_id)) { seen.add(r.item_id); result.push(r); }
    }
  }
  result.sort((a, b) => a.price - b.price);
  return result;
}

export interface VendorItem { item_id: number; name: string; price: number; gate: string | null }

export function getGuildVendorItems(vendor: string): VendorItem[] {
  return getDb().prepare(`
    SELECT s.item_id, i.name, s.price, s.gate
    FROM sources s JOIN items i ON i.id = s.item_id
    WHERE s.type='guild_vendor' AND s.where_=? ORDER BY s.price
  `).all(vendor) as VendorItem[];
}

export interface TurninRow { pattern: number; item_id: number; name: string; tier: number; points: number; max_points: number }

export function getGuildTurnins(guildKey: string): Map<number, TurninRow[]> {
  const rows = getDb().prepare(`
    SELECT t.pattern, t.item_id, i.name, t.tier, t.points, t.max_points
    FROM gp_turnins t JOIN items i ON i.id = t.item_id
    WHERE t.guild=? ORDER BY t.pattern, t.tier
  `).all(guildKey) as TurninRow[];
  const map = new Map<number, TurninRow[]>();
  for (const r of rows) {
    if (!map.has(r.pattern)) map.set(r.pattern, []);
    map.get(r.pattern)!.push(r);
  }
  return map;
}

export interface RewardItem { name: string; item_id: number | null; min_rank: string; cost: number }
export interface RewardKeyItem { name: string; min_rank: string; cost: number }

export function getGuildRewards(guildKey: string): { items: RewardItem[]; keyItems: RewardKeyItem[] } {
  const db = getDb();
  const items = db.prepare(`
    SELECT r.name, r.item_id, r.min_rank, r.cost
    FROM gp_rewards r WHERE r.guild=? AND r.kind='item' ORDER BY r.cost
  `).all(guildKey) as RewardItem[];
  const keyItems = db.prepare(`
    SELECT r.name, r.min_rank, r.cost
    FROM gp_rewards r WHERE r.guild=? AND r.kind='key_item' ORDER BY r.cost
  `).all(guildKey) as RewardKeyItem[];
  return { items, keyItems };
}

// ── Notorious Monsters ──────────────────────────────────────────

export interface NMDrop {
  item_id: number;
  item_name: string;
  pct: number | null;
  is_ingredient: boolean;
}

export interface NMEntry {
  mob: string;
  zone: string;
  level_lo: number | null;
  level_hi: number | null;
  gate: string;
  drops: NMDrop[];
  steals: NMDrop[];
}

export function getAllNMs(): NMEntry[] {
  const db = getDb();

  const ingredientIds = new Set(
    (db.prepare('SELECT DISTINCT item_id FROM recipe_ingredients').all() as { item_id: number }[])
      .map(r => r.item_id)
  );

  const dropRows = db.prepare(`
    SELECT s.where_ as mob, s.zone, s.item_id, i.name as item_name, s.pct,
           s.level_lo, s.level_hi, s.gate, s.type
    FROM sources s JOIN items i ON i.id = s.item_id
    WHERE s.type IN ('mob_drop', 'mob_steal')
      AND s.gate LIKE '%notorious%'
      AND (s.content IS NULL OR LOWER(s.content) IN ('rotz','cop','toau','wotg'))
    ORDER BY s.zone, s.where_, s.type, s.pct DESC
  `).all() as {
    mob: string; zone: string; item_id: number; item_name: string;
    pct: number | null; level_lo: number | null; level_hi: number | null;
    gate: string; type: string;
  }[];

  const nmMap = new Map<string, NMEntry>();
  for (const r of dropRows) {
    if (isExcludedZone(r.zone)) continue;
    const key = `${r.mob}|${r.zone}`;
    if (!nmMap.has(key)) {
      nmMap.set(key, {
        mob: r.mob, zone: r.zone,
        level_lo: r.level_lo, level_hi: r.level_hi,
        gate: r.gate, drops: [], steals: [],
      });
    }
    const entry = nmMap.get(key)!;
    const drop: NMDrop = {
      item_id: r.item_id, item_name: r.item_name,
      pct: r.pct, is_ingredient: ingredientIds.has(r.item_id),
    };
    if (r.type === 'mob_steal') entry.steals.push(drop);
    else entry.drops.push(drop);
  }

  return [...nmMap.values()].sort((a, b) => a.zone.localeCompare(b.zone) || a.mob.localeCompare(b.mob));
}
