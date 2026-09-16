from fastapi import FastAPI
from routes.certificate_routes import router

app = FastAPI(title="RPC Certificate Verification")

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Certificate Verification Module is Running"}