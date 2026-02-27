import datetime
from database import init_db, log_daily_weight, log_food, save_workout, upsert_apple_watch_data

# Ensure DB exists
init_db()

today = datetime.date.today()

# 1. Log past 7 days of weight
weights = [76.5, 76.2, 76.0, 75.8, 75.5, 75.3, 75.0]
for i in range(7):
    d = today - datetime.timedelta(days=6-i)
    log_daily_weight(str(d), weights[i])

# 2. Log some food for today
log_food(str(today), "Breakfast", "Oatmeal with berries", "1 bowl", 350.5, 12.0, 60.0, 5.0)
log_food(str(today), "Lunch", "Chicken Breast & Rice", "1 plate", 600.0, 50.0, 70.0, 10.0)

# 3. Log a workout
save_workout(
    str(today), 
    65, 
    "Great push session!", 
    [
        {"exercise_name": "Bench Press", "sets": 3, "reps": 8, "weight_kg": 80.0, "rpe": 8.0},
        {"exercise_name": "Overhead Press", "sets": 3, "reps": 10, "weight_kg": 50.0, "rpe": 8.5}
    ]
)

# 4. Mock Apple Watch Data for the past 5 days
steps = [8500, 10200, 12000, 7500, 11000]
active_cals = [400, 500, 650, 350, 550]
for i in range(5):
    d = today - datetime.timedelta(days=4-i)
    upsert_apple_watch_data(str(d), steps[i], active_cals[i], 45, 72.5)

print("Mock data generated successfully!")
