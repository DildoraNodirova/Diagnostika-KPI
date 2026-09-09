"""
Xodimlar ro'yxatini app.fairtech.uz tizimidan olib, mahalliy bazaga yozadi.

Har bir hudud uchun `kpi/employee-wise-indicator-report` chaqiriladi
(soato majburiy) va natija `employees` jadvaliga yoziladi.

Ishga tushirish:
    venv313\\Scripts\\python.exe sync_employees.py
    venv313\\Scripts\\python.exe sync_employees.py --date1 01-01-2026 --date2 02-09-2026
"""

import argparse
from datetime import date

from app import fairtech, models
from app.database import SessionLocal
from app.routers.fairtech import _local_regions, _match_region


def parse_args():
    today = date.today()

    parser = argparse.ArgumentParser(description="Fairtech xodimlar sinxronizatsiyasi")

    parser.add_argument("--date1", default=f"01-01-{today.year}")
    parser.add_argument("--date2", default=today.strftime("%d-%m-%Y"))
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Mavjud xodimlarni o'chirmaslik (odatda ro'yxat to'liq almashtiriladi)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    date1, date2 = args.date1, args.date2

    print(f"Davr: {date1} .. {date2}")

    db = SessionLocal()

    try:
        report = fairtech.region_report(date1, date2)

        index = _local_regions(db)

        if not args.keep:
            removed = db.query(models.Employee).delete()
            db.commit()
            print(f"Eski xodimlar o'chirildi: {removed}")

        # Bazadagi mavjud xodimlar (takrorlanmasligi uchun)
        seen = {
            (e.fullname, e.region_id)
            for e in db.query(models.Employee).all()
        }

        total = 0
        skipped_regions = []

        for row in report.get("rows", []):
            info = row.get("region") or {}

            soato = info.get("soato")

            local = _match_region(soato, info.get("nameLt"), index)

            if local is None:
                skipped_regions.append(f"{info.get('nameLt')} (soato={soato})")
                continue

            payload = fairtech.employee_report(date1, date2, soato)

            added = 0

            for entry in payload.get("rows", []):
                person = entry.get("employee") or {}

                fullname = (person.get("fullName") or "").strip()

                if not fullname:
                    continue

                key = (fullname, local.id)

                if key in seen:
                    continue

                seen.add(key)

                db.add(models.Employee(
                    fullname=fullname,
                    position=person.get("positionName"),
                    region_id=local.id,
                    status="Active",
                ))

                added += 1

            db.commit()

            total += added

            print(f"  {local.name:<32} xodimlar: {added}")

        if skipped_regions:
            print("\nBazada topilmagan hududlar (o'tkazib yuborildi):")
            for name in skipped_regions:
                print(f"  ! {name}")

        print(f"\nTayyor. Jami xodimlar: {total}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
