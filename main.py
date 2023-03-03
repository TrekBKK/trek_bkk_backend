from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import user_router, generator_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


def create_app():
    fast_app = FastAPI(title="trek-bkk backend")
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fast_app.mount('/static', StaticFiles(directory='static'), name='static')
    return fast_app


app = create_app()
# uvicorn.run(app, host="0.0.0.0", port=8000)
app.include_router(user_router)
app.include_router(generator_router)
