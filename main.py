from fastapi import FastAPI

from app.graph.workflow import graph

app = FastAPI()


@app.get("/")
def run_graph():

    initial_state = {
          "user_query": (
        "Plan a 7 day trip from Delhi to Japan "
        "for 2 people with a budget of 3000 dollars. travel style is anime"
    ),
        "requirements": {},
        "missing_fields": [],
        "research_data": {},
        "travel_plan": {},
        "final_response": "",
    }

    result = graph.invoke(initial_state)

    return result