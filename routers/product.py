from fastapi import APIRouter
from database import get_db
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

@router.post("")
def add_product(product: ProductCreate):
    conn = get_db()
    cursor = conn.cursor()
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
    cursor.close()
    conn.close()
    return {
        "message": "Product added",
        "id": new_id,
        "barcode": product.barcode,
        "product_name": product.product_name
    }

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

#查询产品（通过条码信息）
@router.get("/barcode/{barcode}")
def get_product_info(barcode: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM product WHERE barcode=%s",
        (barcode,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row
    else:
        return {"error": "product not found"}

#查询所有产品
@router.get("")
def get_all_product():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM product"
    )
    row = cursor.fetchall()
    cursor.close()
    conn.close()
    if row:
        return row
    else:
        return {"error": "product not found"}