from pydantic import BaseModel
from typing import Literal

# === Input fitur yang akan dikirim ke model ===
class PlafonFeatureInput(BaseModel):
    rata2_penggunaan_plafon: float
    maks_penggunaan_plafon: float
    rasio_telat: float
    total_transaksi: int
    total_telat: int
    total_cair: float

# === Output prediksi ===
class PlafonPredictionResponse(BaseModel):
    cust_no: str
    rekomendasi: Literal["Naik", "Tetap"]
    nilai_rekomendasi: int