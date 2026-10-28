# AI Travel Planner 

An AI-powered travel planning application built with **Python, LangChain, LangGraph, FastAPI, Streamlit, and Groq**. It transforms natural-language travel requests into personalized, research-backed itineraries through a multi-agent AI workflow.

Instead of generating a trip plan from a single prompt, the application collects travel requirements, researches the destination, estimates costs using researched price data, and generates a structured itinerary based on the user's preferences and budget.

The application uses **Llama 3.3 70B Versatile through Groq** for AI-powered reasoning and structured output generation, with Tavily, Open-Meteo, and OpenStreetMap providing external travel information.

## Key Features

- **Natural Language Travel Planning:** Describe your trip conversationally, including destinations, duration, budget, travelers, and preferences.
- **Intelligent Requirement Gathering:** Extracts structured travel requirements and asks follow-up questions when essential details are missing.
- **Multi-Agent Architecture:** Separates requirement extraction, destination research, cost estimation, and itinerary planning into specialized agents.
- **Destination Research:** Collects information about attractions, hotels, restaurants, transportation, travel costs, and local tips.
- **Weather and Geolocation:** Retrieves weather information and geographical coordinates for the destination.
- **Budget Estimation:** Calculates estimated hotel, food, transportation, and activity expenses using available research data.
- **Budget Validation:** Compares estimated trip expenses against the user's budget and identifies whether the trip is within budget, over budget, or cannot be determined.
- **Structured AI Outputs:** Uses Pydantic models to validate agent inputs and outputs.
- **Streaming Updates:** Displays agent execution progress in the Streamlit chat interface.
- **Resilient Execution:** Implements retries, backoff, and fallback handling for external API and LLM failures.
- **Dual Interfaces:** Supports an interactive Streamlit application and a FastAPI backend.
- **Session-Based Conversations:** Maintains incomplete travel requests while collecting missing information.

## Architecture

The application follows a multi-agent pipeline in which each agent has a clearly defined responsibility.

```text
                 User Request
                      |
             Streamlit Chat / API
                      |
                      v
             Requirement Agent
                      |
              TravelRequirements
                      |
             Required fields missing?
                 /           \
               Yes            No
                |              |
          Ask Follow-up        |
                |              v
                |       Research Agent
                |              |
                |       +------+------+
                |       |      |      |
                |     Tavily Weather Geocoding
                |       |      |      |
                |       +------+------+
                |              |
                |       ResearchSummary
                |              |
                |              v
                |    Cost Estimation Agent
                |              |
                |       Budget Breakdown
                |              |
                |              v
                |       Planning Agent
                |              |
                |         TravelPlan
                |              |
                +--------> Final Response
```

The workflow is implemented through two execution paths:

- **Conversational path:** `chat_service.py` orchestrates the agents directly, allowing the Streamlit interface to display progress updates and manage follow-up messages.
- **LangGraph path:** The graph in `app/graph/` executes the requirement, research, cost estimation, and planning stages. The `/demo` endpoint invokes this graph.

Both paths use the same core travel-planning workflow, while serving different execution and interaction needs.

## Multi-Agent Workflow

### 1. Requirement Agent

**File:** `app/agents/requirement_agent.py`

Converts a natural-language request into a structured `TravelRequirements` object.

For example, a user might enter:

> Plan a 7-day trip from Delhi to Japan for 2 people with a budget of $3,000. Include Indian food options.

The agent extracts details such as:

- Origin and destination
- Number of days
- Number of travelers
- Budget and currency
- Preferred transportation
- Hotel preferences
- Food preferences
- Additional requirements

The agent uses an LLM with Pydantic structured output to convert conversational text into validated fields.

If essential information is missing, the application asks a follow-up question and combines the user's response with the existing conversation before extracting the requirements again.

Hotel, food, and transportation preferences default to `any`, allowing the workflow to continue without unnecessary questions about optional preferences.

### 2. Research Agent

**File:** `app/agents/research_agent.py`

Researches the destination using external APIs and search tools.

The agent gathers information about:

- Tourist attractions and activities
- Hotels and accommodation options
- Restaurants and local cuisine
- Transportation options
- Estimated travel expenses
- Local travel tips
- The best time to visit

It integrates three external information sources:

