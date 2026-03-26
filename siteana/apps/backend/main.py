from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="SiteANA API", description="2D GIS 基地分析出圖系統核心 API", version="0.1.0")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境，之後需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to SiteANA API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
