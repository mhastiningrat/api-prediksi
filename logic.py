from sqlalchemy import create_engine,text
import psycopg2
import pandas as pd
from datetime import datetime
import joblib
import numpy as np

# Load model logistic regression
model = joblib.load("model_plafon.pkl")

def get_data_from_db(cust_no=None, start_date=None, end_date=None):
    print(cust_no)
    print(start_date)
    print(end_date)
    DATABASE_URL = ""
    engine = create_engine(DATABASE_URL)

    base_query = """
        select 
        ttl.no_trans_lending,
        ttl.cust_no,ttl.plafon,
        ttl.total_cair,
        ttl.biaya_admin,
        ttl.tanggal_trans ,
        ttl.tanggal_jttmp ,
        ttl.total_bayar, 
        ttp.tanggal_bayar 
        from gateway.tlen_trans_lending ttl 
        left join gateway.tlen_trans_pembayaran ttp on ttl.no_trans_lending = ttp.no_trans_lending 
        WHERE 1=1
    """

    filters = []
    params = {}

    if cust_no:
        filters.append("AND ttl.cust_no = :cust_no")
        params['cust_no']=cust_no
    else:
        filters.append("AND ttl.cust_no in (" \
        "'C100003179', 'C100008699', 'C100006240','C100006658','C100006686'," \
        "'C100001924','C100004191','C100003442','C100004511','C100003970'," \
        "'C100006045','C100007249','C100005028','C100006982','C100004241'," \
        "'C100004895','C100004332','C100007928','C100000485','C100007659'," \
        "'C100002080','C100004024','C100000488','C100007295','C100001776'," \
        "'C100007289','C100004971','C100001384','C100004737','C100001616'," \
        "'C100003205','C100001879','C100001191','C100008073','C100006803'," \
        "'C100000406','C100006832','C100005100','C100007123','C100000411'," \
        "'C100003954','C100005423','C100006142','C100001558','C100005466'," \
        "'C100001038','C100008474','C100000407','C100004691','C100004569'," \
        "'C100002360','C100007265','C100001152','C100005472','C100005512'," \
        "'C100009000','C100003492','C100000832','C100008046','C100006629'," \
        "'C100004076','C100008346','C100007887','C100004422','C100004533'," \
        "'C100003969','C100003354','C100001533','C100006625','C100002447'," \
        "'C100006053','C100005156','C100006296','C100001161','C100003440'," \
        "'C100002440','C100000583','C100008273','C100001327','C100005674'," \
        "'C100001201','C100008653','C100003154','C100002474','C100008632'," \
        "'C100003337','C100004532','C100001024','C100003590','C100000386'," \
        "'C100001865','C100002351','C100001587','C100005213','C100000978'," \
        "'C100004126','C100000422','C100002018','C100001843','C100008355'," \
        "'C100000873','C100000953','C100000906','C100001403','C100001135'," \
        "'C100006807','C100000391','C100004243','C100001210','C100005705'," \
        "'C100000490','C100004823','C100008760','C100001192','C100003280'," \
        "'C100005522','C100001895','C100001951','C100004360','C100006477'," \
        "'C100004531','C100006098','C100000850','C100003188','C100001526'," \
        "'C100002408','C100007975','C100002046','C100000970','C100003485'," \
        "'C100008081','C100008166','C100000392','C100005800')")

        



    if start_date:
        filters.append("AND ttl.tanggal_trans >= :start_date")
        params['start_date']=start_date
    if end_date:
        filters.append("AND ttl.tanggal_trans <= :end_date")
        params['end_date']=end_date
   

    final_query = f"""{base_query} {' '.join(filters)} ORDER BY ttl.tanggal_trans"""
    print(final_query)
    df = pd.read_sql(text(final_query), engine, params=params)
    df['nominal_transaksi'] = df['total_cair'] + df['biaya_admin']
    return df

def prepare_features(data):
    df = pd.DataFrame(data)
    df['tanggal_trans'] = pd.to_datetime(df['tanggal_trans'])
    df['tanggal_jttmp'] = pd.to_datetime(df['tanggal_jttmp'])
    df['tanggal_bayar'] = pd.to_datetime(df['tanggal_bayar'])

    # Hitung nilai total cair
    df['nominal_transaksi'] = df['nominal_transaksi'].astype(float)
    df['plafon'] = df['plafon'].astype(float)
    df['minggu'] = df['tanggal_trans'].dt.to_period('W').apply(lambda r: r.start_time)

    # Hitung keterlambatan
    df['is_late'] = (df['tanggal_bayar'] > df['tanggal_jttmp']).astype(int)

    result = []
    for idx, (cust_no, group) in enumerate(df.groupby('cust_no'), start=1):
        mingguan = group.groupby('minggu').agg({
            'nominal_transaksi': 'sum',
            'plafon': 'mean'
        }).reset_index()
        mingguan['penggunaan_plafon'] = mingguan['nominal_transaksi'] / mingguan['plafon']

        # Dapatkan tanggal_trans terakhir per cust_no
        last_trans = df.groupby('cust_no')['tanggal_trans'].max().reset_index()
        last_trans.columns = ['cust_no', 'tanggal_trans_terakhir']

        # Fitur untuk ML
        rata2_penggunaan = mingguan['penggunaan_plafon'].mean()
        maks_penggunaan = mingguan['penggunaan_plafon'].max()
        total_trans = group.shape[0]
        total_telat = group['is_late'].sum()
        rasio_telat = total_telat / total_trans if total_trans > 0 else 0
        total_cair = group['nominal_transaksi'].sum()
        plafon_terakhir = group['plafon'].iloc[-1]
        

        # Prediksi
        fitur_model = np.array([[
            rata2_penggunaan,
            maks_penggunaan,
            rasio_telat,
            total_trans,
            total_telat,
            total_cair
        ]])

        pred = model.predict(fitur_model)[0]
        label = "Naik" if pred == 1 else "Tetap"

        # Hitung rekomendasi plafon
        if label == "Naik":
            if rata2_penggunaan > 0.95:
                plafon_baru = plafon_terakhir + 1_000_000
                label_detail = "Naik (1.000.000)"
            else:
                plafon_baru = plafon_terakhir + 500_000
                label_detail = "Naik (500.000)"
        elif label == "Turun":
            plafon_baru = 1_000_000
            label_detail = "Turun"
        else:
            plafon_baru = plafon_terakhir
            label_detail = "Tetap"

        tanggal_terakhir = pd.Timestamp(
            last_trans[last_trans['cust_no'] == cust_no]['tanggal_trans_terakhir'].values[0]
        )

        result.append({
            'id': idx,
            'cust_no': cust_no,
            'rata_rata_penggunaan': round(rata2_penggunaan, 2),
            'maks_penggunaan': round(maks_penggunaan, 2),
            'total_transaksi': total_trans,
            'total_telat': total_telat,
            'rasio_telat': round(rasio_telat, 2),
            'total_cair': round(total_cair),
            'plafon_sekarang': int(plafon_terakhir),
            'rekomendasi': label_detail,
            'plafon_rekomendasi': int(plafon_baru),
            'tanggal_trans_terakhir': tanggal_terakhir.strftime('%Y-%m-%d')
        })

    return pd.DataFrame(result)


