# main.py (Versi Debugging Lanjutan)
import os
import json
from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

db = None
# Variabel ini akan menyimpan pesan diagnostik
DIAGNOSTIC_MESSAGE = "Proses inisialisasi belum dimulai."

def initialize_database():
    global db, DIAGNOSTIC_MESSAGE
    try:
        DIAGNOSTIC_MESSAGE = "Langkah 1: Mencoba membaca environment variable 'FIREBASE_CREDENTIALS'."
        service_account_str = os.getenv('FIREBASE_CREDENTIALS')

        if not service_account_str:
            DIAGNOSTIC_MESSAGE = "GAGAL di Langkah 1: Environment variable 'FIREBASE_CREDENTIALS' tidak ditemukan atau kosong. Aplikasi akan berhenti."
            print(DIAGNOSTIC_MESSAGE)
            return

        DIAGNOSTIC_MESSAGE = f"Langkah 2: Berhasil membaca env var. Panjang karakter: {len(service_account_str)}. Mencoba parsing JSON."
        print(DIAGNOSTIC_MESSAGE)
        service_account_info = json.loads(service_account_str)

        DIAGNOSTIC_MESSAGE = "Langkah 3: Berhasil parsing JSON. Mencoba membuat kredensial."
        print(DIAGNOSTIC_MESSAGE)
        cred = credentials.Certificate(service_account_info)

        DIAGNOSTIC_MESSAGE = "Langkah 4: Berhasil membuat kredensial. Mencoba inisialisasi Firebase App."
        print(DIAGNOSTIC_MESSAGE)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        DIAGNOSTIC_MESSAGE = "Langkah 5: Berhasil inisialisasi App. Mencoba mendapatkan klien Firestore."
        print(DIAGNOSTIC_MESSAGE)
        db = firestore.client()

        DIAGNOSTIC_MESSAGE = "--- SEMUA LANGKAH BERHASIL. KONEKSI DATABASE SUKSES. ---"
        print(DIAGNOSTIC_MESSAGE)

    except Exception as e:
        # Jika ada error di langkah mana pun, kita akan menangkapnya di sini.
        error_detail = f"Error pada '{DIAGNOSTIC_MESSAGE}' - Detail: {str(e)}"
        DIAGNOSTIC_MESSAGE = error_detail
        print(f"--- KONEKSI DATABASE GAGAL: {DIAGNOSTIC_MESSAGE} ---")
        db = None

app = FastAPI(on_startup=[initialize_database])

class Product(BaseModel):
    name: str; price: int; description: str; product_id: str

@app.get("/")
def read_root():
    # Endpoint ini sekarang akan melaporkan status terakhir dari proses inisialisasi.
    return {
        "status": "OK" if db else "ERROR", 
        "database_connected": db is not None,
        "diagnostic_message": DIAGNOSTIC_MESSAGE
    }

@app.get("/api/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Layanan database tidak tersedia.")
    try:
        doc_ref = db.collection('products').document(product_id).get()
        if doc_ref.exists:
            return doc_ref.to_dict()
        else:
            raise HTTPException(status_code=404, detail=f"Produk dengan ID '{product_id}' tidak ditemukan.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))