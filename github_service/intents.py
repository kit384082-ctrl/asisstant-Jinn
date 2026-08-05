import json
import logging
from openai import OpenAI
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IntentParser:
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def parse_intent(self, text: str) -> Dict[str, Any]:
        """
        Uses OpenAI API to parse the Russian voice command into a structured JSON intent.
        """
        system_prompt = """
        You are an AI assistant that parses voice commands in Russian intended for a GitHub assistant.
        You must return a raw JSON object and nothing else. No markdown formatting like ```json.

        The possible actions are:
        - "check_notifications": Check github notifications.
        - "check_issues": Check active issues.
        - "check_prs": Check active pull requests.
        - "check_actions": Check CI/CD GitHub Actions status.
        - "recent_commits": Get a summary of recent commits.
        - "append_file": Append dictation to a file on the 'main' branch.
        - "unknown": If the command is not understood.

        If the action is "append_file", you must extract:
        - "file_path": The filename mentioned (e.g., "notes.md", "todo.txt"). Default to "notes.md" if unspecified.
        - "content": The text to append to the file.
        - "commit_message": A short commit message summarizing the change (in English).

        Output format example:
        {"action": "append_file", "file_path": "notes.md", "content": "buy milk", "commit_message": "Add milk to notes"}
        OR
        {"action": "check_notifications"}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # or any other available model, assuming compatibility
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0
            )

            raw_response = response.choices[0].message.content.strip()

            # Remove markdown if the model hallucinated it
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:-3].strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response[3:-3].strip()

            intent = json.loads(raw_response)
            return intent

        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {"action": "unknown"}
