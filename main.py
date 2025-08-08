from fastapi import FastAPI, Query,Request
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from logic import prepare_features, get_data_from_db
from user import userRegistration, userLogin
from analytic import getDataSixMonth
import pandas as pd
import asyncpg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sesuaikan kalau mau secure
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql://neondb_owner:npg_0NhJsCfg2HUT@ep-lingering-truth-ad83kw5t.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.create_pool(DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

class RegistrationRequest(BaseModel):
    username: str
    no_hp: str
    password: str
    email: EmailStr

class LoginRequest(BaseModel):
    no_hp: str
    password: str

class TokenResponse(BaseModel):
    responseStatus:int
    message:str
    access_token: str
    token_type: str = "bearer"

# Endpoint dinamis dengan parameter
@app.get("/rekomendasi-plafon")
async def rekomendasi_plafon(
    cust_no: Optional[str] = Query(None),
    start_date: Optional[str] = '2024-01-01',
    end_date: Optional[str] = '2024-12-31'
):
    # Ambil data dari database
    df = get_data_from_db(cust_no, start_date, end_date)

    if df.empty:
        return JSONResponse(content={"message": "Data tidak ditemukan"}, status_code=404)

    # Proses prediksi
    hasil = prepare_features(df.to_dict(orient="records"))
    return JSONResponse(content=hasil.to_dict(orient="records"))


@app.post("/registration")
async def registration(payload: RegistrationRequest):
    # print(payload)
    data = userRegistration(payload)
    return JSONResponse(data)

@app.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request):
    db = request.app.state.db

    data = await userLogin(payload,db)
    return data

@app.get("/analytic")
async def dataSixMonth(cust_no:str, request: Request):
    print(cust_no)
    db = request.app.state.db

    data = await getDataSixMonth(cust_no,db)
    return data
