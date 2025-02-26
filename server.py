from flask import Flask, request, jsonify
from flask_cors import CORS  # Додаємо CORS
import json
import os
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

@app.route("/submit", methods=["POST"])
def submit():
    data = load_data()
    today = datetime.today().strftime("%Y-%m-%d")
    
    # Якщо на сьогодні вже є запис – повертаємо помилку
    if today in data["entries"]:
        return jsonify({"message": "Сьогодні вже введені дані!"}), 400

    entry = request.json
    data["entries"][today] = entry  # Зберігаємо запис
    streak = len(data["entries"])  # Стрік рахується по довжині entries
    
    reset_day = None
    if data["last_entry"]:
        last_date = datetime.strptime(data["last_entry"], "%Y-%m-%d")
        
        days_missed = (datetime.today() - last_date).days
        
        if days_missed > data["freezes"] + 1:
            # Якщо минув день після останнього можливого дня – обнуляємо стрік і очищаємо записи
            data["entries"] = {}
            streak = 1
            data["freezes"] = 0  
        else:
            # Витрачаємо рівно стільки заморозок, скільки потрібно
            data["freezes"] -= max(0, days_missed - 1)
    
    # Раз на 4 дні стріку додається 1 заморозка
    if streak % 4 == 0:
        data["freezes"] += 1

    data["last_entry"] = today
    save_data(data)

    return jsonify({"message": "Дані збережено!", "streak": streak, "freezes": data["freezes"]})

@app.route("/status", methods=["GET"])
def get_status():
    data = load_data()
    streak = len(data["entries"])  # Стрік рахується по довжині entries
    
    reset_day = None
    if data["last_entry"]:
        last_date = datetime.strptime(data["last_entry"], "%Y-%m-%d")
        last_possible_day = last_date + timedelta(days=data["freezes"])
        reset_day = (last_possible_day + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return jsonify({
        "streak": streak,
        "freezes": data["freezes"],
        "entries": data["entries"],
        "reset_day": reset_day  # Показуємо дату reset day
    })

@app.route('/get_chart_data', methods=['GET'])
def get_data():
    with open(DATA_FILE, "r") as file:
        data = json.load(file)
    
    return jsonify([float(entry["value"]) for entry in data["entries"].values()])

if __name__ == "__main__":
    app.run(debug=True)
