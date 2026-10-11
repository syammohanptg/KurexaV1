# ============================================================
#  HealthAI Configuration
#  Update these values before running the application
# ============================================================

# --- SQL Server Connection ---
# Format: mssql+pyodbc://user:password@host/dbname?driver=ODBC+Driver+17+for+SQL+Server
# For SQL Express (local): mssql+pyodbc://./SQLEXPRESS/HealthAI?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
# DATABASE_URL = "Server=localhost\SQLEXPRESS;Database=master;Trusted_Connection=True;"
DATABASE_URL = "mssql+pyodbc://healthaiuser:healthaiuser123@localhost\\SQLEXPRESS/HealthAI?driver=ODBC+Driver+17+for+SQL+Server"

# --- OpenAI / GPT Configuration ---
OPENAI_API_KEY = "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"
OPENAI_MODEL   = "gpt-4o"          # or "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 2000

# --- FastAPI Settings ---
API_HOST = "127.0.0.1"
API_PORT = 8000
API_SECRET_KEY = "change-me-to-a-long-random-secret"   # used for JWT

# --- Streamlit Settings ---
STREAMLIT_PORT = 8501
API_BASE_URL   = f"http://{API_HOST}:{API_PORT}"

# --- Google Places API (for nearby doctors) ---
# Leave blank to skip real geo-search; app shows placeholder data instead
GOOGLE_PLACES_API_KEY = ""

# --- App Metadata ---
APP_NAME    = "HealthAI Assistant"
APP_VERSION = "1.0.0"
