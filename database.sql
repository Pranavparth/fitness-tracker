-- Run these commands in the Supabase SQL Editor to initialize the tables

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    height_cm REAL,
    maintenance_calories INTEGER
);

CREATE TABLE IF NOT EXISTS daily_logs (
    date TEXT PRIMARY KEY,
    weight_kg REAL,
    maintenance_calories INTEGER,
    deficit_surplus INTEGER,
    bmi REAL
);

CREATE TABLE IF NOT EXISTS apple_watch_data (
    date TEXT PRIMARY KEY,
    steps INTEGER,
    active_calories INTEGER,
    exercise_minutes INTEGER,
    avg_heart_rate REAL
);

CREATE TABLE IF NOT EXISTS workouts (
    id SERIAL PRIMARY KEY,
    date TEXT,
    duration_minutes INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id SERIAL PRIMARY KEY,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_name TEXT,
    sets INTEGER,
    reps INTEGER,
    weight_kg REAL,
    rpe REAL
);

CREATE TABLE IF NOT EXISTS food_logs (
    id SERIAL PRIMARY KEY,
    date TEXT,
    meal_name TEXT,
    food_name TEXT,
    portion_size TEXT,
    calories REAL,
    protein_g REAL,
    carbs_g REAL,
    fats_g REAL
);

-- Insert a default user record if starting fresh
INSERT INTO users (id, height_cm, maintenance_calories) 
VALUES (1, 175.0, 2500)
ON CONFLICT DO NOTHING;
