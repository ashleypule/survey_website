from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('survey.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            dob TEXT,
            contact TEXT,
            food TEXT,
            watch_movies INTEGER,
            listen_radio INTEGER,
            eat_out INTEGER,
            watch_tv INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    dob = request.form.get('dob')
    contact = request.form.get('contact')
    foods = request.form.getlist('food')

    if not name or not email or not dob or not contact:
        return "All text fields are required.", 400

    try:
        birth_year = datetime.strptime(dob, "%Y-%m-%d").year
        current_year = datetime.now().year
        age = current_year - birth_year
        if age < 5 or age > 120:
            return "Age must be between 5 and 120.", 400
    except ValueError:
        return "Invalid date format for DOB.", 400

    try:
        watch_movies = int(request.form['watch_movies'])
        listen_radio = int(request.form['listen_radio'])
        eat_out = int(request.form['eat_out'])
        watch_tv = int(request.form['watch_tv'])
    except (KeyError, ValueError):
        return "Please select a rating for each question.", 400

    try:
        with sqlite3.connect('survey.db', timeout=10) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO surveys (name, email, dob, contact, food, watch_movies, listen_radio, eat_out, watch_tv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, dob, contact, ', '.join(foods), watch_movies, listen_radio, eat_out, watch_tv))
    except sqlite3.OperationalError as e:
        return f"Database error: {str(e)}", 500

    return redirect('/results')

@app.route('/results')
def results():
    conn = sqlite3.connect('survey.db')
    c = conn.cursor()
    c.execute('SELECT * FROM surveys')
    rows = c.fetchall()

    if not rows:
        return render_template('results.html', no_data=True)

    from datetime import datetime
    total = len(rows)
    ages = []
    pizza = pasta = pap = 0
    rating_watch_movies = []
    rating_listen_radio = []
    rating_eat_out = []
    rating_watch_tv = []

    for row in rows:
        try:
            age = datetime.now().year - datetime.strptime(row[3], "%Y-%m-%d").year
            ages.append(age)
        except:
            continue
        foods = row[5].split(', ')
        if "Pizza" in foods:
            pizza += 1
        if "Pasta" in foods:
            pasta += 1
        if "Pap and Wors" in foods:
            pap += 1

        rating_watch_movies.append(row[6])
        rating_listen_radio.append(row[7])
        rating_eat_out.append(row[8])
        rating_watch_tv.append(row[9])

    def avg(lst): return round(sum(lst)/len(lst), 1) if lst else 0

    data = {
        "total": total,
        "avg_age": round(sum(ages) / len(ages), 1) if ages else "N/A",
        "oldest": max(ages) if ages else "N/A",
        "youngest": min(ages) if ages else "N/A",
        "pizza_pct": round((pizza / total) * 100, 1),
        "pasta_pct": round((pasta / total) * 100, 1),
        "pap_pct": round((pap / total) * 100, 1),
        "avg_watch_movies": avg(rating_watch_movies),
        "avg_listen_radio": avg(rating_listen_radio),
        "avg_eat_out": avg(rating_eat_out),
        "avg_watch_tv": avg(rating_watch_tv),
        "no_data": False
    }

    return render_template("results.html", **data)


if __name__ == '__main__':
    app.run(debug=True)
