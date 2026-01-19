import mysql.connector
from mysql.connector import Error

def get_db():
    conn = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="fast",
            password="7355608",
            database="fastAPI_test"
        )
        return conn

    except Error as e:
        print(f"连接数据库时发生错误: {e}")
        return None
