import json
import logging
import os
import re

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


async def generate_matches_with_ai(user_profile: dict) -> dict:
    try:
        skills = user_profile.get("skills", [])
        proficiency = user_profile.get("proficiency", {})

        skills_text = ", ".join([f"{s} ({proficiency.get(s, 'beginner')})" for s in skills])

        prompt = f"""You are an AI system powering a Skill Partner Finder app. A user wants to learn or improve these skills: {skills_text}.

Generate a JSON response with:
1. 3-5 ideal learning partners (fictional profiles with complementary skills)
2. 2-3 mini-challenges related to their skills
3. 2-3 social hooks or achievement ideas

Format:
{{
  "matches": [
    {{
      "partner_name": "Name",
      "complementary_skills": ["skill1", "skill2"],
      "compatibility": "High/Medium/Low",
      "collaboration_idea": "Short actionable plan",
      "conversation_starters": ["Starter1", "Starter2"]
    }}
  ],
  "mini_challenges": ["Challenge 1", "Challenge 2"],
  "social_hooks": ["Achievement to share", "Invite friends prompt"]
}}

Only return valid JSON, nothing else."""

        chat = LlmChat(
            api_key=os.environ.get("EMERGENT_LLM_KEY"),
            session_id=f"match_{user_profile.get('id', 'default')}",
            system_message="You are a helpful AI assistant that generates skill matching data. Respond with raw JSON only, no markdown code fences or additional text."
        ).with_model("openai", "gpt-4o")

        response = await chat.send_message(UserMessage(text=prompt))
        cleaned_response = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip(), flags=re.MULTILINE).strip()

        if not cleaned_response.startswith('{'):
            start = cleaned_response.find('{')
            end = cleaned_response.rfind('}')
            if start != -1 and end != -1:
                cleaned_response = cleaned_response[start:end + 1]

        result = json.loads(cleaned_response)
        if not result.get("matches") or len(result["matches"]) == 0:
            raise ValueError("Empty matches from AI")

        return result
    except Exception as e:
        logger.error(f"AI matchmaking error: {e}")
        return {
            "matches": [],
            "mini_challenges": ["Add more skills to get better matches", "Try refreshing your profile"],
            "social_hooks": ["Share your profile", "Invite a friend"],
            "error": True,
            "error_message": "Failed to generate AI matches. Please try again."
        }
