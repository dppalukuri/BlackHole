import type { APIRoute } from 'astro';

// Editorial articles — kept in sync with travel-radar/index.astro
const editorial = [
  {
    slug: 'uae-mortgaged-car-oman-noc',
    title: 'Driving a Mortgaged Car from the UAE to Oman? You Need a Bank NOC',
    summary: 'Bank-financed cars now require a formal No Objection Certificate at every UAE-Oman land border. Process can take up to two weeks.',
    region: 'UAE → Oman',
    category: 'Border rules',
    publishedDate: '2026-06-07',
    href: '/travel-radar/uae-mortgaged-car-oman-noc/',
  },
];

// Auto-include change sets dropped into src/data/visa-changes/
const changeMods = import.meta.glob('../../data/visa-changes/*.json', { eager: true });
const changes = Object.entries(changeMods)
  .filter(([path]) => !path.includes('.gitkeep'))
  .map(([path, mod]) => {
    const slug = path.split('/').pop()!.replace(/\.json$/, '');
    const data = (mod as any).default ?? mod;
    const summary = data.summary || {};
    const periodLabel = (data.from_date && data.to_date)
      ? `${data.from_date} → ${data.to_date}`
      : `${data.from_snapshot} → ${data.to_snapshot}`;
    return {
      slug,
      title: `Visa Policy Changes: ${periodLabel}`,
      summary: `${summary.total_changes || 0} change(s) detected — ${summary.status_changed_count || 0} status flips, ${summary.days_changed_count || 0} day-limit shifts, ${summary.added_count || 0} new pairs, ${summary.removed_count || 0} removed.`,
      region: 'Auto-tracker',
      category: 'Visa policy changes',
      publishedDate: data.to_date || '',
      href: `/travel-radar/changes/${slug}/`,
    };
  });

const SITE = 'https://wanderwise.techtools365.com';

function escapeXml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function rfc822(dateIso: string): string {
  // Convert YYYY-MM-DD to RFC 822 — assume publish at 12:00 UTC for stability
  if (!dateIso) return new Date().toUTCString();
  try {
    return new Date(`${dateIso}T12:00:00Z`).toUTCString();
  } catch {
    return new Date().toUTCString();
  }
}

export const GET: APIRoute = () => {
  const items = [...changes, ...editorial]
    .filter((a) => a.publishedDate)
    .sort((a, b) => b.publishedDate.localeCompare(a.publishedDate));

  const lastBuildDate = items[0]?.publishedDate
    ? rfc822(items[0].publishedDate)
    : new Date().toUTCString();

  const itemsXml = items
    .map((a) => {
      const url = `${SITE}${a.href}`;
      return [
        '    <item>',
        `      <title>${escapeXml(a.title)}</title>`,
        `      <link>${url}</link>`,
        `      <guid isPermaLink="true">${url}</guid>`,
        `      <pubDate>${rfc822(a.publishedDate)}</pubDate>`,
        `      <category>${escapeXml(a.category)}</category>`,
        `      <description>${escapeXml(`[${a.region}] ${a.summary}`)}</description>`,
        '    </item>',
      ].join('\n');
    })
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>WanderWise Travel Radar</title>
    <link>${SITE}/travel-radar/</link>
    <atom:link href="${SITE}/travel-radar/rss.xml" rel="self" type="application/rss+xml" />
    <description>Border-rule changes, visa-policy updates, and travel advisories — every entry cites authentic government or established media sources.</description>
    <language>en-us</language>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
    <generator>WanderWise (TechTools365)</generator>
${itemsXml}
  </channel>
</rss>
`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
