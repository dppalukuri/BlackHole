/** URL-safe name for a country, shared by the build and the browser: "Côte d'Ivoire" -> "cote-d-ivoire". */
export function countrySlug(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
