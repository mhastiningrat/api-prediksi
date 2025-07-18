import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime, timedelta

# Load data historis (10.000 data)
df = pd.read_csv("data_pinjaman_ppob1.csv").head(1000)
print("Kolom CSV:", df.columns.tolist())
df['nominal_transaksi'] = df['nominal_transaksi'].replace(',', '', regex=True).astype(float)
df['plafon'] = df['plafon'].replace(',', '', regex=True).astype(float)
df['tanggal_trans'] = pd.to_datetime(df['tanggal_trans'])

# Hitung bulan dan agregasi
# Ganti per minggu jadi per bulan

# Hitung bulan (format: 2024-07)
df['bulan'] = df['tanggal_trans'].dt.to_period('M').astype(str)

summary = df.groupby(['cust_no', 'bulan']).agg({
    'nominal_transaksi': 'sum',
    'plafon': 'mean'
}).reset_index()

# Hitung jumlah minggu dalam bulan
summary['minggu_dalam_bulan'] = pd.to_datetime(summary['bulan'] + '-01').dt.days_in_month / 7
summary['transaksi_per_minggu'] = summary['nominal_transaksi'] / summary['minggu_dalam_bulan']

# Hitung total pencairan per customer dari seluruh urutan cair
cair_per_cust = df.groupby('cust_no')['nominal_cair'].sum()
summary['penggunaan_plafon'] = summary['nominal_transaksi'] / summary['cust_no'].map(cair_per_cust)

# Tentukan label
labels = []

# Total pencairan per customer
total_cair = df.groupby('cust_no')['nominal_cair'].sum()
summary['total_cair'] = summary['cust_no'].map(total_cair)

for cust_no, group in summary.groupby('cust_no'):
    avg_transaksi_per_minggu = group['transaksi_per_minggu'].mean()
    avg_plafon = group['plafon'].mean()
    minggu_dlm_bulan = group['minggu_dalam_bulan'].mean()
    expected_cair = avg_plafon * minggu_dlm_bulan
    total_cair_value = total_cair.get(cust_no, 0)
    total_transaksi = avg_transaksi_per_minggu * minggu_dlm_bulan
    sisa = total_transaksi - total_cair_value
    terakhir_trans = pd.to_datetime(group['bulan'] + '-01').max()

    if terakhir_trans < datetime.now() - timedelta(days=180) and avg_plafon > 1_000_000:
        labels.append({'cust_no': cust_no, 'plafon': avg_plafon, 'label': 'turun'})
    elif total_cair_value == expected_cair and sisa > 0:
        labels.append({'cust_no': cust_no, 'plafon': avg_plafon, 'label': 'naik (1.000.000)'})
    elif total_cair_value < expected_cair and sisa > 0:
        labels.append({'cust_no': cust_no, 'plafon': avg_plafon, 'label': 'naik (500.000)'})
    elif total_cair_value == expected_cair and sisa <= 0:
        labels.append({'cust_no': cust_no, 'plafon': avg_plafon, 'label': 'tetap'})

    
        labels.append({'cust_no': cust_no, 'plafon': avg_plafon, 'label': 'tetap'})

label_df = pd.DataFrame(labels)

# ===== DEBUG INFO =====
print("Jumlah data awal:", len(df))
print("Jumlah data summary mingguan:", len(summary))
print("Jumlah label hasil penilaian:", len(label_df))
print("Distribusi label:")
print(label_df['label'].value_counts())


# Siapkan fitur X dan target y
# Hanya ambil label yang memiliki minimal 2 data
label_counts = label_df['label'].value_counts()
valid_labels = label_counts[label_counts >= 2].index
filtered_df = label_df[label_df['label'].isin(valid_labels)]

print("Setelah filter label >= 2:")
print("Jumlah data:", len(filtered_df))
print("Distribusi label valid:")
print(filtered_df['label'].value_counts())

X = filtered_df[['plafon']]
y = filtered_df['label']

# Train model hanya jika data cukup
if len(X) >= 5 and y.nunique() >= 2:
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=None, random_state=42, test_size=0.2)
    model = LogisticRegression(multi_class='multinomial', max_iter=1000)
    model.fit(X_train, y_train)

    joblib.dump(model, "model_plafon_logreg.pkl")
    print("Model saved to model_plafon_logreg.pkl")
else:
    print("❌ Data terlalu sedikit untuk training. Jumlah data:", len(X), ", Jumlah kelas:", y.nunique())	
	
	
# 'C100003179',
# 'C100008699',
# 'C100006240',
# 'C100006658',
# 'C100006686',
# 'C100001924',
# 'C100004191',
# 'C100003442',
# 'C100004511',
# 'C100003970',
# 'C100006045',
# 'C100007249',
# 'C100005028',
# 'C100006982',
# 'C100004241',
# 'C100004895',
# 'C100004332',
# 'C100007928',
# 'C100000485'

# notes 
# 	kecilin jumlah customer
#   coba /10 customer 
#  Prediksi customer yang belum dapat pinjaman
#   cek terlebih dahulu data apa yang sudah tersedia
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	












































































































