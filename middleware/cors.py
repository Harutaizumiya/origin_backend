from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    """
    配置CORS中间件
    """
    origins = [
        "0.0.0.0",
        "127.0.0.1"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )