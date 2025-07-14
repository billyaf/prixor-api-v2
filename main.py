# main.py
import os
import json
from fastapi import FastAPI, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from pydantic import BaseModel

db = None

async def initialize_database():
    global db
    try:
        # Coba ambil kredensial dari environment variable (untuk Vercel)
        service_account_str = os.getenv('FIREBASE_CREDENTIALS')
        if service_account_str:
            service_account_info = json.loads(service_account_str)
            print("Menginisialisasi Firebase dari Environment Variable...")
        else:
            # Jika tidak ada, coba dari file lokal (untuk development)
            with open('serviceAccountKey.json') as f:
                service_account_info = json.load(f)
            print("Menginisialisasi Firebase dari file lokal...")

        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        print("--- KONEKSI DATABASE BERHASIL ---")
    except Exception as e:
        print(f"--- KONEKSI DATABASE GAGAL: {e} ---")
        db = None

app = FastAPI(on_startup=[initialize_database])

class Product(BaseModel):
    name: str; price: int; description: str; product_id: str

@app.get("/")
def read_root():
    return {"status": "OK" if db else "ERROR", "database_connected": db is not None}

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
