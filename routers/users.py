from fastapi import APIRouter
from database import get_db

router = APIRouter(
    prefix="/users",   # 所有接口都带 /users
    tags=["Users"]     # 自动文档分类
)

@router.post("/create/{name}")
def create_user(name: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user (name) VALUES (%s)", [name])
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "User created", "name": name}

@router.delete("/delete/{user_id}")
def delete_user(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": f"User {user_id} deleted"}

@router.get("/get/{user_id}")
def get_user(user_id: int):
    conn = get_db()                  # ① 获取数据库连接
    cursor = conn.cursor()           # ② 创建游标
    cursor.execute(
        "SELECT id, name FROM user WHERE id=%s",
        (user_id,)
    )                                # ③ 执行查询
    row = cursor.fetchone()          # ④ 获取一行结果
    cursor.close()
    conn.close()                     # ⑤ 关闭连接

    if row:
        return {"id": row[0], "name": row[1]}
    else:
        return {"error": "User not found"}
