from pymongo import MongoClient
import config

# MongoDB কানেকশন
client = MongoClient(config.MONGO_URI)
db = client['cartspy_db']
users_collection = db['users']

def get_or_create_user(user_id, username=None):
    """ইউজার ডেটাবেসে না থাকলে নতুন প্রোফাইল তৈরি করবে"""
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "username": username,
            "country": None,
            "language": None,
            "search_count": 0,
            "premium_status": False
        }
        users_collection.insert_one(user)
        return user
    return user

def update_profile(user_id, country, language):
    """ইউজারের দেশ ও ভাষা আপডেট করার জন্য (নাম ফিক্স করা হয়েছে)"""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"country": country, "language": language}}
    )

def get_search_count(user_id):
    """ইউজার কতবার সার্চ করেছে তা চেক করবে"""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("search_count", 0) if user else 0

def increment_search_count(user_id):
    """প্রতি সফল সার্চের পর কাউন্টার ১ বাড়াবে"""
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"search_count": 1}}
    )

def check_free_limit(user_id):
    """ইউজার ফ্রি ট্রায়াল (২ বার) পাবে কিনা চেক করবে"""
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return True
    
    if user.get("premium_status", False):
        return True
        
    if user.get("search_count", 0) < 2:
        return True
        
    return False

def make_user_premium(user_id):
    """পেমেন্ট সফল হলে ইউজারকে প্রিমিয়াম করবে"""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"premium_status": True}}
    )
