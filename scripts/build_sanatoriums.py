#!/usr/bin/env python3
"""Собирает data/sanatoriums.json из исходного CSV заказчика.

Запуск:  python3 scripts/build_sanatoriums.py
Источник: files/Информация_по_санаториям_от_НК_ТРАНС.csv
Результат: data/sanatoriums.json

CSV устроен иерархически: строки-заголовки регионов/городов (в первом столбце
текст, остальные пустые) и строки-данные (первый столбец — номер). Лечебный
профиль разделён «;», услуги — двойными пробелами. Часть полей многострочные —
поэтому используем настоящий CSV-парсер, а не построчное чтение.
"""
import csv
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "files", "Информация_по_санаториям_от_НК_ТРАНС.csv")
OUT = os.path.join(ROOT, "data", "sanatoriums.json")
UPDATED = "2026-06-02"

CITY_SLUG = {
    "Ессентуки": "essentuki",
    "Железноводск": "zheleznovodsk",
    "Кисловодск": "kislovodsk",
    "Пятигорск": "pyatigorsk",
    "Светлогорск": "svetlogorsk",
    "Сочи": "sochi",
}
CITY_REGION = {
    "Ессентуки": "Кавказские Минеральные Воды",
    "Железноводск": "Кавказские Минеральные Воды",
    "Кисловодск": "Кавказские Минеральные Воды",
    "Пятигорск": "Кавказские Минеральные Воды",
    "Светлогорск": "Калининградская область",
    "Сочи": "Краснодарский край",
}


def clean_ws(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def clean_name(s):
    s = clean_ws(s)
    # убираем одиночную «висячую» кавычку — артефакт исходных данных
    if s.count('"') % 2 == 1:
        idx = s.rfind('"')
        s = (s[:idx] + s[idx + 1:]).strip()
    return s


def split_directions(s):
    out = []
    for p in re.split(r"[;\n]+", s or ""):
        p = clean_ws(p).rstrip(".").strip()
        if p:
            out.append(p[0].upper() + p[1:])
    return out


def split_amenities(s):
    return [clean_ws(p) for p in re.split(r"\s{2,}", (s or "").strip()) if clean_ws(p)]


def main():
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    current_city = None
    sanatoriums = []

    for r in rows:
        cells = (r + [""] * 6)[:6]
        col0, name, addr, desc, prof, serv = (cells[0].strip(), cells[1].strip(),
                                              cells[2].strip(), cells[3], cells[4], cells[5])

        if not any(c.strip() for c in cells):
            continue
        if col0 == "№" or col0.startswith("Информация о санаториях"):
            continue

        is_header = (col0 and not col0.isdigit() and not name and not addr
                     and not desc.strip() and not prof.strip() and not serv.strip())
        if is_header:
            if "минеральные воды" in col0.lower():
                continue  # зонтичный регион — пропускаем, город задаст следующая строка
            current_city = col0
            continue

        if col0.isdigit() and name:
            city = current_city or ""
            region = CITY_REGION.get(city) or (addr.split(",")[-1].strip() if addr else "")
            slug = CITY_SLUG.get(city) or re.sub(r"[^a-z0-9]+", "-", city.lower())
            sanatoriums.append({
                "id": f"{slug}-{col0}",
                "name": clean_name(name),
                "city": city,
                "region": region,
                "address": clean_ws(addr),
                "photos": [],
                "description": clean_ws(desc),
                "directions": split_directions(prof),
                "amenities": split_amenities(serv),
                "price_from": "",
                "cta": "Хочу сюда",
            })

    data = {
        "meta": {
            "title": "Санатории ФНПР",
            "source": "files/Информация_по_санаториям_от_НК_ТРАНС.csv",
            "updated": UPDATED,
            "count": len(sanatoriums),
            "note": "Фото добавляются в массив photos; цена — в price_from при наличии.",
        },
        "sanatoriums": sanatoriums,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Записано {len(sanatoriums)} объектов → {os.path.relpath(OUT, ROOT)}")
    for city, n in Counter(s["city"] for s in sanatoriums).items():
        print(f"  {city}: {n}")


if __name__ == "__main__":
    main()
