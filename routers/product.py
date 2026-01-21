import json
from typing import Optional
from psycopg2 import errors
from fastapi import APIRouter,Query,HTTPException, status
from supa_connect import get_supabase_client
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

    conn = get_supabase_client()

    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO product
                (barcode, product_name, shelf_life_days, location, category, unit)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """

            cursor.execute(
                sql,
                (
                    product.barcode,
                    product.product_name,
                    product.shelf_life_days,
                    product.location,
                    product.category,
                    product.unit,
                ),
            )

            new_id = cursor.fetchone()[0]
            conn.commit()

            return {
                "message": "Product added successfully",
                "id": new_id,
                "product_name": product.product_name,
            }

    except errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="该条码已存在")

    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误，无法保存产品")

    finally:
        conn.close()

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


#查询产品
#2026.1.21携带参数测试通过
@router.get("")
def get_product(search: Optional[str] = Query(default=None)):
    conn = get_supabase_client()
    query = (
        conn
        .table("product")
        .select(
            "id, barcode, product_name, shelf_life_days, "
            "location, category, unit, created_at, updated_at"
        )
    )
    if search:
        like_value = f"%{search}%"
        query = query.or_(
            ",".join([
                f"barcode.ilike.{like_value}",
                f"product_name.ilike.{like_value}",
                f"category.ilike.{like_value}",
                f"location.ilike.{like_value}",
                f"unit.ilike.{like_value}",
            ])
        )
        res = query.execute()
        res = res.data
        return {
            "code": 0,
            "message": "ok",
            "data": res
        }
    else:
        res = (conn.table("product")
               .select("*")
               .execute()
               )
        return {
            "code": 0,
            "message": "ok",
            "data": res
        }


