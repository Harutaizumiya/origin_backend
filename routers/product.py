from typing import Optional
import postgrest.exceptions
from fastapi import APIRouter, Query, HTTPException, status
from supa_connect import get_supabase_client
from fastapi import Path
from pydantic import BaseModel

router = APIRouter(
    prefix="/product",
    tags=["product"]
)


#新增产品
class ProductCreate(BaseModel):
    barcode: str  #条码信息
    product_name: str  #产品名称
    shelf_life_days: int  #保质期
    location: str | None = None  #存储位置
    category: str | None = None  #产品类型
    unit: str | None = None  #存储单位


@router.post("", status_code=status.HTTP_201_CREATED)
def add_product(product: ProductCreate):
    conn = get_supabase_client()

    try:
        res = (
            conn
            .table("product")
            .insert({
                "barcode": product.barcode,
                "product_name": product.product_name,
                "shelf_life_days": product.shelf_life_days,
                "location": product.location,
                "category": product.category,
                "unit": product.unit
            })
            .execute()
        )

        # 如果返回 data 为空，说明插入失败
        if not res.data:
            raise HTTPException(status_code=500, detail="产品插入失败")

        new_id = res.data[0]["id"]

        return {
            "code": 0,
            "message": "Product added successfully",
            "id": new_id,
            "product_name": product.product_name,
        }

    except postgrest.exceptions.APIError as e:
        # 唯一约束冲突 / 其他错误
        if e.code == "23505":  # PostgreSQL 唯一约束违反
            raise HTTPException(status_code=400, detail="该条码已存在")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


# 更新产品信息
class ProductUpdate(BaseModel):
    product_name: str | None = None
    shelf_life_days: int | None = None
    location: str | None = None
    category: str | None = None
    unit: str | None = None

@router.put("/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    conn = get_supabase_client()

    # 构造更新字典，只保留非 None 的字段
    update_data = {}
    if product.product_name is not None:
        update_data["product_name"] = product.product_name
    if product.shelf_life_days is not None:
        update_data["shelf_life_days"] = product.shelf_life_days
    if product.location is not None:
        update_data["location"] = product.location
    if product.category is not None:
        update_data["category"] = product.category
    if product.unit is not None:
        update_data["unit"] = product.unit

    if not update_data:
        return {"message": "No fields to update"}

    try:
        res = (
            conn
            .table("product")
            .update(update_data)
            .eq("id", product_id)
            .execute()
        )

        # 如果 data 为空，说明没有找到对应 id
        if not res.data:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        return {"message": f"Product {product_id} updated", "updated_fields": list(update_data.keys())}

    except postgrest.APIError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {e}")

#删除产品
@router.delete("/{product_id}")
def delete_product(
    product_id: int = Path(
        ...,
        gt=0,
        description="产品 ID，不能为空且必须大于 0"
    )
):
    try:
        conn = get_supabase_client()
        res = (
            conn
            .table("product")
            .delete()
            .eq("id", product_id)
            .execute()
        )
    except postgrest.APIError as e:
        raise HTTPException(status_code=400, detail=e.json())

    if not res.data:
        raise HTTPException(status_code=404, detail="产品不存在")

    return {
            "code":0,
            "message": "删除成功",
            "deleted": res.data
            }


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

@router.get("/category",description="指定产品类型查询，只返回product.category字段，支持模糊查询")
def get_category(search: Optional[str] = Query(default=None)):
    conn = get_supabase_client()

    query = (
        conn
        .table("product")
        .select("category")
    )

    if search:
        like_value = f"%{search}%"
        query = query.like("category", like_value)

    res = query.execute()
    rows = res.data or []

    # Python 去重 + 过滤空值
    categories = list({
        row["category"]
        for row in rows
        if row.get("category")
    })

    if search and not categories:
        raise HTTPException(
            status_code=404,
            detail=f"category not found for search='{search}'"
        )

    return {
        "code": 0,
        "message": "ok",
        "data": categories
    }
