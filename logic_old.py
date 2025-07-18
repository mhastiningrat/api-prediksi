import pandas as pd
from datetime import datetime, timedelta
import joblib

model = joblib.load("model_plafon_logreg.pkl")

def prepare_features(data):
    df = pd.DataFrame(data)
    df['tanggal_trans'] = pd.to_datetime(df['tanggal_trans'])
    df['nominal_transaksi'] = df['nominal_transaksi'].astype(float)
    df['plafon'] = df['plafon'].astype(float)

    df['minggu'] = df['tanggal_trans'].dt.to_period('W').apply(lambda r: r.start_time)
    summary = df.groupby(['cust_no', 'minggu']).agg({
        'nominal_transaksi': 'sum',
        'plafon': 'mean'
    }).reset_index()
    summary['penggunaan_plafon'] = summary['nominal_transaksi'] / summary['plafon']

    result = []
    for idx, (cust_no, group) in enumerate(summary.groupby('cust_no'), start=1):
        avg_trans = group['nominal_transaksi'].mean()
        avg_plafon = group['plafon'].mean()
        avg_penggunaan = group['penggunaan_plafon'].mean()

        fitur = pd.DataFrame([[avg_plafon]], columns=['plafon'])
        rekomendasi = model.predict(fitur)[0]

        if rekomendasi == 'naik (1.000.000)':
            plafon_baru = avg_plafon + 1_000_000
        elif rekomendasi == 'naik (500.000)':
            plafon_baru = avg_plafon + 500_000
        elif rekomendasi == 'turun':
            plafon_baru = 1_000_000 if avg_plafon > 1_000_000 else avg_plafon
        else:
            plafon_baru = avg_plafon

        result.append({
            'id':idx,
            'cust_no': cust_no,
            'rata_rata_transaksi_per_minggu': round(avg_trans),
            'rata_rata_penggunaan': round(avg_penggunaan, 2),
            'rata_rata_plafon': round(avg_plafon),
            'rekomendasi': rekomendasi,
            'rekomendasi_plafon': round(plafon_baru)
        })

    return pd.DataFrame(result)