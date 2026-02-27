import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

# Initialize Supabase client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Missing Supabase credentials. Ensure SUPABASE_URL and SUPABASE_KEY are set in .env")

supabase: Client = create_client(url, key)

# ------------- DB Handlers -------------

def get_user_settings():
    response = supabase.table("users").select("*").limit(1).execute()
    if response.data:
        return response.data[0]
    return {"height_cm": 175.0, "maintenance_calories": 2500} # Default

def update_user_settings(height_cm, maintenance_calories):
    user = get_user_settings()
    if "id" in user:
        response = supabase.table("users").update({
            "height_cm": height_cm,
            "maintenance_calories": maintenance_calories
        }).eq("id", user["id"]).execute()
    else:
         response = supabase.table("users").insert({
            "height_cm": height_cm,
            "maintenance_calories": maintenance_calories
        }).execute()
    return response

def log_daily_weight(date, weight_kg):
    # Fetch user for BMI calculation
    user = get_user_settings()
    height_m = user.get('height_cm', 175.0) / 100.0 if user.get('height_cm') else None
    bmi = (weight_kg / (height_m * height_m)) if height_m and height_m > 0 else None
    
    # Supabase upsert requires the primary key (date)
    response = supabase.table("daily_logs").upsert({
        "date": date,
        "weight_kg": weight_kg,
        "maintenance_calories": user.get('maintenance_calories', 2500),
        "bmi": bmi
    }).execute()
    return response

def get_daily_logs_df():
    response = supabase.table("daily_logs").select("*").order("date", desc=True).execute()
    return pd.DataFrame(response.data)

def log_food(date, meal_name, food_name, portion_size, calories, protein_g=0, carbs_g=0, fats_g=0):
    response = supabase.table("food_logs").insert({
        "date": date,
        "meal_name": meal_name,
        "food_name": food_name,
        "portion_size": portion_size,
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fats_g": fats_g
    }).execute()
    return response

def get_food_logs_by_date(date):
    response = supabase.table("food_logs").select("*").eq("date", date).execute()
    return pd.DataFrame(response.data)

def get_daily_calories_df():
    # Since Supabase RPC (functions) are needed for group by, we will aggregate in Pandas for now
    response = supabase.table("food_logs").select("date", "calories").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        agg_df = df.groupby('date')['calories'].sum().reset_index()
        agg_df = agg_df.rename(columns={'calories': 'consumed'})
        agg_df = agg_df.sort_values(by='date', ascending=False)
        return agg_df
    return pd.DataFrame(columns=['date', 'consumed'])

def save_workout(date, duration_minutes, notes, exercises):
    """
    exercises: list of dicts with keys: exercise_name, sets, reps, weight_kg, rpe
    """
    # 1. Insert workout
    workout_resp = supabase.table("workouts").insert({
        "date": date,
        "duration_minutes": duration_minutes,
        "notes": notes
    }).execute()
    
    if workout_resp.data:
        workout_id = workout_resp.data[0]['id']
        
        # 2. Insert exercises
        if exercises:
            for ex in exercises:
                ex['workout_id'] = workout_id
            
            supabase.table("workout_exercises").insert(exercises).execute()

def get_recent_workouts(limit=10):
    workouts_resp = supabase.table("workouts").select("*").order("date", desc=True).limit(limit).execute()
    workouts = workouts_resp.data
    
    workout_data = []
    for w in workouts:
        exercises_resp = supabase.table("workout_exercises").select("*").eq("workout_id", w['id']).execute()
        workout_data.append({
            'workout': w,
            'exercises': exercises_resp.data
        })
    return workout_data

def upsert_apple_watch_data(date, steps, active_calories, exercise_minutes, avg_heart_rate):
    response = supabase.table("apple_watch_data").upsert({
        "date": date,
        "steps": steps,
        "active_calories": active_calories,
        "exercise_minutes": exercise_minutes,
        "avg_heart_rate": avg_heart_rate
    }).execute()
    return response

def get_apple_watch_df():
    response = supabase.table("apple_watch_data").select("*").order("date", desc=True).execute()
    return pd.DataFrame(response.data)

if __name__ == '__main__':
    # Test connection
    print("Testing Supabase connection...")
    try:
        user = get_user_settings()
        print(f"Connected successfully! Default user settings: {user}")
    except Exception as e:
        print(f"Connection failed: {e}")
