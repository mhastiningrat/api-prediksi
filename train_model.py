from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn.utils.multiclass import unique_labels
import joblib

# === 1. Ambil data dari PostgreSQL ===
def load_data_from_db():

    DATABASE_URL = ""
    engine = create_engine(DATABASE_URL)

    query = """
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
        WHERE ttl.tanggal_trans between '2024-01-01' and '2024-12-31' 
        LIMIT 15000
    """
# and ttl.cust_no in (
#         'C100003179', 'C100008699', 'C100006240','C100006658','C100006686','C100001924','C100004191','C100003442','C100004511','C100003970','C100006045','C100007249','C100005028','C100006982','C100004241','C100004895','C100004332','C100007928','C100000485','C100007659','C100002080','C100004024','C100000488','C100007295','C100001776','C100007289','C100004971','C100001384','C100004737','C100001616','C100003205','C100001879','C100001191','C100008073','C100006803','C100000406','C100006832','C100005100','C100007123','C100000411','C100003954','C100005423','C100006142','C100001558','C100005466','C100001038','C100008474','C100000407','C100004691','C100004569','C100002360','C100007265','C100001152','C100005472','C100005512','C100009000','C100003492','C100000832','C100008046','C100006629','C100004076','C100008346','C100007887','C100004422','C100004533','C100003969','C100003354','C100001533','C100006625','C100002447','C100006053','C100005156','C100006296','C100001161','C100003440','C100002440','C100000583','C100008273','C100001327','C100005674','C100001201','C100008653','C100003154','C100002474','C100008632','C100003337','C100004532','C100001024','C100003590','C100000386','C100001865','C100002351','C100001587','C100005213','C100000978','C100004126','C100000422','C100002018','C100001843','C100008355','C100000873','C100000953','C100000906','C100001403','C100001135','C100006807','C100000391','C100004243','C100001210','C100005705','C100000490','C100004823','C100008760','C100001192','C100003280','C100005522','C100001895','C100001951','C100004360','C100006477','C100004531','C100006098','C100000850','C100003188','C100001526','C100002408','C100007975','C100002046','C100000970','C100003485','C100008081','C100008166','C100000392','C100005800'
#         )
    print(query)
    df = pd.read_sql(query, engine)
    df['nominal_transaksi'] = df['total_cair'] + df['biaya_admin']
    return df

# === 2. Proses fitur & generate label otomatis ===
def build_features(df):
    print(df)
    df['tanggal_trans'] = pd.to_datetime(df['tanggal_trans'])
    df['tanggal_jttmp'] = pd.to_datetime(df['tanggal_jttmp'])
    df['tanggal_bayar'] = pd.to_datetime(df['tanggal_bayar'])

    df['is_late'] = (df['tanggal_bayar'] > df['tanggal_jttmp']).astype(int)
    df['minggu'] = df['tanggal_trans'].dt.to_period('W').apply(lambda r: r.start_time)

    result = []
    for cust_no, group in df.groupby('cust_no'):
        mingguan = group.groupby('minggu').agg({
            'nominal_transaksi': 'sum',
            'plafon': 'mean'
        }).reset_index()

        mingguan['penggunaan_plafon'] = mingguan['nominal_transaksi'] / mingguan['plafon']

        # Dapatkan tanggal_trans terakhir per cust_no
        last_trans = df.groupby('cust_no')['tanggal_trans'].max().reset_index()
        last_trans.columns = ['cust_no', 'tanggal_trans_terakhir']

        rata2_penggunaan = mingguan['penggunaan_plafon'].mean()
        maks_penggunaan = mingguan['penggunaan_plafon'].max()
        total_trans = len(group)
        total_telat = group['is_late'].sum()
        rasio_telat = total_telat / total_trans if total_trans > 0 else 0
        total_cair = group['nominal_transaksi'].sum()
        plafon_terakhir = group['plafon'].iloc[-1]
        tanggal_terakhir = pd.Timestamp(
            last_trans[last_trans['cust_no'] == cust_no]['tanggal_trans_terakhir'].values[0]
        )
        batas_6_bulan = pd.Timestamp("2024-06-30")
        

        # === Penentuan Label Otomatis ===
        if rata2_penggunaan >= 0.95 and rasio_telat < 0.4:
            label = 'Naik'
        elif tanggal_terakhir <= batas_6_bulan and plafon_terakhir > 1_000_000:
            label = 'Turun'
        else:
            label = 'Tetap'

        

        result.append({
            'cust_no': cust_no,
            'rata2_penggunaan_plafon': round(rata2_penggunaan, 2),
            'maks_penggunaan_plafon': round(maks_penggunaan, 2),
            'rasio_telat': round(rasio_telat, 2),
            'total_transaksi': total_trans,
            'total_telat': total_telat,
            'total_cair': round(total_cair),
            'plafon_terakhir': int(plafon_terakhir),
            'rekomendasi_plafon': label,
            'tanggal_trans_terakhir': tanggal_terakhir.strftime('%Y-%m-%d')
        })

    return pd.DataFrame(result)

# === 3. Train model ===
def train_model(df):
    label_encoder = LabelEncoder()
    df['label'] = label_encoder.fit_transform(df['rekomendasi_plafon'])

    features = [
        'rata2_penggunaan_plafon',
        'maks_penggunaan_plafon',
        'rasio_telat',
        'total_transaksi',
        'total_telat',
        'total_cair'
    ]

    X = df[features]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("=== Evaluation ===")
    labels = unique_labels(y_test, y_pred)
    target_names = label_encoder.inverse_transform(labels)
    print(classification_report(y_test, y_pred, target_names=target_names))

    joblib.dump(model, "model_plafon.pkl")
    print("✅ Model saved as 'model_plafon.pkl'")


# === MAIN ===
if __name__ == "__main__":
    df_raw = load_data_from_db()
    df_feat = build_features(df_raw)
    train_model(df_feat)
