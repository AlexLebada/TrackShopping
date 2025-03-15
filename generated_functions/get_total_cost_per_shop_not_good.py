from utils import get_mongo_db
from typing import Dict

def get_total_cost_per_shop(user: str = None) -> Dict[str, float]:
    """
    This query calculates the total cost per shop location.
    
    It aggregates costs from both receipts and non-receipts collections,
    grouped by shop_place.
    
    Args:
        user: str, optional - If provided, results will be filtered for this specific user
              If not provided, results will include all users
              
    Returns:
        Dict[str, float] - A dictionary where keys are shop locations and values are the 
        total costs for each location
    """
    db = get_mongo_db()
    
    # Initialize result dictionary
    total_cost_per_shop = {}
    
    # Define collections to query
    collections = ["receipts", "non-receipts"]
    
    # Create match condition based on user parameter
    match_condition = {} if user is None else {"user": user}
    
    # Process each collection
    for collection_name in collections:
        collection = db[collection_name]
        
        # MongoDB aggregation pipeline to sum total_cost by shop_place
        pipeline = [
            {"$match": match_condition},
            {"$group": {
                "_id": "$shop_place",
                "total": {"$sum": "$total_cost"}
            }}
        ]
        
        # Execute aggregation
        results = collection.aggregate(pipeline)
        
        # Update the total_cost_per_shop dictionary with results
        for result in results:
            shop = result["_id"]
            cost = result["total"]
            
            if shop in total_cost_per_shop:
                total_cost_per_shop[shop] += cost
            else:
                total_cost_per_shop[shop] = cost
    
    return total_cost_per_shop

if __name__ == "__main__":
    # Test the function
    result = get_total_cost_per_shop()
    print("Total cost per shop location for all users:")
    for shop, total in result.items():
        print(f"{shop}: {total}")
    
    # Test with a specific user if needed
    # result_user = get_total_cost_per_shop(user="some_username")
    # print("\nTotal cost per shop location for specific user:")
    # for shop, total in result_user.items():
    #     print(f"{shop}: {total}")