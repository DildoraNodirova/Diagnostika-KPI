"""
KPI tuzilmasini app.fairtech.uz tizimidan olib, mahalliy bazaga yozadi.

Yuqori tizimdagi 16 ta kategoriya -> kpi_sections
Har bir kategoriya ichidagi ko'rsatkichlar -> kpi_indicators
Har bir hudud x ko'rsatkich natijasi -> kpi_results

Ishga tushirish:
    venv313\\Scripts\\python.exe sync_fairtech.py
    venv313\\Scripts\\python.exe sync_fairtech.py --date1 01-01-2026 --date2 02-09-2026
"""

import argparse
from datetime import date, datetime

from app import fairtech, models
from app.database import SessionLocal
from app.routers.fairtech import _local_regions, _match_region, _number, _text


# Yakuniy natija - bu alohida kategoriya emas, balki umumiy yig'indi.
SKIP_COLUMNS = {"YAKUNIY_NATIJA"}

LANG = "lt"


def parse_args():
    today = date.today()

    parser = argparse.ArgumentParser(description="Fairtech KPI sinxronizatsiyasi")

    parser.add_argument(
        "--date1",
        default=f"01-01-{today.year}",
        help="Boshlanish sanasi (KUN-OY-YIL)",
    )
    parser.add_argument(
        "--date2",
        default=today.strftime("%d-%m-%Y"),
        help="Tugash sanasi (KUN-OY-YIL)",
    )
    parser.add_argument(
        "--period",
        default=None,
        help="Natijalar yoziladigan davr (YYYY-MM). Odatda --date2 oyidan olinadi.",
    )

    return parser.parse_args()


def weight_of(value) -> float:
    """'20%' yoki '25' -> 20.0 / 25.0"""

    number = _number(str(value).replace("%", "").strip() if value is not None else None)

    return number or 0.0


def split_rows(rows: list[dict]) -> tuple[dict | None, list[dict]]:
    """Sarlavha qatori (masalan '2.') va ko'rsatkich qatorlarini ajratadi."""

    header = None
    items = []

    for row in rows:
        order_no = (row.get("orderNo") or "").strip().rstrip(".")

        # "2" -> sarlavha, "2.1" -> ko'rsatkich
        if "." in order_no:
            items.append(row)
        elif header is None:
            header = row
        else:
            items.append(row)

    # Ichki ko'rsatkichlar bo'lmasa, sarlavhaning o'zi ko'rsatkich bo'ladi.
    if not items and header is not None:
        items = [header]

    return header, items


def main():
    args = parse_args()

    date1, date2 = args.date1, args.date2

    period = args.period or datetime.strptime(date2, "%d-%m-%Y").strftime("%Y-%m")
    result_date = datetime.strptime(date2, "%d-%m-%Y").date()

    print(f"Davr: {date1} .. {date2}  (period={period})")

    db = SessionLocal()

    try:
        report = fairtech.region_report(date1, date2)

        columns = [
            column for column in report.get("columns", [])
            if column.get("code") not in SKIP_COLUMNS
        ]

        index = _local_regions(db)

        # Hududlarni moslashtirish
        region_rows = []

        for row in report.get("rows", []):
            info = row.get("region") or {}
            local = _match_region(info.get("soato"), info.get("nameLt"), index)

            if local:
                region_rows.append((info.get("soato"), local))
            else:
                print(f"  ! bazada topilmadi: {info.get('nameLt')} (soato={info.get('soato')})")

        print(f"Kategoriyalar: {len(columns)}, moslashgan hududlar: {len(region_rows)}")

        # 1) Eski KPI tuzilmasini tozalash (natijalar cascade bilan o'chadi)
        db.query(models.KPIResult).delete()
        db.query(models.KPIIndicator).delete()
        db.query(models.KPISection).delete()
        db.commit()

        # 2) Kategoriyalar va ko'rsatkichlarni yaratish
        #    Tuzilma barcha hududlarda bir xil, shuning uchun bitta hududdan olinadi.
        reference_soato = region_rows[0][0] if region_rows else None

        indicators_by_column: dict[str, list[tuple[str, models.KPIIndicator]]] = {}

        for number, column in enumerate(columns, start=1):
            code = column["code"]

            detail = fairtech.indicator_cell(date1, date2, reference_soato, code)

            header, items = split_rows(detail.get("rows", []))

            section = models.KPISection(
                number=number,
                name=_text(column.get("name"), LANG) or code,
                weight=weight_of(header.get("vazn_ball") if header else None),
            )

            db.add(section)
            db.flush()

            created = []

            for item in items:
                indicator = models.KPIIndicator(
                    section_id=section.id,
                    name=_text(item.get("korsatkich"), LANG) or "-",
                    unit="ball",
                    plan=weight_of(item.get("vazn_ball")),
                    weight=weight_of(item.get("vazn_ball")),
                )

                db.add(indicator)
                db.flush()

                created.append(((item.get("orderNo") or "").strip(), indicator))

            indicators_by_column[code] = created

            print(f"  [{number:>2}] {section.name[:52]:<52} ko'rsatkich: {len(created)}")

        db.commit()

        # 3) Har bir hudud uchun natijalarni yozish
        total_results = 0

        for soato, region in region_rows:

            region_results = 0

            for column in columns:
                code = column["code"]

                detail = fairtech.indicator_cell(date1, date2, soato, code)

                _, items = split_rows(detail.get("rows", []))

                by_order = {
                    (item.get("orderNo") or "").strip(): item
                    for item in items
                }

                for order_no, indicator in indicators_by_column.get(code, []):
                    item = by_order.get(order_no)

                    if item is None:
                        continue

                    actual = _number(item.get("olingan_ball"))

                    if actual is None:
                        continue

                    db.add(models.KPIResult(
                        indicator_id=indicator.id,
                        region_id=region.id,
                        plan=weight_of(item.get("vazn_ball")),
                        actual=actual,
                        date=result_date,
                        period=period,
                    ))

                    region_results += 1

            db.commit()

            total_results += region_results

            print(f"  {region.name:<32} natijalar: {region_results}")

        print(f"\nTayyor. Jami natijalar: {total_results}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
