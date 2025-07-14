# main.py (Versi Final - Lazy Initialization)
import os
import json
from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

# Variabel global untuk menampung koneksi database.
# Dimulai dengan None, akan diinisialisasi pada permintaan pertama.
db = None

def initialize_firebase():
    """
    Fungsi untuk menginisialisasi koneksi Firebase.
    Hanya akan berjalan jika koneksi belum ada.
    """
    global db
    # Jika db sudah ada isinya (dari permintaan sebelumnya), hentikan fungsi.
    if db is not None:
        return

    print("--- Mencoba inisialisasi koneksi Firebase... ---")
    try:
        # Coba ambil kredensial dari environment variable (untuk Vercel)
        service_account_str = os.getenv('FIREBASE_CREDENTIALS')
        if service_account_str:
            service_account_info = json.loads(service_account_str)
            print("Menginisialisasi dari Environment Variable...")
        else:
            # Jika tidak ada, coba dari file lokal (untuk development)
            with open('serviceAccountKey.json') as f:
                service_account_info = json.load(f)
            print("Menginisialisasi dari file lokal...")

        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        print("--- KONEKSI DATABASE BERHASIL ---")
    except Exception as e:
        print(f"--- KONEKSI DATABASE GAGAL: {e} ---")
        db = None

# Buat aplikasi FastAPI tanpa event startup
app = FastAPI(title="API Deteksi Harga Produk")

class Product(BaseModel):
    name: str; price: int; description: str; product_id: str

@app.get("/")
def read_root():
    # Selalu coba inisialisasi saat endpoint ini diakses
    initialize_firebase()
    return {"status": "OK" if db else "ERROR", "database_connected": db is not None}

@app.get("/api/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: str):
    # Selalu coba inisialisasi saat endpoint ini diakses
    initialize_firebase()

    if db is None:
        raise HTTPException(status_code=503, detail="Layanan database tidak tersedia karena gagal inisialisasi.")
    try:
        doc_ref = db.collection('products').document(product_id).get()
        if doc_ref.exists:
            return doc_ref.to_dict()
        else:
            raise HTTPException(status_code=404, detail=f"Produk dengan ID '{product_id}' tidak ditemukan.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
