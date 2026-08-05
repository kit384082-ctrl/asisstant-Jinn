import json
import logging
from openai import OpenAI
from typing import Dict, Any, List

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
        - "web_search": Perform a web search for general questions or finding information online.
        - "unknown": If the command is not understood.

        If the action is "append_file", you must extract:
        - "file_path": The filename mentioned (e.g., "notes.md", "todo.txt"). Default to "notes.md" if unspecified.
        - "content": The text to append to the file.
        - "commit_message": A short commit message summarizing the change (in English).

        If the action is "web_search", you must extract:
        - "query": The specific query to search for, translated to English if appropriate for better search results, or kept in Russian if it's highly specific to a Russian context.

        Output format example:
        {"action": "append_file", "file_path": "notes.md", "content": "buy milk", "commit_message": "Add milk to notes"}
        OR
        {"action": "web_search", "query": "latest python release version"}
        OR
        {"action": "check_notifications"}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0
            )

            raw_response = response.choices[0].message.content.strip()

            if raw_response.startswith("```json"):
                raw_response = raw_response[7:-3].strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response[3:-3].strip()

            intent = json.loads(raw_response)
            return intent

        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            return {"action": "unknown"}

    def summarize_search_results(self, query: str, search_results: List[Dict]) -> str:
        """
        Uses the LLM to summarize web search results into a concise spoken answer in English.
        """
        if not search_results:
            return "I couldn't find any information on that."

        results_text = ""
        for i, res in enumerate(search_results):
            results_text += f"Result {i+1}:\nTitle: {res['title']}\nSnippet: {res['body']}\n\n"

        prompt = f"""
        The user asked: "{query}"

        Here are the top search results:
        {results_text}

        Please provide a concise, direct, and conversational summary of the answer in English.
        It should be easy to listen to when spoken aloud by a text-to-speech engine.
        Do not include links, markdown formatting, or bullet points. Just natural sentences.
        Keep it under 3-4 sentences.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error summarizing search results: {e}")
            return "I encountered an error while trying to summarize the search results."
