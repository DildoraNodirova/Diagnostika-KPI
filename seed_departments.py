from app.database import SessionLocal
from app.models import Region, Department, KPISection


REGION_NAME = "Toshkent"


def get_or_create_region(db):

    region = (
        db.query(Region)
        .filter(Region.name == REGION_NAME)
        .first()
    )

    if region:
        return region

    region = Region(
        name=REGION_NAME,
        director_name="Ali Valiyev",
        director_email="ali.valiyev@example.uz",
        director_phone="",
        password="changeme",
        status="Active",
    )

    db.add(region)
    db.flush()

    return region


def seed_departments():

    db = SessionLocal()

    try:
        region = get_or_create_region(db)

        sections = (
            db.query(KPISection)
            .order_by(KPISection.number)
            .all()
        )

        created = 0
        skipped = 0

        for section in sections:

            existing = (
                db.query(Department)
                .filter(
                    Department.region_id == region.id,
                    Department.name == section.name,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            department = Department(
                name=section.name,
                head=None,
                region_id=region.id,
            )

            db.add(department)
            created += 1

        db.commit()

        print("=" * 60)
        print("BO'LIMLAR (DEPARTMENTS) SEED YAKUNLANDI")
        print("=" * 60)
        print(f"Region: {region.name} (id={region.id})")
        print(f"Yangi bo'limlar: {created}")
        print(f"Mavjud edi (o'tkazib yuborildi): {skipped}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print("XATOLIK:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_departments()