from typing import Optional

from fastapi import APIRouter,Query,HTTPException, status
from database import get_db
from sqlalchemy import text
from pydantic import BaseModel

router = APIRouter(
    prefix="/product",
    tags=["product"]
)

#新增产品
class ProductCreate(BaseModel):
    barcode: str                    #条码信息
    product_name: str               #产品名称
    shelf_life_days: int            #保质期
    location: str | None = None     #存储位置
    category: str | None = None     #产品类型
    unit: str | None = None         #存储单位


@router.post("", status_code=status.HTTP_201_CREATED)
def add_product(product: ProductCreate):
    # 1. 获取连接
    conn = get_db()
    try:
        with conn.cursor(dictionary=True) as cursor:
            sql = """
                INSERT INTO product (barcode, product_name, shelf_life_days, location, category, unit)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                product.barcode, product.product_name, product.shelf_life_days,
                product.location, product.category, product.unit
            ))
            conn.commit()
            new_id = cursor.lastrowid

            return {
                "message": "Product added successfully",
                "id": new_id,
                "product_name": product.product_name
            }
    except Exception as e:
        conn.rollback()  # 发生错误务回滚
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="该条码已存在")

        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误，无法保存产品")
    finally:
        conn.close()  # 3. 确保关闭连接

# 更新产品信息
class ProductUpdate(BaseModel):
    product_name: str | None = None
    shelf_life_days: int | None = None
    location: str | None = None
    category: str | None = None
    unit: str | None = None

@router.put("/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    conn = get_db()
    cursor = conn.cursor()

    fields = []
    values = []
    if product.product_name:
        fields.append("product_name = %s")
        values.append(product.product_name)
    if product.shelf_life_days:
        fields.append("shelf_life_days = %s")
        values.append(product.shelf_life_days)
    if product.location:
        fields.append("location = %s")
        values.append(product.location)
    if product.category:
        fields.append("category = %s")
        values.append(product.category)
    if product.unit:
        fields.append("unit = %s")
        values.append(product.unit)

    if not fields:
        return {"message": "No fields to update"}

    values.append(product_id)
    sql = f"UPDATE product SET {', '.join(fields)} WHERE id = %s"
    cursor.execute(sql, tuple(values))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": f"Product {product_id} updated"}

#删除产品
@router.delete("/{product_id}")
def delete_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product WHERE id=%s", (product_id,))
    conn.commit()
    deleted_rows = cursor.rowcount  # 受影响行数
    cursor.close()
    conn.close()

    if deleted_rows == 0:
        return {"message": f"Product {product_id} not found"}
    return {"message": f"Product {product_id} deleted"}

#查询产品（通过ID）
@router.get("/{product_id}")
def get_product_info(product_id: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM product WHERE id=%s",
        (product_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row
    else:
        return {"error": "product not found"}

#通过名称查询
@router.get("/name/{product_name}")
def get_product_info(product_name: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM product WHERE product_name=%s",
        (product_name,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row
    else:
        return {"error": "product not found"}

#查询产品
#⚠警告，2026.1.13 0：54测试未通过！
@router.get("")
def query_product(search: Optional[str] = Query(default=None)):
    conn = get_db()
    if conn is None:
        raise HTTPException(status_code=500,detail="数据库连接错误")
    sql = """
    SELECT
        id,
        barcode,
        product_name,
        shelf_life_days,
        location,
        category,
        unit,
        created_at,
        updated_at
    FROM product
    """

    params = []

    if search:
        like_value = f"%{search}%"
        conditions = [
            "barcode LIKE %s",
            "product_name LIKE %s",
            "category LIKE %s",
            "location LIKE %s",
            "unit LIKE %s"
        ]
        sql += " WHERE (" + " OR ".join(conditions) + ")"
        params = [like_value] * len(conditions)

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()

#查询所有产品
# @router.get("")
# def get_all_product():
#     conn = get_db()
#     try:
#         with conn.cursor(dictionary=True) as cursor:
#             cursor.execute(
#                 "SELECT * FROM product"
#             )
#             row = cursor.fetchall()
#             if row:
#                 return row
#
#     except Exception as e:
#         return {f"error":{e}}
#
#     finally:
#         conn.close()

    # conn = get_db()
    # cursor = conn.cursor(dictionary=True)
    # cursor.execute(
    #     "SELECT * FROM product"
    # )
    # row = cursor.fetchall()
    # cursor.close()
    # conn.close()
    # if row:
    #     return row
    # else:
    #     return {"error": "product not found"}