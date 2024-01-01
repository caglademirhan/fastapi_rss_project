# RSS Feed Parser REST API

This project implements a REST API for extracting content from user-submitted URLs that point to RSS feeds. The API is built using FastAPI, SQLAlchemy for database management, and incorporates authentication via OAuth2 with Auth0. The parsed data is stored in an SQLite database.

## Features

1. **Parse RSS Feed:**
   - Users can submit any arbitrary URL for an RSS feed.
   - The system parses the URL and extracts links for all articles within the feed.

2. **Return Parsed Data:**
   - The system returns a list of article titles and descriptions in JSON format.

3. **Database Storage:**
   - Parsed URLs, titles, and descriptions are stored in an SQLite database.

4. **Caching:**
   - The system avoids parsing an RSS feed if it has been parsed in the last 10 minutes.
   - Instead, it returns the last parsed results from the SQLite database.

5. **Authentication:**
   - The API endpoint is protected using JSON Web Tokens (JWT) with OAuth2.
   - OAuth2 interactions are handled using Auth0.

## Requirements

- Python 3.7 or later
- FastAPI
- SQLAlchemy
- Auth0 Account (for OAuth2)
- SQLite

## Steps that I followed:

- mkdir fastapi_rss_project
- cd fastapi_rss_project
- python -m venv venv
- \venv\Scripts\activate (On Windows)
- pip install fastapi uvicorn[standard] sqlalchemy databases python-jose (installing necessary dependencies, feedparser, pytest-mock, etc.)
- created an free account on Auth0.
- obtain Auth0 domain, client ID, and client secret and use them into main application.
- for run the application and run the tests:

```bash

 uvicorn main:app --reload 
 pytest tests/

```

You can clone the repository:

   ```bash
   git clone https://github.com/caglademirhan/fastapi_rss_project.git
   cd fastapi_rss_project
