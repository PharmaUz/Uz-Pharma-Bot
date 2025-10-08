# import requests
# from sqlalchemy.orm import Session
# from database.models import Drug
# from database.db import SessionLocal  # SessionLocal ni db.py dan import qiling

# def fetch_and_create_drugs():
#     session: Session = SessionLocal()
#     try:
#         # 100 ta ma'lumot olish
#         resp = requests.get(
#             "https://api.pharmagency.uz/drug-catalog-api/v1/drugs/search?page=0&size=100"
#         )
#         data = resp.json()["content"]

#         drugs = []
#         for item in data:
#             drug = Drug(
#                 name=item.get("shortName"),
#                 description=item.get("pharmaCotherapeuticGroup"),
#                 manufacturer=item.get("manufacturer"),
#                 dosage_form=item.get("dosageForm"),
#                 strength=item.get("strength"),
#                 price=None,  # API-da yo'q, kerak bo'lsa boshqa joydan olasiz
#                 expiration_date=None,  # API-da yo'q
#                 prescription_required=item.get("prescriptionRequired"),
#                 category=None,  # API-da yo'q
#                 image_url=item.get("imgUrl"),
#                 thumbnail_url=None  # API-da yo'q
#             )
#             drugs.append(drug)

#         session.bulk_save_objects(drugs)
#         session.commit()
#         print(f"{len(drugs)} ta drug bazaga qo'shildi.")
#     except Exception as e:
#         print("Xatolik:", e)
#         session.rollback()
#     finally:
#         session.close()

# if __name__ == "__main__":
#     fetch_and_create_drugs()