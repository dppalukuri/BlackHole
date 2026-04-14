// @ts-check
import { defineConfig } from 'astro/config';
import preact from '@astrojs/preact';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://calcstack.techtools365.com',
  integrations: [
    preact(),
    sitemap({
      filter: (page) => !page.includes('/404'),
    }),
  ],
});
