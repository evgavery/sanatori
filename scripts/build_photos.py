#!/usr/bin/env python3
"""Готовит фото санаториев для сайта: оптимизирует и раскладывает по id.

Запуск:  python3 scripts/build_photos.py
Источник: files/Фото санаториев / (оригиналы заказчика, только локально — в .gitignore)
Результат: public/photos/<город-название>/1.jpg, 2.jpg, … (оптимизированные, в репозитории)

Что делает:
- сопоставляет папки заказчика (город → санаторий) с id из data/sanatoriums.json;
- внутри каждого санатория выбирает обложкой (1.jpg) главный фасадный кадр —
  как правило это самый «тяжёлый» исходник (профессиональный общий план),
  остальные нумерует естественным порядком (2.jpg, 3.jpg, …);
- приводит все форматы (jpg/jpeg/jfif/webp/JPG) к единому .jpg, ужимает до
  макс. 1280px по большей стороне и пережимает с качеством 80 — чтобы сайт
  грузился быстро (оригиналы остаются нетронутыми в files/);
- дополнительно кладёт cover.jpg — облегчённую обложку (≈800px) для карточки
  каталога, чтобы не грузить туда полноразмерный кадр (полные 1.jpg…N.jpg
  используются в галерее/лайтбоксе).

После прогона пересоберите каталог: `python3 scripts/build_sanatoriums.py`
(он сам подтянет фото из public/photos/ в массив photos каждого санатория).

Нужен macOS-овский `sips` (есть из коробки).
"""
import os
import re
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "files", "Фото санаториев ")  # внимание: пробел в конце имени папки
OUT = os.path.join(ROOT, "public", "photos")

MAX_SIDE = 1280    # px по большей стороне для галереи/лайтбокса (меньшие не растягиваем)
COVER_SIDE = 800   # px для облегчённой обложки карточки (cover.jpg) — карточка ~380px (×2 retina)
QUALITY = 80       # качество JPEG

# Путь папки заказчика (относительно SRC) → id санатория из data/sanatoriums.json.
# «Кирова» встречается и в Железноводске, и в Кисловодске — поэтому ключ полный.
FOLDER_TO_ID = {
    "КавМинводы/Ессентуки/Виктория": "essentuki-1",
    "КавМинводы/Ессентуки/Целебный ключ": "essentuki-2",
    "КавМинводы/Ессентуки/Надежда": "essentuki-3",
    "КавМинводы/Ессентуки/Анджиевского": "essentuki-4",
    "КавМинводы/Ессентуки/Вилла Герман": "essentuki-5",
    "КавМинводы/Железноводск/30 летия Победы": "zheleznovodsk-1",
    "КавМинводы/Железноводск/Бальнеогрязелечебница": "zheleznovodsk-2",
    "КавМинводы/Железноводск/Дубрава": "zheleznovodsk-3",
    "КавМинводы/Железноводск/Здоровье": "zheleznovodsk-4",
    "КавМинводы/Железноводск/Кирова": "zheleznovodsk-5",
    "КавМинводы/Железноводск/Тельмана": "zheleznovodsk-6",
    "КавМинводы/Железноводск/Эльбрус": "zheleznovodsk-7",
    "КавМинводы/Кисловодск/Димитрова": "kislovodsk-1",
    "КавМинводы/Кисловодск/Кирова": "kislovodsk-2",
    "КавМинводы/Кисловодск/Москва": "kislovodsk-3",
    "КавМинводы/Кисловодск/Нарзан": "kislovodsk-4",
    "КавМинводы/Кисловодск/Пикет": "kislovodsk-5",
    "КавМинводы/Пятигорск/Лермонтова": "pyatigorsk-1",
    "КавМинводы/Пятигорск/Искра": "pyatigorsk-2",
    "КавМинводы/Пятигорск/Лесная поляна": "pyatigorsk-3",
    "КавМинводы/Пятигорск/Родник": "pyatigorsk-4",
    "Светлогорск/Отрадное": "svetlogorsk-1",
    "Светлогорск/Пансионат Волна": "svetlogorsk-2",
    "Сочи/Адлеркурорт": "sochi-1",
    "Сочи/Металлург": "sochi-2",
}

