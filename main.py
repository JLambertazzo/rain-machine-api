from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from keys import CDB_PASS, OWM_KEY
from shortuuid import uuid
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cockroachdb.sqlalchemy import run_transaction
import requests
from time import time

# tags for documentation page
tags_metadata = [
  {
    "name": "Documentation",
    "description": "The route for this page"
  },
  {
    "name": "Weather Query",
    "description": "Routes for querying weather options"
  },
]

# create api
app = FastAPI(
  title="Rain Machine API",
  description="An api to get options for Rain Machine js library - Created by Julien Bertazzo Lambert",
  version="0.0.1",
  openapi_tags=tags_metadata
)
# base for sqlalchemy models
Base = declarative_base()

# Database Model
class Query(Base):
  __tablename__ = 'query'
  id = Column(String(100), primary_key=True)
  query = Column(String(100), nullable=False)
  updatedAt = Column(Integer(), nullable=False)
  precipitation = Column(String(100), nullable=False)
  wind = Column(Integer(), nullable=False)
  clouds = Column(Integer(), nullable=False)
  sunrise = Column(Integer(), nullable=False)
  sunset = Column(Integer(), nullable=False)

  def __repr__(self):
    return f"{self.query}: {self.precipitation} updated at {updatedAt}"

# Pydantic model (for req bodies)
class QueryCreate(BaseModel):
  query: str
  updatedAt: int
  precipitation: str
  wind: int
  clouds: int
  sunrise: int
  sunset: int

# db engine
engine = create_engine(
  f"cockroachdb://julien:{CDB_PASS}@free-tier.gcp-us-central1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=certs/cc-ca.crt&options=--cluster%3Dgood-bat-867",
  echo=True
)
# initialize
Base.metadata.create_all(engine)
sessionmaker = sessionmaker(engine)

# api routes
@app.get('/', tags=['Documentation'])
def root():
  return RedirectResponse('/docs', 301)

@app.get('/weather/{weather_query}', tags=['Weather Query'])
def get_sports(weather_query: str):
  def callback(session, weather_query):
    found = session.query(Query).filter_by(query=weather_query).first()
    if found:
      return {precipitation:found.precipitation,wind:found.wind,numClouds:found.clouds,lightData:{sunrise:found.sunrise,sunset:found.sunset}}
    else:
      r=requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={weather_query}&appid={OWM_KEY}")
      precip = "none"
      if (r.weather[0].id//100 in [2,3,5]):
        precip = "rain"
      elif (r.weather[0].id//100 == 8):
        precip = "snow"
      new_query = Query(query=weather_query,updatedAt=(int)(time()*1000),precipitation=precip,wind=r.wind.speed,clouds=r.clouds.all,sunrise=r.sys.sunrise,sunset=r.sys.sunset)
      session.add(new_query)
      return {precipitation:new_query.precipitation,wind:new_query.wind,numClouds:new_query.clouds,lightData:{sunrise:new_query.sunrise,sunset:new_query.sunset}}
  result = run_transaction(sessionmaker, lambda s: callback(s, weather_query))
  return result

# @app.post('/sports', tags=['General Sports Operations'])
# def post_sport(sport: SportsCreate):
#   def callback(session, sport):
#     new_sport = Sports(id=uuid(), name=sport.name, description=sport.description)
#     session.add(new_sport)
#     return {"id": new_sport.id, "name": new_sport.name, "description": new_sport.description}
#   return run_transaction(sessionmaker, lambda s: callback(s, sport))

# @app.get('/sports/{sport_id}', tags=['Specific Sports Operations'])
# def get_sport(sport_id: str):
#   def callback(session, sport_id):
#     found = session.query(Sports).filter_by(id=sport_id).first()
#     if found:
#       return {"id": found.id, "name": found.name, "description": found.description}
#     else:
#       raise HTTPException(status_code=404, detail="Sport not found")
#   return run_transaction(sessionmaker, lambda s: callback(s, sport_id))

# @app.patch('/sports/{sport_id}', tags=['Specific Sports Operations'])
# def patch_sport(sport_id: str, sport: SportsCreate):
#   def callback(session, sport_id, sport):
#     found = session.query(Sports).filter_by(id=sport_id).update({"name": sport.name, "description": sport.description})
#     if not found:
#       raise HTTPException(status_code=404, detail="Sport not found")
#     return {"message": "Successfully updated"}
#   return run_transaction(sessionmaker, lambda s: callback(s, sport_id, sport))

# @app.delete('/sports/{sport_id}', tags=['Specific Sports Operations'])
# def delete_sport(sport_id: str):
#   def callback(session, sport_id):
#     found = session.query(Sports).filter_by(id=sport_id).delete()
#     if not found:
#       raise HTTPException(status_code=404, detail="Sport not found")
#     return {"message": "Successfully deleted"}
#   return run_transaction(sessionmaker, lambda s: callback(s, sport_id))