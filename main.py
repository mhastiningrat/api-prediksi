from fastapi import FastAPI, Query
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from logic import prepare_features, get_data_from_db
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sesuaikan kalau mau secure
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
