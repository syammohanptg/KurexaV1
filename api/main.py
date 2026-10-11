"""
api/main.py – FastAPI application
Run with:  uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
"""

import asyncio
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from typing import Optional, List

import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import config
from db.models import (
    Base, User, FeatureFlag, SymptomCheck,
    DiagnosedCondition, HomeRemedy, DoctorRecommendation, init_db
)

# ── App bootstrap ─────────────────────────────────────────────────────────────
app = FastAPI(title="HealthAI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

engine = init_db(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class _PwdCtx:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

pwd_ctx = _PwdCtx()
oauth2   = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_ALGO = "HS256"


# ── DB dependency ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth helpers ──────────────────────────────────────────────────────────────
def create_token(data: dict, expires_minutes: int = 480):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, config.API_SECRET_KEY, algorithm=JWT_ALGO)


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, config.API_SECRET_KEY, algorithms=[JWT_ALGO])
        user_id: int = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool
    full_name: str
    user_id: int

class SymptomRequest(BaseModel):
    symptoms: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = ""

class FeatureFlagUpdate(BaseModel):
    is_enabled: bool

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""
    is_admin: bool = False


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.post("/auth/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=req.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=req.email,
        password_hash=pwd_ctx.hash(req.password),
        full_name=req.full_name,
    )
    db.add(user); db.commit(); db.refresh(user)
    return {"message": "Registered successfully", "user_id": user.id}


@app.post("/auth/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=form.username, is_active=True).first()
    if not user or not pwd_ctx.verify(form.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token, is_admin=user.is_admin,
        full_name=user.full_name or user.email, user_id=user.id
    )


# ── Feature flags ─────────────────────────────────────────────────────────────
@app.get("/features")
def get_features(db: Session = Depends(get_db)):
    flags = db.query(FeatureFlag).all()
    return [{"key": f.feature_key, "label": f.label, "enabled": f.is_enabled} for f in flags]


@app.patch("/admin/features/{key}")
def toggle_feature(key: str, body: FeatureFlagUpdate,
                   admin=Depends(require_admin), db: Session = Depends(get_db)):
    flag = db.query(FeatureFlag).filter_by(feature_key=key).first()
    if not flag:
        raise HTTPException(404, "Feature not found")
    flag.is_enabled = body.is_enabled
    flag.updated_at = datetime.utcnow()
    db.commit()
    return {"key": key, "enabled": flag.is_enabled}


# ── Admin: user management ─────────────────────────────────────────────────────
@app.get("/admin/users")
def list_users(admin=Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name,
             "is_admin": u.is_admin, "is_active": u.is_active,
             "created_at": u.created_at.isoformat()} for u in users]


@app.post("/admin/users", status_code=201)
def create_user(req: UserCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=req.email).first():
        raise HTTPException(400, "Email already exists")
    u = User(email=req.email, password_hash=pwd_ctx.hash(req.password),
              full_name=req.full_name, is_admin=req.is_admin)
    db.add(u); db.commit(); db.refresh(u)
    return {"message": "User created", "user_id": u.id}


@app.patch("/admin/users/{user_id}/toggle")
def toggle_user(user_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    u.is_active = not u.is_active
    db.commit()
    return {"user_id": user_id, "is_active": u.is_active}


# ── GPT helper ────────────────────────────────────────────────────────────────
def get_enabled_features(db: Session) -> List[str]:
    return [f.feature_key for f in db.query(FeatureFlag).filter_by(is_enabled=True).all()]


def build_prompt(symptoms: str, location: str, features: List[str]) -> str:
    sections = []

    if "possible_conditions" in features:
        sections.append(
            '"possible_conditions": [array of up to 5 objects with: '
            '"name" (string), "probability" (integer 1-100), '
            '"description" (string, max 2 sentences), '
            '"severity" ("Mild"|"Moderate"|"Severe")]'
        )

    if "home_remedies" in features:
        sections.append(
            '"home_remedies": [array of objects with: '
            '"remedy" (string), "category" ("hydration"|"diet"|"sleep"|"herbal"|"exercise"), '
            '"duration" (string e.g. "3-5 days")]'
        )

    if "doctor_recommendations" in features:
        sections.append(
            '"doctor_recommendations": [array of objects with: '
            '"specialist_type" (string), "reason" (string)]'
        )

    if "risk_indicator" in features:
        sections.append(
            '"risk_level": "Low"|"Moderate"|"High", '
            '"risk_explanation": (string, 1 sentence)'
        )

    schema = "{\n  " + ",\n  ".join(sections) + "\n}"

    return f"""You are a medical AI assistant. A user reports the following symptoms:

SYMPTOMS: {symptoms}
LOCATION: {location or "Not specified"}

Based ONLY on the reported symptoms, respond with a JSON object matching this exact schema:
{schema}

Important rules:
- Be medically accurate but conservative.
- Never replace professional medical advice.
- Respond ONLY with valid JSON, no markdown, no explanations outside JSON.
- If a field is not requested in the schema, do not include it.
"""


async def call_openai(prompt: str) -> dict:
    models = [config.OPENAI_MODEL, "gpt-4o-mini"]

    for attempt, model in enumerate(models):
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": config.OPENAI_MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=body,
                )
                if r.status_code == 429:
                    retry_after = float(r.headers.get("Retry-After", "2"))
                    if attempt < len(models) - 1:
                        await asyncio.sleep(retry_after + 1)
                        continue
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            "OpenAI API rate limit reached. The key is valid, but the account "
                            "has hit its quota/rate limit for this model. Wait a few minutes or "
                            "increase the billing/quota for your OpenAI project."
                        ),
                    )
                r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                retry_after = float(exc.response.headers.get("Retry-After", "2"))
                if attempt < len(models) - 1:
                    await asyncio.sleep(retry_after + 1)
                    continue
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "OpenAI API rate limit reached. The key is valid, but the account "
                        "has hit its quota/rate limit for this model. Wait a few minutes or "
                        "increase the billing/quota for your OpenAI project."
                    ),
                ) from exc
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI request failed: {exc.response.text[:500] if exc.response else str(exc)}",
            ) from exc

        text = r.json()["choices"][0]["message"]["content"]
        return json.loads(text)

    raise HTTPException(status_code=502, detail="OpenAI request failed without a response.")


