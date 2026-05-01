from fastapi import FastAPI
from uvicorn import run

from contextlib import asynccontextmanager

from api import router
from config import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    print(0)
    yield
    if db.conn:
        await db.conn.close()
        print(1)

app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=8000, reload=True)