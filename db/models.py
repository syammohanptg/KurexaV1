"""
db/models.py – SQLAlchemy models + table creation helper
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime,
    Text, Float, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


# ── Users ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255))
    is_admin      = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    symptom_checks = relationship("SymptomCheck", back_populates="user")


# ── Admin Feature Flags ───────────────────────────────────────────────────────
class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id          = Column(Integer, primary_key=True, index=True)
    feature_key = Column(String(100), unique=True, nullable=False)
    label       = Column(String(255))
    is_enabled  = Column(Boolean, default=True)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Symptom Checks (main history table) ──────────────────────────────────────
class SymptomCheck(Base):
    __tablename__ = "symptom_checks"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms    = Column(Text, nullable=False)
    location    = Column(String(500))
    raw_result  = Column(Text)          # full GPT JSON response
    risk_level  = Column(String(20))    # Low / Moderate / High
    created_at  = Column(DateTime, default=datetime.utcnow)

    user        = relationship("User", back_populates="symptom_checks")
    conditions  = relationship("DiagnosedCondition", back_populates="check")
    remedies    = relationship("HomeRemedy", back_populates="check")
    doctors     = relationship("DoctorRecommendation", back_populates="check")


# ── Diagnosed Conditions ──────────────────────────────────────────────────────
class DiagnosedCondition(Base):
    __tablename__ = "diagnosed_conditions"

    id          = Column(Integer, primary_key=True, index=True)
    check_id    = Column(Integer, ForeignKey("symptom_checks.id"), nullable=False)
    name        = Column(String(255))
    probability = Column(Float)
    description = Column(Text)
    severity    = Column(String(50))    # Mild / Moderate / Severe

    check       = relationship("SymptomCheck", back_populates="conditions")


# ── Home Remedies ─────────────────────────────────────────────────────────────
class HomeRemedy(Base):
    __tablename__ = "home_remedies"

    id          = Column(Integer, primary_key=True, index=True)
    check_id    = Column(Integer, ForeignKey("symptom_checks.id"), nullable=False)
    remedy      = Column(Text)
    category    = Column(String(100))   # hydration / diet / sleep / herbal / exercise
    duration    = Column(String(100))   # e.g. "3-5 days"

    check       = relationship("SymptomCheck", back_populates="remedies")


# ── Doctor Recommendations ────────────────────────────────────────────────────
class DoctorRecommendation(Base):
    __tablename__ = "doctor_recommendations"

    id              = Column(Integer, primary_key=True, index=True)
    check_id        = Column(Integer, ForeignKey("symptom_checks.id"), nullable=False)
    specialist_type = Column(String(255))
    reason          = Column(Text)
    nearby_doctors  = Column(JSON)      # list of {name, address, distance, rating}

    check           = relationship("SymptomCheck", back_populates="doctors")


# ── DB initialisation helper ──────────────────────────────────────────────────
DEFAULT_FLAGS = [
    ("possible_conditions",  "Possible Conditions (AI Prediction)"),
    ("home_remedies",        "Home Remedies"),
    ("doctor_recommendations","Recommended Doctors & Specialists"),
    ("risk_indicator",       "Risk & Urgency Indicator"),
    ("history_tracking",     "User History & Tracking"),
]

DEFAULT_ADMIN = {
    "email":     "admin@healthai.com",
    "password":  "Admin@123",
    "full_name": "System Admin",
}


def init_db(database_url: str):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Seed feature flags
    for key, label in DEFAULT_FLAGS:
        if not db.query(FeatureFlag).filter_by(feature_key=key).first():
            db.add(FeatureFlag(feature_key=key, label=label, is_enabled=True))

    # Seed admin user (use bcrypt directly)
    import bcrypt
    if not db.query(User).filter_by(email=DEFAULT_ADMIN["email"]).first():
        db.add(User(
            email=DEFAULT_ADMIN["email"],
            password_hash=bcrypt.hashpw(DEFAULT_ADMIN["password"].encode(), bcrypt.gensalt()).decode(),
            full_name=DEFAULT_ADMIN["full_name"],
            is_admin=True,
        ))

    db.commit()
    db.close()
    engine.dispose()
    return engine
