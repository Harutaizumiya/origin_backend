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
    """新增产品数据模型
    用于创建新产品时的数据验证和序列化
    """
    barcode: str  #条码信息
    product_name: str  #产品名称
    shelf_life_days: int  #保质期
    location: str | None = None  #存储位置
    category: str | None = None  #产品类型
    unit: str | None = None  #存储单位
    manufacturer: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def add_product(product: ProductCreate):
    """新增产品接口

    Args:
        product: 产品数据对象，包含条码、名称、保质期等信息

    Returns:
        dict: 包含创建成功的产品ID和产品名称的字典
            - code: 状态码，0表示成功
            - message: 提示信息
            - id: 新创建的产品ID
            - product_name: 产品名称

    Raises:
        HTTPException: 当条码已存在时返回400，当插入失败时返回500
    """
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
                "unit": product.unit,
                "manufacturer": product.manufacturer
            })
            .execute()
        )

        # 如果返回 data 为空，说明插入失败
        if not res.data:
            raise HTTPException(status_code=500, detail="产品插入失败")

        new_id = res.data[0]["id"]

        return {
            "code": 0,
            "message": "产品已创建",
            "id": new_id,
            "product_name": product.product_name,
        }

    except postgrest.exceptions.APIError as e:
        # 唯一约束冲突 / 其他错误
        if e.code == "23505":  # PostgreSQL 唯一约束违反
            raise HTTPException(status_code=400, detail="该条码已存在")
        if e.code == "23502":
            raise HTTPException(status_code=400, detail="缺少参数")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


# 更新产品信息
class ProductUpdate(BaseModel):
    """更新产品数据模型
    用于更新产品信息时的数据验证和序列化，所有字段都是可选的
    """
    product_name: str | None = None
    shelf_life_days: int | None = None
    location: str | None = None
    category: str | None = None
    unit: str | None = None
    manufacturer: str | None = None

@router.put("/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    """更新产品信息接口

    Args:
        product_id: 要更新的产品ID
        product: 更新的产品数据对象，只包含需要更新的字段

    Returns:
        dict: 包含更新结果的字典
            - code: 状态码，0表示成功
            - message: 提示信息
            - updated_fields: 被更新的字段列表

    Raises:
        HTTPException: 当产品不存在时返回404，当更新失败时返回500
    """
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
    if product.manufacturer is not None:
        update_data["manufacturer"] = product.manufacturer

    # 如果没有需要更新的字段，直接返回
    if not update_data:
        return {"message": "No fields to update"}

    try:
        # 执行数据库更新操作
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

        return {
                "code": 0,
                "message": f"Product {product_id} updated",
                "updated_fields": list(update_data.keys())
                }

    except postgrest.APIError as e:
        raise HTTPException(status_code=500, detail=f"更新失败，: {e}")

#删除产品
@router.delete("/{product_id}")
def delete_product(
    product_id: int = Path(
        ...,
        gt=0,
        description="产品 ID，不能为空且必须大于 0"
    )
):
    """删除产品接口

    Args:
        product_id: 要删除的产品ID，必须大于0

    Returns:
        dict: 包含删除结果的字典
            - code: 状态码，0表示成功
            - message: 提示信息
            - deleted: 被删除的产品数据

    Raises:
        HTTPException: 当产品不存在时返回404，当删除失败时返回400
    """
    try:
        conn = get_supabase_client()
        # 执行数据库删除操作
        res = (
            conn
            .table("product")
            .delete()
            .eq("id", product_id)
            .execute()
        )
    except postgrest.APIError as e:
        raise HTTPException(status_code=400, detail=e.json())

    # 如果没有返回数据，说明产品不存在
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
    """查询产品接口

    Args:
        search: 可选的搜索关键词，支持模糊搜索条码、产品名称、类型、位置和单位

    Returns:
        dict: 包含查询结果的字典
            - code: 状态码，0表示成功
            - message: 提示信息
            - data: 产品列表，每个产品包含id、条码、名称、保质期等信息
    """
    conn = get_supabase_client()
    # 构建基础查询，选择所有需要的字段
    query = (
        conn
        .table("product")
        .select(
            "id, barcode, product_name, shelf_life_days, "
            "location, category, unit, manufacturer,created_at, updated_at"
        )
    )

    # 如果有搜索关键词，添加模糊搜索条件
    if search:
        like_value = f"%{search}%"
        query = query.or_(
            ",".join([
                f"barcode.ilike.{like_value}",
                f"product_name.ilike.{like_value}",
                f"category.ilike.{like_value}",
                f"location.ilike.{like_value}",
                f"unit.ilike.{like_value}",
                f"manufacturer.ilike.{like_value}",
            ])
        )

    # 统一执行并返回结果
    # 无论是否有 search，逻辑都保持一致
    res = query.execute()

    return {
        "code": 0,
        "message": "ok",
        "data": res.data  # 确保这里始终取 .data
    }

@router.get("/category",description="指定产品类型查询，只返回product.category字段，支持模糊查询")
def get_category(search: Optional[str] = Query(default=None)):
    """查询产品类型接口

    Args:
        search: 可选的搜索关键词，支持模糊查询产品类型

    Returns:
        dict: 包含查询结果的字典
            - code: 状态码，0表示成功
            - message: 提示信息
            - data: 产品类型列表（已去重）

    Raises:
        HTTPException: 当搜索关键词没有匹配结果时返回404
    """
    conn = get_supabase_client()

    # 构建查询，只选择 category 字段
    query = (
        conn
        .table("product")
        .select("category")
    )

    # 如果有搜索关键词，添加模糊搜索条件
    if search:
        like_value = f"%{search}%"
        query = query.like("category", like_value)

    # 执行查询
    res = query.execute()
    rows = res.data or []

    # 使用集合去重并过滤空值
    categories = list({
        row["category"]
        for row in rows
        if row.get("category")
    })

    # 如果有搜索关键词但没有结果，返回404
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
