from fastapi import FastAPI
from starlette.responses import HTMLResponse

from middleware.cors import setup_cors
from routers import users, product, batches


app = FastAPI(
    title="智能效期管理系统",
    description="基于fastapi开发的商业效期管理系统",
    version="0.0.1"
)
__all__ = ["setup_cors"]
setup_cors(app)

# 注册路由
app.include_router(users.router)
app.include_router(product.router)
app.include_router(batches.router)

@app.get("/",response_class=HTMLResponse)
async def hello():
    with open('./index.html','r',encoding="utf-8") as f:
        return f.read()


#局域网开发
#poetry run uvicorn origin_backend:app --host 0.0.0.0 --port 8000 --reload

#本地开发
#uvicorn origin_backend:app --reload
