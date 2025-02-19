from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # Додаємо CORS
import json
import os
import re
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Дозволяємо CORS для всіх запитів

DATA_FILE = "data.json"

# Функція для завантаження даних
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {"entries": {}, "freezes": 0, "last_entry": None}  # Видалено "streak"

# Функція для збереження даних
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Функція для обчислення ao5
def calculate_ao5(times):
    if len(times) < 5:
        return None
    ao5_values = []
    for i in range(len(times) - 4):
        subset = times[i:i+5]
        subset.sort()
        ao5 = sum(subset[1:4]) / 3  # Прибираємо найшвидший і найповільніший час
        ao5_values.append(ao5)
    return min(ao5_values) if ao5_values else None

# Функція для обробки вхідних даних
def parse_cstimer_data(raw_text):
    times = [float(match.group()) for match in re.finditer(r"\d+\.\d+", raw_text)]
    best_ao5 = calculate_ao5(times)
    return {"times": times, "best_ao5": best_ao5}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/parse", methods=["POST"])
def parse():
    data = request.json.get("cstimer_data", "")
    result = parse_cstimer_data(data)
    return jsonify(result)

@app.route("/status", methods=["GET"])
def get_status():
    data = load_data()
    streak = len(data["entries"])  # Стрік рахується по довжині entries
    
    reset_day = None
    lost_streak = False
    if data["last_entry"]:
        last_date = datetime.strptime(data["last_entry"], "%Y-%m-%d")
        last_possible_day = last_date + timedelta(days=data["freezes"])
        reset_day = (last_possible_day + timedelta(days=1)).strftime("%Y-%m-%d")
        
        days_missed = (datetime.today() - last_date).days
        if days_missed > data["freezes"] + 1:
            lost_streak = True
    
    return jsonify({
        "streak": streak,
        "freezes": data["freezes"],
        "entries": data["entries"],
        "reset_day": reset_day,  # Показуємо дату reset day
        "lost_streak": lost_streak  # Вказуємо, чи відрізок вже втрачено
    })

if __name__ == "__main__":
    app.run(debug=True)
