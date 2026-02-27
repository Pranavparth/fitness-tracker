# 🏋️‍♂️ Fitness & Health Analytics Tracker

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-Plotly-0085CA?style=for-the-badge&logo=plotly&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Render](https://img.shields.io/badge/Render-Deployment-46E3B7?style=for-the-badge&logo=render&logoColor=white)

A mobile-first, cloud-connected data analytics web application designed to automatically track, visualize, and analyze personal fitness journeys. Built end-to-end using a modern Python data stack, acting as a fully automated ETL pipeline for Apple Health data.

## 🌟 Key Features

*   **📱 Mobile-First "Web App" UI:** Designed with a premium dark-mode aesthetic, utilizing CSS glassmorphism, safe-area dynamic padding for iPhones, and a custom bottom navigation bar replacing traditional sidebars.
*   **⌚ Apple Health Automation Pipeline:** Features a custom Flask REST API webhook (`/api/apple-health-sync`) that accepts daily JSON payloads from an automated iOS Shortcut, syncing Apple Watch data directly to the cloud without manual entry.
*   **📊 Dynamic Real-Time Dashboards:** Interactive Plotly charts optimized for mobile constraints, visualizing weight trends, daily caloric intake against maintenance goals, and step counts.
*   **🧮 Smart Health Metrics:** Automatically calculates Body Mass Index (BMI) dynamically from user settings and logs, categorizing the result against official CDC thresholds (Normal, Overweight, Obese) with live color coordination.
*   **☁️ Cloud Database (Supabase):** Fully migrated from local SQLite to Supabase (PostgreSQL) for scalable, real-time data persistence.
*   **🚀 CI/CD Pipeline:** Containerized with Gunicorn and continuously deployed to Render directly from GitHub using strictly pinned environment dependencies to prevent pip backtracking loops.

## 🏗️ Architecture

1.  **Extract:** iOS Automation Shortcuts pull daily metrics (Steps, Active Calories, Exercise Minutes) from Apple Health via the iPhone.
2.  **Transform:** The data is compiled into a JSON payload and `POST`ed to the Dash webhook API. The server parses and validates the payload.
3.  **Load:** The Python backend leverages the Supabase client to `upsert` the data into a PostgreSQL relational database.
4.  **Visualize:** The Dash frontend queries the cloud database, merges different tables using Pandas, and renders responsive Plotly charts.

## 🛠️ Technology Stack

*   **Frontend Data App:** Dash (Plotly), Dash Bootstrap Components
*   **Backend & API:** Flask, Python 3.11, Gunicorn
*   **Database:** Supabase (PostgreSQL)
*   **Data Processing:** Pandas
*   **Hosting:** Render.com

## 📷 Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/6be073aa-b262-4d50-9e93-ed2734d7b085" alt="Dashboard Overview" width="240">
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="https://github.com/user-attachments/assets/e455edb6-801a-40a3-9371-04dcedd0d8df" alt="Dashboard Charts" width="240">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/0888d34f-88b5-4d70-9708-413719ece953" alt="Journal Top" width="240">
  &nbsp; &nbsp; &nbsp; &nbsp;
  <img src="https://github.com/user-attachments/assets/da9203ad-7b88-4058-97e6-4476855b2f93" alt="Journal Bottom" width="240">
</p>

*   **Dashboard View:** Showing the grid metrics and trend charts.
*   **Journal View:** Mobile-optimized data entry forms for weight, nutrition, and workouts.

## 🚀 How to Run Locally

1.  Clone the repository:
    ```bash
    git clone https://github.com/Pranavparth/fitness-tracker.git
    cd fitness-tracker
    ```
2.  Create a virtual environment and install exactly pinned dependencies:
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  Create a `.env` file with your Supabase credentials:
    ```env
    SUPABASE_URL="your-supabase-url"
    SUPABASE_KEY="your-supabase-anon-key"
    ```
4.  Start the Dash server:
    ```bash
    python app_dash.py
    ```

---
*Developed by [Pranav Parthasarathy](https://github.com/Pranavparth) as a Data Analytics Portfolio Project.*
