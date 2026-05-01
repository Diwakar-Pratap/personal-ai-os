"""
memory/importance.py - Uses LLM to decide what to remember.
Avoids cluttering memory with trivial chat (e.g. "hi", "ok").
"""
import re
from llm.openai_client import chat_completion

async def evaluate_importance(text: str) -> int:
    """
    Asks the LLM to rate the importance of a statement from 1-10.
    1 = Trivial/Small talk
    10 = Critical personal fact/Preference/Instruction
    """
    prompt = f"""
    You are a memory filter for a Personal AI OS.
    Rate how important it is to remember the following information about the user on a scale of 1 to 10.
    
    CRITERIA:
    - 1-3: Small talk, greetings, passing comments (e.g. "I'm bored", "hello").
    - 4-6: General facts that might be useful later (e.g. "I like pizza", "I am working on a React project").
    - 7-10: Critical personal info, deep preferences, or specific instructions (e.g. "My birthday is June 5th", "I prefer Python over Java", "Always format code in dark mode").
    
    TEXT: "{text}"
    
    Return ONLY a single number between 1 and 10.
    """
    
    response = await chat_completion([{"role": "system", "content": prompt}])
    
    # Extract number from response
    match = re.search(r'\d+', response)
    if match:
        score = int(match.group())
        return min(max(score, 1), 10)
    return 1

async def extract_memories(user_msg: str, ai_msg: str) -> list[str]:
    """
    Asks the LLM to extract specific facts worth remembering from an exchange.
    Returns a list of clean fact strings.
    """
    prompt = f"""
    Analyze the following conversation and extract any new personal facts, preferences, or important details about the USER that should be remembered for the long term.
    
    USER: {user_msg}
    AI: {ai_msg}
    
    Format each fact as a simple, standalone 3rd-person statement starting with "The user...".
    If no important facts are found, return "NONE".
    
    Example Output:
    - The user's favorite language is Python.
    - The user lives in New York.
    """
    
    response = await chat_completion([{"role": "system", "content": prompt}])
    
    if "NONE" in response.upper():
        return []
        
    facts = [f.strip("- ").strip() for f in response.split("\n") if f.strip() and "The user" in f]
    return facts
