import requests
import json
import pandas as pd

def search_food_openfoodfacts(query):
    """
    Search for food using Open Food Facts API
    Returns a list of dicts with food name and macroscopic info per 100g or serving.
    """
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&search_simple=1&action=process&json=1&page_size=20"
    try:
        response = requests.get(url, timeout=2)
        data = response.json()
        
        results = []
        if 'products' in data:
            for product in data['products']:
                name = product.get('product_name', 'Unknown')
                brand = product.get('brands', '')
                if brand:
                    name = f"{brand} - {name}"
                
                nutriments = product.get('nutriments', {})
                
                # Default to per 100g if serving not available, but user can scale it
                cals = nutriments.get('energy-kcal_100g', 0)
                protein = nutriments.get('proteins_100g', 0)
                carbs = nutriments.get('carbohydrates_100g', 0)
                fats = nutriments.get('fat_100g', 0)
                
                # Only add if it has some calorie data to avoid clutter
                if cals is not None and name != 'Unknown':
                    results.append({
                        'name': name,
                        'calories_100g': float(cals) if cals else 0.0,
                        'protein_100g': float(protein) if protein else 0.0,
                        'carbs_100g': float(carbs) if carbs else 0.0,
                        'fats_100g': float(fats) if fats else 0.0
                    })
        return results
    except Exception as e:
        print(f"Error fetching from Open Food Facts: {e}. Using local fallback data.")
        # Local fallback database of common foods
        mock_db = [
            {"name": "Apple", "calories_100g": 52.0, "protein_100g": 0.3, "carbs_100g": 14.0, "fats_100g": 0.2},
            {"name": "Banana", "calories_100g": 89.0, "protein_100g": 1.1, "carbs_100g": 23.0, "fats_100g": 0.3},
            {"name": "Chicken Breast", "calories_100g": 165.0, "protein_100g": 31.0, "carbs_100g": 0.0, "fats_100g": 3.6},
            {"name": "White Rice (Cooked)", "calories_100g": 130.0, "protein_100g": 2.7, "carbs_100g": 28.0, "fats_100g": 0.3},
            {"name": "Oatmeal", "calories_100g": 68.0, "protein_100g": 2.4, "carbs_100g": 12.0, "fats_100g": 1.4},
            {"name": "Egg (Boiled)", "calories_100g": 155.0, "protein_100g": 13.0, "carbs_100g": 1.1, "fats_100g": 11.0},
            {"name": "Broccoli", "calories_100g": 34.0, "protein_100g": 2.8, "carbs_100g": 6.6, "fats_100g": 0.4},
            {"name": "Salmon", "calories_100g": 208.0, "protein_100g": 20.0, "carbs_100g": 0.0, "fats_100g": 13.0},
            {"name": "Almonds", "calories_100g": 579.0, "protein_100g": 21.0, "carbs_100g": 22.0, "fats_100g": 50.0},
            {"name": "Greek Yogurt", "calories_100g": 59.0, "protein_100g": 10.0, "carbs_100g": 3.6, "fats_100g": 0.4},
            {"name": "Sweet Potato", "calories_100g": 86.0, "protein_100g": 1.6, "carbs_100g": 20.0, "fats_100g": 0.1},
            {"name": "Avocado", "calories_100g": 160.0, "protein_100g": 2.0, "carbs_100g": 8.5, "fats_100g": 15.0},
            {"name": "Whey Protein Powder", "calories_100g": 359.0, "protein_100g": 80.0, "carbs_100g": 5.0, "fats_100g": 2.0},
            {"name": "Peanut Butter", "calories_100g": 588.0, "protein_100g": 25.0, "carbs_100g": 20.0, "fats_100g": 50.0},
            {"name": "Milk (Whole)", "calories_100g": 61.0, "protein_100g": 3.2, "carbs_100g": 4.8, "fats_100g": 3.3},
            {"name": "Steak", "calories_100g": 271.0, "protein_100g": 25.0, "carbs_100g": 0.0, "fats_100g": 19.0},
            {"name": "Dal (Cooked Lentils)", "calories_100g": 116.0, "protein_100g": 9.0, "carbs_100g": 20.0, "fats_100g": 0.4},
            {"name": "Paneer", "calories_100g": 321.0, "protein_100g": 25.0, "carbs_100g": 3.6, "fats_100g": 25.0},
            {"name": "Chapati / Roti", "calories_100g": 297.0, "protein_100g": 9.0, "carbs_100g": 46.0, "fats_100g": 8.0}
        ]
        
        fallback_results = []
        q_lower = query.lower()
        for item in mock_db:
            if q_lower in str(item.get("name", "")).lower():
                fallback_results.append(item)
                
        # If still empty, return a generic item matching the query to ensure *something* logs
        if not fallback_results:
            fallback_results.append({
                "name": query.capitalize() + " (Generic Estimate)",
                "calories_100g": 130.0,
                "protein_100g": 5.0,
                "carbs_100g": 20.0,
                "fats_100g": 5.0
            })
            
        return fallback_results

def scale_nutrients(food_item, weight_g):
    """
    Scale the 100g nutrients based on provided weight in grams.
    """
    ratio = weight_g / 100.0
    return {
        'name': food_item['name'],
        'calories': round(food_item['calories_100g'] * ratio, 1),
        'protein_g': round(food_item['protein_100g'] * ratio, 1),
        'carbs_g': round(food_item['carbs_100g'] * ratio, 1),
        'fats_g': round(food_item['fats_100g'] * ratio, 1)
    }

def process_apple_watch_export(file_content):
    """
    Process Apple Watch JSON export.
    Expects JSON structure (array of objects with date, steps, active_calories...)
    Or a CSV. For MVP, assuming user uploads a simple daily aggregation JSON.
    """
    try:
        # If it's pure json text
        if isinstance(file_content, str):
            data = json.loads(file_content)
        else:
            # Assume it's a file byte stream
            data = json.load(file_content)
            
        df = pd.DataFrame(data)
        # We expect columns like: date, steps, active_calories, exercise_minutes, avg_heart_rate
        # For simplicity return the dataframe if it matches
        required_cols = ['date', 'steps', 'active_calories', 'exercise_minutes', 'avg_heart_rate']
        if all(col in df.columns for col in required_cols):
            return df
        else:
            return None
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None
