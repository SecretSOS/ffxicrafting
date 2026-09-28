const LOW_WORDS = new Set(['of', 'the', 'and', 'a', 'for', 'in', 'on', 'at', 'by', 'to', 'from']);

export function pretty(name: string): string {
  if (!name) return '';
  const words = name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).split(' ');
  return words.map((w, i) => (i > 0 && LOW_WORDS.has(w.toLowerCase())) ? w.toLowerCase() : w).join(' ');
}

export function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

export function fmtPct(p: number | null | undefined): string {
  if (p == null) return '—';
  if (p >= 10) return `${p.toFixed(1)}%`;
  if (p >= 1) return `${p.toFixed(2)}%`;
  return `${p.toFixed(3)}%`;
}

export function fmtGil(g: number | null | undefined): string {
  if (!g) return '';
  return `${g.toLocaleString('en-US')}g`;
}

export function fmtLevel(lo: number | null, hi: number | null): string {
  if (lo == null) return '';
  if (hi == null || lo === hi) return String(lo);
  return `${lo}–${hi}`;
}

export function itemUrl(id: number, name: string): string {
  return `/item/${id}-${slugify(name.replace(/_/g, ' '))}`;
}

export function iconPath(itemId: number): string {
  return `/icons/${itemId}.png`;
}