# id санатория → имя папки с фото (латиницей, «город-название»), чтобы папку
# было легко опознать при добавлении/удалении фото. Используется и в
# build_sanatoriums.py (импортируется оттуда) — единый источник истины.
ID_TO_SLUG = {
    "essentuki-1": "essentuki-viktoriya",
    "essentuki-2": "essentuki-tselebny-klyuch",
    "essentuki-3": "essentuki-nadezhda",
    "essentuki-4": "essentuki-anzhievskogo",
    "essentuki-5": "essentuki-villa-german",
    "zheleznovodsk-1": "zheleznovodsk-30-let-pobedy",
    "zheleznovodsk-2": "zheleznovodsk-balneo",
    "zheleznovodsk-3": "zheleznovodsk-dubrava",
    "zheleznovodsk-4": "zheleznovodsk-zdorovye",
    "zheleznovodsk-5": "zheleznovodsk-kirova",
    "zheleznovodsk-6": "zheleznovodsk-telmana",
    "zheleznovodsk-7": "zheleznovodsk-elbrus",
    "kislovodsk-1": "kislovodsk-dimitrova",
    "kislovodsk-2": "kislovodsk-kirova",
    "kislovodsk-3": "kislovodsk-moskva",
    "kislovodsk-4": "kislovodsk-narzan",
    "kislovodsk-5": "kislovodsk-piket",
    "pyatigorsk-1": "pyatigorsk-lermontova",
    "pyatigorsk-2": "pyatigorsk-iskra",
    "pyatigorsk-3": "pyatigorsk-lesnaya-polyana",
    "pyatigorsk-4": "pyatigorsk-rodnik",
    "svetlogorsk-1": "svetlogorsk-otradnoe",
    "svetlogorsk-2": "svetlogorsk-volna",
    "sochi-1": "sochi-adlerkurort",
    "sochi-2": "sochi-metallurg",
}

IMG_EXT = {".jpg", ".jpeg", ".jfif", ".webp", ".png"}


def natural_key(name):
    """Естественная сортировка: 'Фото 2' < 'Фото 10'."""
    parts = re.split(r"(\d+)", name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def list_images(folder):
    files = []
    for fn in os.listdir(folder):
        if fn.startswith("."):
            continue
        if os.path.splitext(fn)[1].lower() in IMG_EXT:
            files.append(os.path.join(folder, fn))
    return files


def ordered_photos(files):
    """Обложка — самый «тяжёлый» исходник (общий план фасада), остальные —
    естественным порядком имён."""
    if not files:
        return []
    cover = max(files, key=lambda p: os.path.getsize(p))
    rest = sorted((f for f in files if f != cover), key=lambda p: natural_key(os.path.basename(p)))
    return [cover] + rest


def max_side(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
        capture_output=True, text=True,
    ).stdout
    nums = [int(n) for n in re.findall(r"pixel(?:Width|Height):\s*(\d+)", out)]
    return max(nums) if nums else 0


def convert(src, dst, side=MAX_SIDE):
    cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(QUALITY)]
    if max_side(src) > side:
        cmd += ["-Z", str(side)]
    cmd += [src, "--out", dst]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    if not os.path.isdir(SRC):
        raise SystemExit(f"Нет папки с оригиналами: {SRC}")

    # Полностью пересобираем public/photos из исходников.
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    total_files = 0
    empty = []
    for folder_rel, sid in FOLDER_TO_ID.items():
        folder = os.path.join(SRC, *folder_rel.split("/"))
        if not os.path.isdir(folder):
            empty.append((sid, folder_rel, "нет папки"))
            continue
        photos = ordered_photos(list_images(folder))
        if not photos:
            empty.append((sid, folder_rel, "нет изображений"))
            continue
        slug = ID_TO_SLUG[sid]
        dest_dir = os.path.join(OUT, slug)
        os.makedirs(dest_dir, exist_ok=True)
        for i, src in enumerate(photos, start=1):
            convert(src, os.path.join(dest_dir, f"{i}.jpg"))
            total_files += 1
        # Облегчённая обложка карточки (≈800px) — чтобы в каталог не грузить
        # полноразмерный кадр; полный 1.jpg остаётся для галереи/лайтбокса.
        # Делаем только если исходник реально крупнее 800px — иначе обложка
        # совпала бы с 1.jpg (карточка возьмёт его как фолбэк).
        cover_note = ""
        if max_side(photos[0]) > COVER_SIDE:
            convert(photos[0], os.path.join(dest_dir, "cover.jpg"), side=COVER_SIDE)
            cover_note = " + обложка"
        print(f"  {slug:<30} ← {folder_rel}  ({len(photos)} фото{cover_note})")

    print(f"\nГотово: {total_files} фото для {len(FOLDER_TO_ID) - len(empty)} санаториев "
          f"→ {os.path.relpath(OUT, ROOT)}")
    if empty:
        print("\n⚠ Без фото:")
        for sid, rel, why in empty:
            print(f"  {sid}: {why} ({rel})")


if __name__ == "__main__":
    main()
