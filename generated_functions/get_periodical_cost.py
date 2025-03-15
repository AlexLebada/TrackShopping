from utils import get_mongo_db
import datetime


def get_periodical_cost(collection_name: str, start_date: str, end_date: str, user: str):
    """This is an already built-in query to retrieve total cost by period.
    collection_name: "receipts" for complete data or "non-receipts" for incomplete data, which was previously provided by user
    Format date args: 2022-02-09 (year-month-day)"""
    collection = collection_name
    db = get_mongo_db()
    results = []
    total_cost = 0
    monthly_spent = db[collection].find(
        {"date": {"$gte": start_date, "$lte": end_date},
         "user": user},  # Filter condition
        {"total_cost": 1, "date": 1, "_id": 0}  # Field projection
    )
    for doc in monthly_spent:
        if isinstance(doc["total_cost"], float):
            total_cost = total_cost + doc["total_cost"]

    return total_cost


#new_date = datetime.date.today() - datetime.timedelta(days=30)
#print(get_periodical_cost("receipts", str(datetime.date.today() - datetime.timedelta(days=30)), str(datetime.date.today()), 'Giorgio'))