import asyncio
import aiohttp
from datetime import datetime
from database.models import Drug
from database.db import async_session

# API endpoint for fetching drug data
API_URL = "https://api.pharmagency.uz/drug-catalog-api/v2/referent-price/all"


async def fetch_and_create_drugs(page_size=100):
    """
    Fetch drugs from API and save them to the database.
    
    Args:
        page_size (int): Number of items to fetch per page
    """
    page = 0
    total_added = 0

    async with aiohttp.ClientSession() as http_session:
        async with async_session() as db:
            while True:
                print(f"📦 Fetching page {page}...")

                try:
                    # Make GET request to API
                    async with http_session.get(
                        f"{API_URL}?page={page}&size={page_size}"
                    ) as resp:
                        # Check if response is successful
                        if resp.status != 200:
                            print(f"❌ Invalid server response: {resp.status}")
                            break

                        data = await resp.json()
                        result = data.get("result")

                        # Validate response structure
                        if not result or "content" not in result:
                            print("⚠️ No content found in response.")
                            break

                        content = result["content"]
                        
                        # Check if there's data to process
                        if not content:
                            print("✅ No more data found, stopping.")
                            break

                        drugs = []
                        
                        # Process each drug item
                        for item in content:
                            # Convert prescription type: 'Retsipli' -> True, 'Retsiptsiz' -> False
                            prescription_value = item.get("prescription")
                            is_prescription = (
                                True if prescription_value == "Retsipli" else False
                            )

                            # Convert expiration_date to datetime.date format
                            raw_date = item.get("priceDate")
                            expiration_date = None
                            if raw_date:
                                try:
                                    expiration_date = datetime.fromisoformat(
                                        raw_date
                                    ).date()
                                except Exception:
                                    expiration_date = None

                            # Create Drug object
                            drug = Drug(
                                drug_id=item.get("drugId"),
                                name=item.get("name"),
                                description=item.get("trademark"),
                                manufacturer=item.get("manufacturer"),
                                dosage_form=None,
                                strength=None,
                                price=item.get("priceBase") or item.get("price"),
                                expiration_date=expiration_date,
                                prescription_required=is_prescription,
                                category=item.get("currency"),
                                image_url=item.get("imgUrl"),
                                thumbnail_url=None,
                            )
                            drugs.append(drug)

                        # Save all drugs to database
                        db.add_all(drugs)
                        await db.commit()
                        total_added += len(drugs)

                        print(
                            f"✅ {len(drugs)} drugs added to database "
                            f"(total: {total_added})."
                        )

                        # Check if this is the last page
                        if result.get("last", True):
                            print("🏁 Loading completed.")
                            break

                        page += 1

                except Exception as e:
                    print("❌ Error occurred:", e)
                    await db.rollback()
                    break

    print(f"🎉 Total of {total_added} drugs added to database.")


if __name__ == "__main__":
    asyncio.run(fetch_and_create_drugs(page_size=50))