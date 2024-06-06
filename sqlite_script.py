import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

data = pd.read_csv('lines.csv')

for index, row in data.iterrows():
    cursor.execute("INSERT INTO lines (user_id, line, date) VALUES (?, ?, ?)", (row['user_id'], row['line'], row['date']))
    conn.commit()

conn.close()