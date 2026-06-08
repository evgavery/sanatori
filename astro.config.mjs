import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';

// Деплой на GitHub Pages (project-страница evgavery.github.io/sanatori).
// При переезде на свой домен (reg.ru) — поменять site и вернуть base '/'.
export default defineConfig({
  site: 'https://evgavery.github.io',
  base: '/sanatori/',
  integrations: [icon()],
  vite: {
    plugins: [tailwindcss()],
  },
});
