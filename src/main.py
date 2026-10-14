from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.sessions import router as sessions_router
from src.api.routes.reviews import router as reviews_router
from src.api.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CodeLens AI",
    description="Multi-agent AI code review system powered by RAG and LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(reviews_router)
app.include_router(chat_router)


@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}


