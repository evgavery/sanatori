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

function hashId(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return h;
}

// Подборка реальных фото отелей/курортов с Unsplash (проверены, отдают 200).
// Используются как временная замена, пока заказчик не пришлёт настоящие фото.
const STOCK_PHOTO_IDS = [
  '1566073771259-6a8506099945',
  '1571003123894-1f0594d2b5d9',
  '1582719478250-c89cae4dc85b',
  '1520250497591-112f2f40a3f4',
  '1551882547-ff40c63fe5fa',
  '1564501049412-61c2a3083791',
  '1542314831-068cd1dbfeeb',
  '1455587734955-081b22074882',
  '1535827841776-24afc1e255ac',
  '1571896349842-33c89424de2d',
  '1611892440504-42a792e24d32',
  '1540541338287-41700207dee6',
  '1582719508461-905c673771fd',
  '1445019980597-93fa8acb246c',
  '1578683010236-d716f9a3f461',
  '1551918120-9739cb430c6d',
  '1596178065887-1198b6148b2b',
  '1568084680786-a84f91d1153c',
  '1559599238-308793637427',
];

const stockUrl = (id: string, w = 800) =>
  `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=${w}&q=70`;

/**
 * Фото санатория. Если реальных фото в данных нет — отдаём подборку фото
 * отелей/курортов с Unsplash, детерминированную по id (3 разных кадра).
 * Как только заказчик пришлёт настоящие фото и они попадут в data/sanatoriums.json,
 * вернутся именно они.
 */
export function photosFor(s: Sanatorium): string[] {
  if (s.photos.length > 0) return s.photos;
  const h = hashId(s.id);
  const n = STOCK_PHOTO_IDS.length;
  // 7 взаимно просто с 19 → три разных индекса
  return [0, 1, 2].map((k) => stockUrl(STOCK_PHOTO_IDS[(h + k * 7) % n]));
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
