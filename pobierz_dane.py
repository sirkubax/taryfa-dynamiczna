"""
Skrypt do pobierania danych godzinowych TGE RDN.

Użycie:
    python pobierz_dane.py <miesiąc> [rok] [--stary]

Przykłady:
    python pobierz_dane.py 12           # grudzień 2025, nowy format
    python pobierz_dane.py 3 2025 --stary   # marzec 2025, stary format
    python pobierz_dane.py 1 2026       # styczeń 2026, nowy format

Opcje:
    --stary    Użyj starego formatu URL (dla miesięcy przed listopad 2025)
"""
import csv
import re
import sys
import calendar
from datetime import date, timedelta

import requests
from lxml import html

# URL dla nowego formatu (od listopada 2025)
URL_NEW = "https://tge.pl/energia-elektryczna-rdn-tge-base?date_start={d}&iframe=1"
# URL dla starego formatu (przed listopad 2025)
URL_OLD = "https://tge.pl/energia-elektryczna-rdn?date_start={d}"


def pl_number_to_float(s: str) -> float | None:
    s = s.strip()
    if s == "-" or s == "":
        return None
    # "3 759,20" -> 3759.20
    s = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    return float(s)


def fetch_day(d: date, url_template: str):
    url = url_template.format(d=d.isoformat())
    print(f"Fetching: {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    
    tree = html.fromstring(r.content)
    
    # Znajdź tabelę z danymi godzinowymi
    table = tree.xpath('//table[@id="footable_kontrakty_godzinowe"]//tbody//tr')
    
    rows = []
    for tr in table:
        cells = tr.xpath('.//td')
        if len(cells) >= 3:
            # Pierwsza kolumna: czas (np. "0-1")
            time_text = cells[0].text_content().strip()
            time_match = re.match(r"(\d{1,2})-(\d{1,2})", time_text)
            if not time_match:
                continue
            h_from = int(time_match.group(1))
            h_to = int(time_match.group(2))
            
            # Druga kolumna: cena
            price_text = cells[1].text_content().strip()
            price = pl_number_to_float(price_text)
            
            # Trzecia kolumna: wolumen
            vol_text = cells[2].text_content().strip()
            vol = pl_number_to_float(vol_text)
            
            rows.append((h_from, h_to, price, vol))

    if len(rows) != 24:
        raise RuntimeError(f"{d}: expected 24 rows, got {len(rows)} (page format may have changed)")

    return rows


def daterange(d1: date, d2: date):
    d = d1
    while d <= d2:
        yield d
        d += timedelta(days=1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Parsowanie argumentów
    use_old_format = "--stary" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    
    month = int(args[0])
    year = int(args[1]) if len(args) > 1 else 2025
    
    if month < 1 or month > 12:
        print("Miesiąc musi być liczbą od 1 do 12")
        sys.exit(1)
    
    # Wybór URL
    url_template = URL_OLD if use_old_format else URL_NEW
    format_info = "stary" if use_old_format else "nowy"
    print(f"Używam {format_info} format URL")
    
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    
    month_str = f"{year}-{month:02d}"

    out_csv = f"tge_rdn_hourly_{month_str}.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "hour_from", "hour_to", "price_pln_per_mwh", "volume_mwh"])

        for d in daterange(start, end):
            day_rows = fetch_day(d, url_template)
            for h_from, h_to, price, vol in day_rows:
                w.writerow([d.isoformat(), h_from, h_to, price, vol])

    print(f"Saved: {out_csv}")
