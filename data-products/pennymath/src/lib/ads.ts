/**
 * AdSense slot configuration.
 *
 * The layout ships three ad units (left rail, right rail, in-content). Each
 * needs a real slot ID created in the AdSense dashboard. Until one is set, its
 * `<ins>` is not rendered at all: an unconfigured slot never fills, so the page
 * would otherwise show a labelled "Ad" box above ~620px of empty column on
 * desktop, and `adsbygoogle.push()` would fire against an invalid slot.
 *
 * The AdSense script itself still loads (see AdScripts.astro) — it is what
 * proves site ownership and powers Auto Ads, and is unaffected by slot IDs.
 *
 * HOW TO ENABLE (blocked on AdSense approval as of 2026-09): the account must
 * be approved for this site before ad units can be created or served. Once it
 * is, create the units in AdSense, paste each `data-ad-slot` value below (a
 * numeric string), and rebuild — the rails reappear automatically.
 */
export const ADSENSE_CLIENT = 'ca-pub-9446467058878539';

/** Value a slot holds before a real AdSense unit ID is pasted in. */
const PLACEHOLDER = /^REPLACE_/;

export const AD_SLOTS = {
  leftRail: 'REPLACE_LEFT_RAIL_SLOT_ID',
  rightRail: 'REPLACE_RIGHT_RAIL_SLOT_ID',
  inline: 'REPLACE_INLINE_SLOT_ID',
} as const;

export function isAdSlotConfigured(slot: string): boolean {
  return Boolean(slot) && !PLACEHOLDER.test(slot);
}

/** True when at least one unit is live — decides whether to lay out ad rails. */
export const anyAdSlotConfigured = Object.values(AD_SLOTS).some(isAdSlotConfigured);
