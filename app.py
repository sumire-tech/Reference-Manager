import threading
import socket
import webview
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS papers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                link TEXT NOT NULL,
                status TEXT DEFAULT 'To-Read',
                status_priority INTEGER DEFAULT 1,
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
              ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM papers ORDER BY status_priority ASC, created_at DESC')
    papers = c.fetchall()
    conn.close()
    return render_template('index.html', papers=papers)

@app.route('/add', methods=['POST'])
def add_paper():
    title = request.form['title']
    authors = request.form.get('authors', '')
    year = request.form.get('year', None)
    link = request.form.get('link', '')
    status = request.form.get('status', 'To-Read')
    memo = request.form.get('memo', '')
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
              INSERT INTO papers (title, authors, year, link, status, memo)
              VALUES (?, ?, ?, ?, ?, ?)
              ''', (title, authors, year, link, status, memo))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_status/<int:ref_id>', methods=['POST'])
def update_status(ref_id):
    new_status = request.form['status']

    # ステータスに応じた優先度を設定
    priority_map = {
        'To-Read': 1,
        'In-Progress': 2,
        'Read': 3
    }
    new_priority = priority_map.get(new_status, 1)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        UPDATE papers 
        SET status = ?, status_priority = ? 
        WHERE id = ?
    ''', (new_status, new_priority, ref_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:ref_id>', methods=['POST'])
def delete_reference(ref_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM papers WHERE id = ?", (ref_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

def find_free_port():
    s = socket.socket()
    s.bind(('', 0))  # OSに空きポートを割り当て
    port = s.getsockname()[1]
    s.close()
    return port

def run_flask(port):
    # Flask デバッグモードOFF、threaded=True
    app.run(port=port, debug=False, threaded=True)

if __name__ == '__main__':
    port = find_free_port()
    # Flask をバックグラウンドで起動
    threading.Thread(target=run_flask, args=(port,), daemon=True).start()
    # PyWebview でネイティブウィンドウを開く
    webview.create_window("Reference Manager", f"http://127.0.0.1:{port}", width=900, height=700)
    webview.start()