| Tool | Purpose |
|---|---|
| Tavily Search API | Searches the web for destination-specific travel information. |
| Open-Meteo API | Retrieves weather information. |
| OpenStreetMap Nominatim | Resolves destination names into geographical coordinates. |

The research results are processed by the LLM and summarized into a structured `ResearchSummary` object for downstream agents.

The application supports parallel searches in `travel_search()` and sequential searches in the streaming execution path.

If Tavily is unavailable, the application can continue with limited research. Weather, geocoding, and LLM failures are handled using the implemented retry and fallback mechanisms.

### 3. Cost Estimation Agent

**Purpose:** Calculate the estimated trip budget from researched information.

This agent converts available price ranges into a practical budget breakdown rather than leaving all cost calculations to the itinerary-generation LLM.

It estimates expenses across categories such as:

- Accommodation
- Food
- Transportation
- Activities and attractions

The estimator averages available researched price ranges and calculates accommodation requirements based on traveler count. For shared rooms, the room estimate uses `ceil(travelers / 2)`; hostel accommodation can use an individual-bed assumption.

The agent then calculates the estimated total and compares it with the user's budget.

Possible budget statuses:

- **Within budget:** Estimated costs fit the available budget.
- **Over budget:** Estimated costs exceed the available budget.
- **Cannot determine:** The available price information is insufficient for a reliable comparison.

The resulting breakdown and budget status are passed to the Planning Agent.

Missing or unreliable price information should remain explicitly unavailable rather than being presented as a verified market price.

### 4. Planning Agent

**File:** `app/agents/planning_agent.py`

Generates the final travel itinerary using the collected requirements, destination research, weather information, and cost estimation results.

The output includes:

- Day-by-day itinerary
- Recommended hotels
- Restaurant suggestions
- Transportation guidance
- Activity recommendations
- Weather notes
- Budget breakdown and status
- Practical travel tips

The agent uses the `TravelPlan` Pydantic schema to produce a structured result that can be formatted into a readable Markdown response.

Its prompting instructions emphasize grounding recommendations in the available research, preserving the cost estimator's figures, and avoiding invented places or prices. When reliable cost data is unavailable, the output should explicitly indicate that it is not available.

## LLM Integration and Prompting Strategy

The application uses **Groq-hosted Llama 3.3 70B Versatile** as its primary language model.

Rather than relying on one large prompt to perform every task, the application divides the work into specialized agent prompts.

Each agent receives the information relevant to its responsibility:

| Agent | LLM responsibility |
|---|---|
| Requirement Agent | Extract and normalize travel requirements into structured fields. |
| Research Agent | Summarize external search results into usable destination research. |
| Cost Estimation Agent | Interpret available price information and calculate budget estimates. |
| Planning Agent | Generate the final itinerary using the requirements, research, and estimated budget. |

Pydantic models define the expected structures, helping the application validate the data passed between agents.

This design makes the workflow easier to maintain, test, and extend. For example, the cost estimator can be improved independently without rewriting the requirement extraction or itinerary-generation logic.

The application also separates the **LLM's reasoning and language-generation responsibilities** from external data retrieval and deterministic calculations. The LLM does not replace the search APIs or the budget arithmetic; each has a separate role.

## Technology Stack

| Technology | Usage |
|---|---|
| Python | Core application and agent logic |
| LangChain | LLM integration and structured output workflows |
| LangGraph | Graph-based orchestration of agent stages |
| FastAPI | REST API and streaming endpoints |
| Streamlit | Interactive conversational interface |
| Groq | Hosted LLM inference |
| Llama 3.3 70B Versatile | Primary language model |
| Pydantic | Input validation and structured agent outputs |
| Tavily Search API | Web-based destination research |
| Open-Meteo | Weather information |
| OpenStreetMap Nominatim | Geocoding and location lookup |
| Uvicorn | ASGI server for FastAPI |

## Project Structure

The primary modules are organized by responsibility. The exact directory layout may vary slightly as the project evolves.

