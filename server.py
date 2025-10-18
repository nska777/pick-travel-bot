from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем доступ с сайта React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Тестовые туры ---
tours = [
    {"id": 1, "title": "Дубай 🇦🇪", "price": 1200, "days": 5},
    {"id": 2, "title": "Мальдивы 🏝️", "price": 2400, "days": 7},
    {"id": 3, "title": "Таиланд 🇹🇭", "price": 1500, "days": 6},
]

@app.get("/")
def root():
    return {"message": "Pick & Travel API is working!"}

@app.get("/tours")
def get_tours():
    return tours
