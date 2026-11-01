/**
 * AdSense slot configuration. Each `<ins>` needs a real slot ID from the AdSense
 * dashboard. Until one is set, the unit is not rendered at all: an unconfigured
 * slot never fills, so it would only show as an empty box.
 *
 * The AdSense script itself still loads (see AdScripts.astro), which is what
 * proves site ownership and powers Auto Ads.
 */
export const ADSENSE_CLIENT = 'ca-pub-9446467058878539';

export const AD_SLOTS = {
  inline: 'REPLACE_INLINE_SLOT_ID',
  midContent: 'REPLACE_MID_CONTENT_SLOT_ID',
} as const;

export function isAdSlotConfigured(slot: string): boolean {
  return Boolean(slot) && !/^REPLACE_/.test(slot);
}