```text
Travel-Agent-GenAi/
│
├── app/
│   ├── agents/
│   │   ├── requirement_agent.py
│   │   ├── research_agent.py
│   │   └── planning_agent.py
│   │
│   ├── graph/
│   │   └── ...                 # LangGraph workflow
│   │
│   ├── models/
│   │   ├── travel_models.py
│   │   ├── research_summary.py
│   │   ├── travel_plan.py
│   │   └── chat_models.py
│   │
│   └── tools/
│       ├── tavily_tool.py
│       ├── geocoding_tool.py
│       └── weather_tool.py
│
├── chat_service.py             # Conversational orchestration
├── main.py                     # FastAPI application
├── streamlit_app.py            # Streamlit chat interface
├── requirement.txt             # Python dependencies
├── .env                        # API keys (not committed)
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10 or a compatible version supported by your dependencies
- A Groq API key
- A Tavily API key for web research

### 1. Clone the repository

```bash
git clone <repository-url>
cd Travel-Agent-GenAi
```

### 2. Create and activate a virtual environment

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirement.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root, alongside `main.py`.

```dotenv
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

Obtain API keys from:

- Groq: https://console.groq.com
- Tavily: https://tavily.com

| Variable | Required? | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Yes | Powers the LLM-based agents. |
| `TAVILY_API_KEY` | Strongly recommended | Enables web-based destination research. |

**Important:** Never commit your `.env` file or expose API keys in source code. Add `.env` and your virtual environment directory to `.gitignore`.

### 5. Run the Streamlit application

```bash
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit, typically:

http://localhost:8501

The interface allows users to enter trip requests, answer follow-up questions, and observe agent execution status as the itinerary is generated.

### 6. Run the FastAPI application

In a separate terminal, activate the virtual environment and run:

```bash
uvicorn main:app --reload
```

The API is typically available at:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

## API Endpoints

The FastAPI application exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root endpoint. |
| `GET` | `/demo` | Runs the graph-based travel-planning workflow. |
| `POST` | `/chat` | Handles conversational travel-planning requests. |
| `POST` | `/chat/stream` | Streams chat and agent progress events. |
| `DELETE` | `/chat/{session_id}` | Deletes the specified in-memory chat session. |

See the interactive API documentation at `/docs` for the request and response schemas.

## Example Usage

Enter a natural-language request in the Streamlit chat:

```text
Plan a 7-day trip from Delhi to Japan
for 2 people with a budget of 3000 USD.
Include Indian food options and affordable hotels.
```

The application follows this sequence:

1. Extracts the destination, origin, duration, travelers, budget, and preferences.
2. Asks follow-up questions if required trip information is missing.
3. Researches attractions, hotels, restaurants, transportation, weather, and local travel costs.
4. Estimates accommodation, food, transport, and activity expenses from available research.
5. Checks the estimated total against the user's budget.
6. Generates a day-by-day itinerary and a budget summary.

The final response is formatted in Markdown for readability.

Actual recommendations and cost estimates depend on the available research results and external API responses.

## Reliability and Error Handling

The application includes resilience mechanisms to reduce the impact of transient failures:

- Retries with backoff for supported external API and LLM calls.
- Fallback behavior for research, weather, and model failures.
- Graceful degradation when the Tavily API key is unavailable.
- Structured validation through Pydantic schemas.
- Explicit handling of missing cost information.
- In-memory session management for conversational follow-ups.

These mechanisms help the application return a useful response when possible, although fallback results may contain less information than a successful research run.

## Current Limitations

- **Session persistence:** Conversations are stored in process memory and are lost when the application restarts.
- **Research coverage:** Recommendations depend on search results and external service availability.
- **Price accuracy:** Estimated expenses are based on available research and should not be treated as live booking quotes.
- **Booking integrations:** The application generates recommendations but does not currently complete flight or hotel bookings.
- **Authentication:** Persistent user accounts and authentication are not part of the described implementation.
- **Live data:** Weather and travel information availability depends on the connected APIs.
- **Streaming and graph execution:** Conversational streaming is orchestrated through `chat_service.py`, while `/demo` exercises the LangGraph implementation.

## Future Enhancements

Potential next steps include:

- Flight search and booking API integration.
- Hotel availability and reservation integrations.
- Persistent sessions using a database or Redis.
- Interactive maps and route visualization.
- PDF itinerary export.
- Currency conversion and more detailed budget handling.
- User authentication and saved trips.
- Automated testing and agent-level evaluation.
- Improved research source attribution and price freshness.
- A unified LangGraph execution path with streaming support.

## License

This project is intended for learning, experimentation, and educational purposes. Add an explicit open-source license if you intend to distribute or reuse it under specific terms.
