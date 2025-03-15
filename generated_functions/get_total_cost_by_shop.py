from utils import get_mongo_db

def get_total_cost_by_shop(collection_name, shop_name, user=None):
    """
    This query is used to retrieve the total cost of purchases made at a specific shop.
    
    Args:
        collection_name: str - Name of the collection to query ('receipts' or 'non-receipts')
        shop_name: str - Name of the shop to filter by
        user: str, optional - Username to filter results for a specific user
        
    Returns:
        float - The total cost of all receipts from the specified shop
    """
    db = get_mongo_db()
    
    # Validate collection name
    if collection_name not in ["receipts", "non-receipts"]:
        raise ValueError("Collection name must be either 'receipts' or 'non-receipts'")
    
    collection = db[collection_name]
    
    # Build the query filter
    query_filter = {"shop_place": shop_name}
    
    # Add user filter if provided
    if user:
        query_filter["user"] = user
    
    # Use the aggregation pipeline to sum up the total_cost
    pipeline = [
        {"$match": query_filter},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$total_cost"}
        }}
    ]
    
    result = list(collection.aggregate(pipeline))
    
    # Return 0 if no receipts found, otherwise return the total
    if not result:
        return 0
    
    return result[0]["total"]

if __name__ == "__main__":
    # Test with some sample parameters
    print(get_total_cost_by_shop("receipts", "Walmart"))