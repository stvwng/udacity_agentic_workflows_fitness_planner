import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class FitnessUser:
    """Represents a fitness app user."""
    def __init__(self, id: str, age: int, fitness_level: int, 
                 goals: List[str], preferences: List[str], 
                 limitations: List[str] = None):
        self.id = id
        self.age = age
        self.fitness_level = fitness_level
        self.goals = goals
        self.preferences = preferences
        self.limitations = limitations or []

    def __str__(self):
        return f"User {self.id}: Level {self.fitness_level}, Goals: {', '.join(self.goals)}"

def deterministic_agent(user: FitnessUser) -> Dict:
    """Agent that creates a workout plan using deterministic rules."""
    plan = {
        "workout_days": 3,
        "session_duration": 30,
        "workout_types": [],
        "intensity": "moderate"
    }
    
    if user.fitness_level >= 4:
        plan["workout_days"] = 5
    elif user.fitness_level >= 2:
        plan["workout_days"] = 4
    
    if user.fitness_level >= 3:
        plan["session_duration"] = 45
    
    if user.fitness_level <= 2:
        plan["intensity"] = "low"
    elif user.fitness_level >= 4:
        plan["intensity"] = "high"
    
    if "weight management" in user.goals:
        plan["workout_types"].append("cardio")
    if "strength building" in user.goals:
        plan["workout_types"].append("strength training")
    if "flexibility" in user.goals:
        plan["workout_types"].append("stretching")
    if "endurance" in user.goals:
        plan["workout_types"].append("interval training")
    
    if not plan["workout_types"]:
        plan["workout_types"] = ["general fitness", "light cardio"]
    
    plan["weekly_schedule"] = {}
    days = ["Monday", "Wednesday", "Friday", "Tuesday", "Thursday", "Saturday"]
    
    for i in range(plan["workout_days"]):
        workout_type = plan["workout_types"][i % len(plan["workout_types"])]
        plan["weekly_schedule"][days[i]] = {
            "type": workout_type,
            "duration": plan["session_duration"],
            "intensity": plan["intensity"],
            "description": f"{plan['intensity'].capitalize()} {workout_type} session"
        }
    
    return plan


# ======== AGENT 2 — LLM-Based Planner ========

def llm_agent(user: FitnessUser) -> Dict:
    goals_text = ", ".join(user.goals)
    preferences_text = ", ".join(user.preferences)
    limitations_text = ", ".join(user.limitations) if user.limitations else "None"

    prompt = f"""
    Create a personalized weekly workout plan for this client.

    Client Information:
    - Age: {user.age}
    - Fitness Level: {user.fitness_level}/5
    - Goals: {goals_text}
    - Preferences: {preferences_text}
    - Limitations: {limitations_text}

    The plan should focus on achieving the client's goals and take into account the client's preferences and limitations.
    
    The plan should be returned in a JSON of the following form:
    
    {{
        "reasoning": [your reasoning for the plan],
        "weekly_schedule":
            {{
                [day of week]:
                    {{
                        [workout object]
                    }}
                ...
                [day of week]: ...
            }}
    }}
    
    A workout object is a JSON in the following format:
    {{
        "type": [type of workout],
        "intensity": [intensity of workout],
        "duration": [duration of workout in minutes],
        "description": [description of workout]    
    }}
    
    Return only a JSON.
    
    EXAMPLE OUTPUT:
    
{{
    "reasoning": "The client wants to improve his health generally. He has never used a personal trainer before and has limited time each day to devote to training."
    "weekly_schedule": {{
        "Monday": {{"type": "Strength Training (Upper Body)", "duration": 45, "intensity": "Moderate", "description": "Focus on chest, shoulders, triceps."}},
        "Tuesday": {{"type": "Cardio (Running)", "duration": 30, "intensity": "Moderate", "description": "Maintain a steady pace."}},
        "Wednesday": {{"type": "Rest", "duration": 1440, "intensity": "Low", "description": "Recovery day."}},
        "Thursday": {{"type": "Strength Training (Lower Body)", "duration": 45, "intensity": "Moderate", "description": "Focus on quads, hamstrings, glutes."}},
        "Friday": {{"type": "Flexibility (Yoga)", "duration": 30, "intensity": "Low", "description": "Full body stretching and relaxation."}},
        "Saturday": {{"type": "Rest", "duration": 1440, "intensity": "Low", "description": "Recovery day."}},
        "Sunday": {{"type": "Active Recovery (Walking)", "duration": 45, "intensity": "Low", "description": "Enjoy a brisk walk."}}
    }}
}}
    
    """

    try:
        response = client.responses.create(
            model="gpt-4.1",
            instructions="You are a certified fitness trainer",
            input=prompt,
            temperature=0.2,
        )
        result_text = response.output_text
        return json.loads(result_text)

    except Exception as e:
        fallback = deterministic_agent(user)
        return {
            "reasoning": f"LLM planning failed: {str(e)}",
            "weekly_schedule": fallback["weekly_schedule"],
            "considerations": "Fallback to rule-based plan."
        }

def show_responses(users: List[FitnessUser]):
    for user in users:
        plan = llm_agent(user)
        print(plan)

# ======== COMPARISON LOGIC (DO NOT EDIT) ========

def compare_workout_planning(users: List[FitnessUser]):
    print("\n===== WORKOUT PLAN COMPARISON =====")
    for i, user in enumerate(users, 1):
        print(f"\n--- User {i}: {user.id} ---")
        print(f"Age: {user.age} | Fitness Level: {user.fitness_level}/5")
        print(f"Goals: {', '.join(user.goals)}")
        print(f"Preferences: {', '.join(user.preferences)}")
        print(f"Limitations: {', '.join(user.limitations)}")

        det_plan = deterministic_agent(user)
        print("\n[Deterministic Agent]")
        for day, workout in det_plan["weekly_schedule"].items():
            print(f"- {day}: {workout['type']} ({workout['intensity']}, {workout['duration']} min)")

        llm_plan = llm_agent(user)
        print("\n[LLM Agent]")
        print(f"Reasoning: {llm_plan.get('reasoning', 'No reasoning provided')}")
        for day, workout in llm_plan["weekly_schedule"].items():
            print(f"- {day}: {workout['type']} ({workout['intensity']}, {workout['duration']} min)")
            print(f"  {workout['description']}")
        print(f"Considerations: {llm_plan.get('considerations', 'None')}")


# ======== SAMPLE USERS ========

def main():
    users = [
        FitnessUser(
            id="U001",
            age=35,
            fitness_level=2,
            goals=["weight management", "stress reduction"],
            preferences=["home workouts", "morning routines"],
            limitations=["limited equipment", "time constraints (max 30 min/day)"]
        ),
        FitnessUser(
            id="U002",
            age=55,
            fitness_level=3,
            goals=["joint mobility", "strength building"],
            preferences=["outdoor activities", "swimming"],
            limitations=["mild joint stiffness"]
        )
    ]

    compare_workout_planning(users)
    # show_responses(users)

if __name__ == "__main__":
    main()
