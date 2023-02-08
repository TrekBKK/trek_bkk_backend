from fastapi import FastAPI
from routes import user_router

app = FastAPI()


def create_app():
    fast_app = FastAPI(title="trek-bkk backend")
    return fast_app


app = create_app()
app.include_router(user_router)
