from app.database import SessionLocal
from app.models import Region, Department, KPISection
from app.security import hash_password


DEFAULT_PASSWORD = "1234"

REGIONS = [
    {"username": "toshkent", "name": "Toshkent shahri", "director_name": "Ali Valiyev"},
    {"username": "toshkent_v", "name": "Toshkent viloyati", "director_name": ""},
    {"username": "andijon", "name": "Andijon viloyati", "director_name": ""},
    {"username": "buxoro", "name": "Buxoro viloyati", "director_name": ""},
    {"username": "fargona", "name": "Farg'ona viloyati", "director_name": ""},
    {"username": "jizzax", "name": "Jizzax viloyati", "director_name": ""},
    {"username": "xorazm", "name": "Xorazm viloyati", "director_name": ""},
    {"username": "namangan", "name": "Namangan viloyati", "director_name": ""},
    {"username": "navoiy", "name": "Navoiy viloyati", "director_name": ""},
    {"username": "qashqadaryo", "name": "Qashqadaryo viloyati", "director_name": ""},
    {"username": "samarqand", "name": "Samarqand viloyati", "director_name": ""},
    {"username": "sirdaryo", "name": "Sirdaryo viloyati", "director_name": ""},
    {"username": "surxondaryo", "name": "Surxondaryo viloyati", "director_name": ""},
    {"username": "qoraqalpogiston", "name": "Qoraqalpog'iston Respublikasi", "director_name": ""},
]


def get_or_create_region(db, entry):

    region = db.query(Region).filter(Region.username == entry["username"]).first()
    if region:
        return region

    # Avvalgi seed_departments.py "Toshkent" nomi bilan yaratgan regionni qayta ishlatamiz
    if entry["username"] == "toshkent":
        region = db.query(Region).filter(Region.name == "Toshkent").first()
        if region:
            return region

    region = db.query(Region).filter(Region.name == entry["name"]).first()
    if region:
        return region

    region = Region(
        name=entry["name"],
        director_name=entry.get("director_name") or None,
        status="Active",
    )

    db.add(region)
    db.flush()

    return region


def seed_department_structure_for_region(db, region):

    sections = db.query(KPISection).order_by(KPISection.number).all()

    created = 0

    for section in sections:

        existing = (
            db.query(Department)
            .filter(Department.region_id == region.id, Department.name == section.name)
            .first()
        )

        if existing:
            continue

        db.add(Department(name=section.name, head=None, region_id=region.id))
        created += 1

    return created


def seed():

    db = SessionLocal()

    try:
        total_new_departments = 0

        for entry in REGIONS:

            region = get_or_create_region(db, entry)

            if not region.username:
                region.username = entry["username"]

            region.password = hash_password(DEFAULT_PASSWORD)

            if not region.status:
                region.status = "Active"

            db.flush()

            total_new_departments += seed_department_structure_for_region(db, region)

        db.commit()

        print("=" * 60)
        print("HUDUDLAR VA LOGIN MA'LUMOTLARI TAYYORLANDI")
        print("=" * 60)

        for entry in REGIONS:
            print(f"  login: {entry['username']:<18} parol: {DEFAULT_PASSWORD}   ({entry['name']})")

        print()
        print(f"Yangi qo'shilgan bo'limlar (jami): {total_new_departments}")
        print("=" * 60)
        print("DIQQAT: bu standart parol faqat SINOV uchun — ishga tushirishdan oldin almashtiring.")

    except Exception as e:
        db.rollback()
        print("XATOLIK:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()