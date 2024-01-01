from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from datetime import datetime, timedelta
from jose import JWTError, jwt
import feedparser

# Configure Auth0
AUTH0_DOMAIN = "dev-iequ56w4z8t4in3a.us.auth0.com"  
AUTH0_CLIENT_ID = "hD0iYIYgufgo6SmFrNL6dB2u3zMN2vi4"  
AUTH0_CLIENT_SECRET = "OVM4oYaVTyAX0kO4uGvcGbH2OYQbY2fn3JlJ45vhYAXidHUwGTTmW8cPid5ak1xZ"  

# Configure SQLite database
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Article model
class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    url = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the table
Base.metadata.create_all(bind=engine)

app = FastAPI()

# OAuth2 configuration for Auth0
oauth2_scheme = OAuth2AuthorizationCodeBearer(tokenUrl="token")

# Function to create a new JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH0_CLIENT_SECRET, algorithm="HS256")
    return encoded_jwt

# Dependency for validating the token and returning the user's info
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, AUTH0_CLIENT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise credentials_exception

# API endpoint to parse RSS
@app.post("/parse_rss")
async def parse_rss(url: str, current_user: dict = Depends(get_current_user)):
    # Check if the URL has been parsed in the last 10 minutes
    last_parsed_entry = await database.fetch_one(
        "SELECT * FROM articles WHERE url = :url AND created_at > :cutoff_time",
        {"url": url, "cutoff_time": datetime.utcnow() - timedelta(minutes=10)},
    )
    if last_parsed_entry:
        return {"titles": last_parsed_entry["title"], "descriptions": last_parsed_entry["description"]}

    # RSS parsing logic using feedparser
    parsed_data = {"titles": [], "descriptions": []}
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            parsed_data["titles"].append(entry.title)
            parsed_data["descriptions"].append(entry.summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing RSS: {str(e)}")

    # Save the parsed data to the database
    await database.execute(
        "INSERT INTO articles (title, description, url) VALUES (:title, :description, :url)",
        {"title": parsed_data["titles"][0], "description": parsed_data["descriptions"][0], "url": url},
    )

    return parsed_data

# API endpoint to get a new JWT token from Auth0
@app.post("/token")
async def login_for_access_token(code: str, state: str, current_user: dict = Depends(get_current_user)):
    # Auth0 token endpoint URL
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    
    # Auth0 token request payload
    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8000/login/callback",
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
    }

    # Request the token from Auth0
    response = await oauth2_scheme.token_request(token_url, method="POST", data=token_payload)

    # Extract user information from the token
    user_info = jwt.decode(response["access_token"], AUTH0_CLIENT_SECRET, algorithms=["HS256"])

    # Create a new JWT token for the user
    access_token = create_access_token(data={"sub": user_info["sub"]})

    return {"access_token": access_token, "token_type": "bearer"}


