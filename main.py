import os
import sys
import logging
from config import Config
from core.wake_word import WakeWordDetector
from core.stt_tts import TTS
from core.search import WebSearcher
from github_service.client import GitHubClient
from github_service.intents import IntentParser

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_intent(intent: dict, github_client: GitHubClient, searcher: WebSearcher, intent_parser: IntentParser) -> str:
    """Executes the action based on the parsed intent and returns a string to speak."""
    action = intent.get("action", "unknown")

    if action == "check_notifications":
        notifs = github_client.get_notifications()
        if not notifs:
            return "You have no unread notifications."
        return f"You have {len(notifs)} unread notifications. The first one is: {notifs[0]['title']}."

    elif action == "check_issues":
        issues = github_client.get_active_issues()
        if not issues:
            return "There are no open issues."
        return f"Found {len(issues)} open issues. The latest one is: {issues[0]['title']}."

    elif action == "check_prs":
        prs = github_client.get_active_prs()
        if not prs:
            return "There are no open pull requests."
        return f"Found {len(prs)} open pull requests. The latest one is: {prs[0]['title']}."

    elif action == "check_actions":
        return github_client.get_latest_action_status()

    elif action == "recent_commits":
        return github_client.get_recent_commits_summary()

    elif action == "append_file":
        file_path = intent.get("file_path", "notes.md")
        content = intent.get("content", "")
        commit_msg = intent.get("commit_message", "Append via Genie")

        if not content:
            return "I couldn't understand what you wanted to append to the file."

        result = github_client.append_to_file(file_path, content, commit_msg)
        return result

    elif action == "web_search":
        query = intent.get("query", "")
        if not query:
            return "I couldn't figure out what you wanted to search for."

        logger.info(f"Executing web search for: {query}")
        results = searcher.search(query, max_results=3)

        logger.info("Summarizing search results...")
        summary = intent_parser.summarize_search_results(query, results)
        return summary

    else:
        return "I didn't understand the command."

def main():
    logger.info("Initializing Genie Assistant...")

    # Validate and load config
    try:
        Config.validate()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Initialize components
    tts = TTS()
    searcher = WebSearcher()

    logger.info("Loading speech recognition model. This might take a few seconds...")
    try:
        wake_detector = WakeWordDetector(Config.VOSK_MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to initialize Wake Word Detector: {e}")
        sys.exit(1)

    logger.info("Initializing GitHub client...")
    try:
        github_client = GitHubClient(Config.GITHUB_TOKEN, Config.GITHUB_REPO)
        if not github_client.verify_main_branch():
             logger.warning("Main branch verification failed. Write operations might fail.")
    except Exception as e:
        logger.error(f"Failed to initialize GitHub Client: {e}")
        sys.exit(1)

    logger.info("Initializing Intent Parser...")
    intent_parser = IntentParser(Config.OPENAI_API_KEY, Config.OPENAI_BASE_URL)

    tts.speak("Genie is online and ready.")

    while True:
        try:
            # 1. Block and listen for wake word
            wake_detector.listen_for_wake_word()
            tts.speak("Yes, master?")

            # 2. Listen for the actual command (short timeout)
            command_text = wake_detector.listen_for_command(timeout_seconds=7)

            if command_text:
                tts.speak("Processing command...")
                logger.info(f"Parsing intent for: {command_text}")

                # 3. Parse the intent using LLM
                intent = intent_parser.parse_intent(command_text)
                logger.info(f"Parsed intent: {intent}")

                # 4. Execute the intent
                response_text = execute_intent(intent, github_client, searcher, intent_parser)

                # 5. Speak the result
                tts.speak(response_text)
            else:
                logger.info("No command heard after wake word.")

        except KeyboardInterrupt:
            logger.info("Shutting down Genie Assistant.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            tts.speak("I encountered an error.")

if __name__ == "__main__":
    main()
