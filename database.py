import mysql.connector

def get_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="fast",
        password="7355608",
        database="fastAPI_test"
    )
    return conn
