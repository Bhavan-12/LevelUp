import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.seed import seed_initial_data
from app.routers import auth, users, habits, tracking, social, leaderboard, gamification, analytics

app = FastAPI(title="LevelUp Habit Tracker API", version="1.0.0")

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Database Initialization & Seeding on Startup
@app.on_event("startup")
def startup_event():
    init_db()
    seed_initial_data()

# 3. Mount Static Files & Templates
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# 4. Include Modular API Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(habits.router)
app.include_router(tracking.router)
app.include_router(social.router)
app.include_router(leaderboard.router)
app.include_router(gamification.router)
app.include_router(analytics.router)

# 5. Serve Main Single-Page Application (SPA) HTML Layout
@app.get("/")
def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})