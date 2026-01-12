from fastapi import APIRouter
from database import get_db
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Literal
import uuid


router = APIRouter(
    prefix="/batches",
    tags=["batches"]
)


class BatchCreate(BaseModel):
    product_id: int
    # 自动生成批次号
    batch_code: str = Field(default_factory=lambda: f"BATCH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}")
    quantity: float
    manufacture_date: date
    expire_date: Optional[date] = None
    status: Literal["unopened", "opened", "expired", "used_up"] = "unopened"
    remarks: Optional[str] = None


@router.post("/")
def create_batch(batch: BatchCreate):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. 自动获取该产品的保质期天数
        cursor.execute("SELECT shelf_life_days FROM product WHERE id = %s", (batch.product_id,))
        product = cursor.fetchone()

        if not product:
            return {"error": "产品不存在"}

        # 2. 如果前端没传过期时间，则根据 生产日期 + 保质期 计算
        expire_date = batch.expire_date
        if not expire_date and batch.manufacture_date:
            # 逻辑：expire_date = manufacture_date + timedelta(days=product['shelf_life_days'])
            # 这里可以在 Python 中计算，也可以在下一步 SQL 中计算
            pass

        # 3. 插入数据库
        sql = """
            INSERT INTO batches (product_id, batch_code, quantity, manufacture_date, expire_date, status, remarks)
            VALUES (%s, %s, %s, %s, DATE_ADD(%s, INTERVAL (SELECT shelf_life_days FROM product WHERE id = %s) DAY), %s, %s)
        """
        # 注意：这里演示了直接在 SQL 中用 DATE_ADD 计算
        params = (
            batch.product_id, batch.batch_code, batch.quantity,
            batch.manufacture_date, batch.manufacture_date, batch.product_id,
            batch.status, batch.remarks
        )

        cursor.execute(sql, params)
        conn.commit()

        return {
            "message": "Batch added successfully",
            "batch_id": cursor.lastrowid,
            "batch_code": batch.batch_code  # 返回自动生成的单号给前端
        }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


@router.get("/")
def get_batches(
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        expired_only: bool = False,
        page: int = 1,
        size: int = 20
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. 基础 SQL：关联两张表获取详细信息
        sql = """
            SELECT 
                b.*, 
                p.product_name, 
                p.barcode, 
                p.unit,
                DATEDIFF(b.expire_date, CURDATE()) as days_to_expire
            FROM batches b
            JOIN product p ON b.product_id = p.id
            WHERE 1=1
        """
        params = []

        # 2. 动态构建筛选条件
        if product_id:
            sql += " AND b.product_id = %s"
            params.append(product_id)

        if status:
            sql += " AND b.status = %s"
            params.append(status)

        if expired_only:
            sql += " AND b.expire_date < CURDATE()"

        # 3. 分页逻辑
        offset = (page - 1) * size
        sql += " ORDER BY b.received_date DESC LIMIT %s OFFSET %s"
        params.extend([size, offset])

        cursor.execute(sql, params)
        results = cursor.fetchall()

        return {
            "total_count": len(results),
            "page": page,
            "data": results
        }
    finally:
        cursor.close()
        conn.close()


