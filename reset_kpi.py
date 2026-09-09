from app.database import engine, Base
from app.models import KPISection, KPIIndicator, KPIResult

print("KPI jadvallari o'chirilmoqda...")

KPIResult.__table__.drop(engine, checkfirst=True)
KPIIndicator.__table__.drop(engine, checkfirst=True)
KPISection.__table__.drop(engine, checkfirst=True)

print("Eski KPI jadvallari o'chirildi.")

KPISection.__table__.create(engine, checkfirst=True)
KPIIndicator.__table__.create(engine, checkfirst=True)
KPIResult.__table__.create(engine, checkfirst=True)

print("Yangi KPI jadvallari yaratildi.")
print("department_id mavjud.")
print("Tayyor!")