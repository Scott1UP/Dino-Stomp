import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The address the game is served from, for the link-preview tags in index.html, which must be
// full addresses. Netlify sets URL during its builds; set SITE_URL to override it. Without
// either (as in local development, or the Android app) the tags fall back to paths from the root.
const siteUrl = (process.env.SITE_URL ?? process.env.URL ?? '').replace(/\/$/, '');

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'site-url',
      transformIndexHtml: (html) => html.replaceAll('%SITE_URL%', siteUrl),
    },
  ],
});