async def fetch_nearby_doctors(lat: float, lng: float, specialist: str) -> list:
    if not config.GOOGLE_PLACES_API_KEY or not lat or not lng:
        return []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "doctor",
        "keyword": specialist,
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
    results = r.json().get("results", [])[:3]
    return [{"name": p.get("name"), "address": p.get("vicinity"),
             "rating": p.get("rating"), "distance": None} for p in results]


# ── Main symptom-check endpoint ───────────────────────────────────────────────
@app.post("/symptom-check")
async def symptom_check(req: SymptomRequest,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    features = get_enabled_features(db)
    if not features:
        raise HTTPException(400, "No features are currently enabled by the admin.")

    location_str = req.location_name or (
        f"{req.latitude},{req.longitude}" if req.latitude else "Unknown"
    )
    prompt  = build_prompt(req.symptoms, location_str, features)
    gpt_raw = await call_openai(prompt)

    # ── Persist to DB ──────────────────────────────────────────────────────────
    check = SymptomCheck(
        user_id=current_user.id,
        symptoms=req.symptoms,
        location=location_str,
        raw_result=json.dumps(gpt_raw),
        risk_level=gpt_raw.get("risk_level"),
    )
    db.add(check); db.flush()   # get check.id before adding children

    for cond in gpt_raw.get("possible_conditions", []):
        db.add(DiagnosedCondition(
            check_id=check.id,
            name=cond.get("name"),
            probability=cond.get("probability"),
            description=cond.get("description"),
            severity=cond.get("severity"),
        ))

    for rem in gpt_raw.get("home_remedies", []):
        db.add(HomeRemedy(
            check_id=check.id,
            remedy=rem.get("remedy"),
            category=rem.get("category"),
            duration=rem.get("duration"),
        ))

    for doc in gpt_raw.get("doctor_recommendations", []):
        nearby = await fetch_nearby_doctors(
            req.latitude, req.longitude, doc.get("specialist_type", "doctor")
        )
        db.add(DoctorRecommendation(
            check_id=check.id,
            specialist_type=doc.get("specialist_type"),
            reason=doc.get("reason"),
            nearby_doctors=nearby,
        ))

    db.commit()

    return {
        "check_id":   check.id,
        "features":   features,
        "result":     gpt_raw,
        "created_at": check.created_at.isoformat(),
    }


# ── History endpoint ──────────────────────────────────────────────────────────
@app.get("/history")
def get_history(current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    checks = (db.query(SymptomCheck)
                .filter_by(user_id=current_user.id)
                .order_by(SymptomCheck.created_at.desc())
                .limit(20).all())
    result = []
    for c in checks:
        result.append({
            "id":         c.id,
            "symptoms":   c.symptoms,
            "location":   c.location,
            "risk_level": c.risk_level,
            "created_at": c.created_at.isoformat(),
            "conditions": [
                {"name": x.name, "probability": x.probability, "severity": x.severity}
                for x in c.conditions
            ],
        })
    return result


@app.get("/history/{check_id}")
def get_history_detail(check_id: int,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    c = db.query(SymptomCheck).filter_by(id=check_id, user_id=current_user.id).first()
    if not c:
        raise HTTPException(404, "Record not found")
    return {
        "id":         c.id,
        "symptoms":   c.symptoms,
        "location":   c.location,
        "risk_level": c.risk_level,
        "created_at": c.created_at.isoformat(),
        "result":     json.loads(c.raw_result) if c.raw_result else {},
        "conditions": [
            {"name": x.name, "probability": x.probability,
             "description": x.description, "severity": x.severity}
            for x in c.conditions
        ],
        "remedies": [
            {"remedy": x.remedy, "category": x.category, "duration": x.duration}
            for x in c.remedies
        ],
        "doctors": [
            {"specialist_type": x.specialist_type, "reason": x.reason,
             "nearby_doctors": x.nearby_doctors or []}
            for x in c.doctors
        ],
    }


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
