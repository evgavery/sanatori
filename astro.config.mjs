import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';
import sitemap from '@astrojs/sitemap';

// Свой домен на reg.ru (хостинг Host-Lite, выкладка dist/ в public_html).
// Punycode-форма (`xn--80aayawdelfebp4a.xn--p1ai`) для site указана намеренно —
// именно её увидят машинные клиенты (sitemap, OG, поисковики, SSL-сертификат).
// Браузер сам подменит её на «санаториифнпр.рф» в адресной строке.
export default defineConfig({
  site: 'https://xn--80aayawdelfebp4a.xn--p1ai',
  integrations: [
    icon(),
    sitemap({
      i18n: { defaultLocale: 'ru', locales: { ru: 'ru-RU' } },
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
