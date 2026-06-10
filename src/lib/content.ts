import sanatoriumsData from '../../data/sanatoriums.json';
import facilitiesData from '../../data/facilities.json';

export interface Sanatorium {
  id: string;
  name: string;
  city: string;
  region: string;
  address: string;
  photos: string[];
  description: string;
  directions: string[];
  amenities: string[];
  price_from: string;
  cta: string;
}

export interface Facility {
  icon: string;
  category: string;
}

export const sanatoriums = sanatoriumsData.sanatoriums as Sanatorium[];
export const facilities = facilitiesData.items as Record<string, Facility>;
export const facilityCategories = facilitiesData.categories as string[];
export const fallbackIcon = facilitiesData._meta.fallbackIcon as string;

// Порядок и подписи регионов (табы каталога)
export const REGION_ORDER = [
  'Кавказские Минеральные Воды',
  'Калининградская область',
  'Краснодарский край',
];

export function regions(): string[] {
  const present = new Set(sanatoriums.map((s) => s.region));
  return REGION_ORDER.filter((r) => present.has(r));
}

export function bySanatoriumRegion(region: string): Sanatorium[] {
  return sanatoriums.filter((s) => s.region === region);
}

/** Имя иконки Lucide для услуги (с фолбэком). */
export function facilityIcon(name: string): string {
  return facilities[name]?.icon ?? fallbackIcon;
}

/**
 * Фото санатория для рендера. Пути в данных относительные (без BASE_URL) —
 * здесь добавляем base, чтобы корректно работало и на GitHub Pages (/sanatori/),
 * и после переезда на свой домен. Если фото нет — вернётся пустой массив,
 * и карточка покажет фолбэк (градиент + иконка горы).
 */
export function photosFor(s: Sanatorium): string[] {
  const base = import.meta.env.BASE_URL;
  return s.photos.map((p) => (/^https?:\/\//.test(p) ? p : base + p));
}

export function facilityCategory(name: string): string {
  return facilities[name]?.category ?? 'Услуги';
}

/** Услуги санатория, сгруппированные по категориям (в порядке categories). */
export function groupAmenities(amenities: string[]): { category: string; items: string[] }[] {
  return facilityCategories
    .map((category) => ({
      category,
      items: amenities.filter((a) => facilityCategory(a) === category),
    }))
    .filter((g) => g.items.length > 0);
}
