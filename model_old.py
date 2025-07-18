from pydantic import BaseModel
from typing import List

class Record(BaseModel):
    cust_no: str
    plafon: float
    nominal_transaksi: float
    nominal_cair: float
    nominal_bayar: float
    tanggal_trans: str
    tanggal_cair: str
    tanggal_bayar: str
    tanggal_jttmp: str

class Records(BaseModel):
    records: List[Record]