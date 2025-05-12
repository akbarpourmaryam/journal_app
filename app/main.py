from fastapi import FastAPI, Request, Form, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.utils import detect_emotion
from app.auth import hash_password, verify_password
from app.database import init_db, SessionLocal, User, Entry
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer

app = FastAPI()
templates = Jinja2Templates(directory="templates")
init_db()  # create DB if it doesn’t exist

# simple cookie signer
serializer = URLSafeSerializer("SUPER_SECRET_KEY", salt="cookie")

# session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get("session")
    if not cookie:
        return None
    try:
        user_id = serializer.loads(cookie)
        return db.query(User).filter(User.id == user_id).first()
    except:
        return None

@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already exists"})
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(response: Response, request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = serializer.dumps(user.id)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="session", value=token, httponly=True)
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "username": user.username})

@app.post("/submit", response_class=HTMLResponse)
def submit(request: Request, entry: str = Form(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    mood = detect_emotion(entry)
    new_entry = Entry(user_id=user.id, content=entry, mood=mood)
    db.add(new_entry)
    db.commit()
    return templates.TemplateResponse("index.html", {"request": request, "mood": mood, "username": user.username})
