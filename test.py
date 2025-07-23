# test_mysql.py
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",
    database="healthmate"
)

print("Connection successful!")
conn.close()
