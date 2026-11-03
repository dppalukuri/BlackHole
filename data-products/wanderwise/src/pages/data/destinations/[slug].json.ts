import type { APIRoute, GetStaticPaths } from 'astro';
import { visaMatrix } from '../../../lib/visa-data';
import { countrySlug } from '../../../lib/slug';

/**
 * One small file per destination: what each passport needs to enter it.
 * The visa checker fetches only the destination someone picks, instead of
 * downloading the whole 199 x 199 matrix before it can be used.
 */
export const getStaticPaths: GetStaticPaths = () => {
  const destinations = [...new Set(Object.values(visaMatrix).flatMap((row) => Object.keys(row)))];
  const bySlug = new Map<string, string>();
  for (const destination of destinations) {
    const slug = countrySlug(destination);
    if (bySlug.has(slug)) throw new Error(`${bySlug.get(slug)} and ${destination} share the slug "${slug}"`);
    bySlug.set(slug, destination);
  }
  return [...bySlug].map(([slug, destination]) => ({ params: { slug }, props: { destination } }));
};

export const GET: APIRoute = ({ props }) => {
  const column: Record<string, string | number> = {};
  for (const [passport, row] of Object.entries(visaMatrix)) {
    const requirement = row[props.destination as string];
    if (requirement !== undefined) column[passport] = requirement;
  }
  return new Response(JSON.stringify(column), { headers: { 'Content-Type': 'application/json' } });
};
