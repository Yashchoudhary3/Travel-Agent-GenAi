# AI Travel Planner

An AI-powered travel planning application built with LangGraph, LangChain, FastAPI, and Groq.

The application understands natural language travel requests, gathers real-time travel information, and generates personalized travel itineraries using a multi-agent workflow.

## Features

- Natural language travel planning
- Multi-agent workflow
- Travel requirement extraction
- Destination research
- Live weather information
- Geolocation lookup
- Personalized itinerary generation
- Hotel recommendations
- Restaurant recommendations
- Transportation suggestions
- Budget estimation
- Structured AI responses

## Tech Stack

- Python
- FastAPI
- LangGraph
- LangChain
- Groq LLM
- Tavily Search API
- Open-Meteo API
- OpenStreetMap (Nominatim)
- Pydantic

## Project Structure

```
app/
├── agents/
├── graph/
├── models/
├── tools/
├── config/
└── main.py
```

## Workflow

```
User Request
      │
      ▼
Requirement Extraction
      │
      ▼
Destination Research
      │
      ├── Web Search
      ├── Weather
      └── Geolocation
      │
      ▼
Travel Planning
      │
      ▼
Final Itinerary
```

## Installation

```bash
git clone <repository-url>

cd <project-folder>

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

## Future Enhancements

- Flight integration
- Hotel booking integration
- PDF itinerary export
- Interactive travel assistant
- Maps integration
- User authentication
- Saved trips
- Expense tracking

## License

This project is intended for learning and educational purposes.
