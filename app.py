from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecret'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT UNIQUE, 
        password TEXT, 
        balance INTEGER DEFAULT 0,
        invested INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        type TEXT,
        amount INTEGER
    )''')
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = u
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        u = session['username']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT balance, invested FROM users WHERE username=?", (u,))
        data = c.fetchone()
        conn.close()
        return render_template("dashboard.html", username=u, balance=data[0], invested=data[1])
    return redirect('/')

@app.route('/recharge', methods=['GET', 'POST'])
def recharge():
    if 'username' in session:
        if request.method == 'POST':
            amount = int(request.form['amount'])
            u = session['username']
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, u))
            c.execute("INSERT INTO transactions (username, type, amount) VALUES (?, ?, ?)", (u, 'recharge', amount))
            conn.commit()
            conn.close()
            return redirect('/dashboard')
        return render_template("recharge.html")
    return redirect('/')

@app.route('/plans')
def plans():
    return render_template("plans.html")

@app.route('/invest/<int:amount>')
def invest(amount):
    if 'username' in session:
        u = session['username']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username=?", (u,))
        bal = c.fetchone()[0]
        if bal >= amount:
            c.execute("UPDATE users SET balance = balance - ?, invested = invested + ? WHERE username=?", (amount, amount, u))
            c.execute("INSERT INTO transactions (username, type, amount) VALUES (?, ?, ?)", (u, 'invest', amount))
            conn.commit()
            conn.close()
            return redirect('/dashboard')
        else:
            conn.close()
            return "Insufficient balance"
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)