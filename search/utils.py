import datetime
import requests

API_URL = "https://crop-recommendation-api.onrender.com/predict"

def get_current_season():
    """Determine the season based on the current month"""
    month = datetime.datetime.now().month
    if month in [12, 1, 2]: return "Winter"
    if month in [3, 4, 5]: return "Summer"
    if month in [6, 7, 8]: return "Monsoon"
    return "Post-Monsoon"

def get_favorable_crops(season):
    """Return suggested crops based on the season"""
    season_crops = {
        "Winter": ["Wheat", "Mustard", "Peas", "Carrots", "Cabbage", "Spinach", "Radish", "Cauliflower", "Fenugreek", "Broccoli"],
        "Summer": ["Maize", "Millets", "Sugarcane", "Watermelon", "Pumpkin", "Bitter Gourd", "Cucumber", "Tomato", "Okra", "Chili"],
        "Monsoon": ["Rice", "Paddy", "Tur", "Corn", "Black Gram (Urad Dal)", "Soybean", "Green Gram (Moong Dal)", "Groundnut", "Cotton", "Jute"],
        "Post-Monsoon": ["Barley", "Gram", "Lentils", "Sesame", "Horse Gram", "Chickpeas", "Mustard", "Sorghum", "Linseed", "Tobacco"]
    }

    return season_crops.get(season, [])

def get_ai_crop_recommendations(soil_ph, nitrogen, phosphorus, potassium):
    """Fetch AI-based crop recommendations"""
    payload = {
        "N": nitrogen,
        "P": phosphorus,
        "K": potassium,
        "temperature": 25.0,  # default or estimated
        "humidity": 60.0,     # default or estimated
        "ph": soil_ph,
        "rainfall": 100.0     # default or estimated
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            crop = response.json().get("prediction")
            return [crop] if crop else []
        else:
            print("🔴 AI crop API error:", response.status_code, response.text)
            return []
    except Exception as e:
        print("🔴 Exception during crop recommendation:", e)
        return []
