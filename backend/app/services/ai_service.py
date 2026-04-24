import json
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from app.config import settings
import structlog

logger = structlog.get_logger()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


SYSTEM_PROMPTS = {
    "en": """You are an expert AI programming tutor. You help students learn programming 
    by explaining concepts clearly, debugging code, and suggesting optimizations. 
    Always be encouraging and educational in your responses.""",

    "hinglish": """Aap ek expert AI programming tutor hain. Aap students ko programming 
    sikhne mein help karte hain concepts clearly explain karke, code debug karke, 
    aur optimizations suggest karke. Apne responses mein Hindi aur English ka mix use karein 
    (Hinglish) aur hamesha encouraging aur educational rehein. 
    Example: "Yeh code mein ek common mistake hai..." ya "Chaliye is problem ko solve karte hain..." """,
}


async def get_ai_response(
    messages: List[Dict[str, str]],
    system_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    custom_api_key: str = None,
) -> str:
    """Get a response from the AI model."""
    if not client and not custom_api_key:
        return "AI service not configured. Please add an OpenAI API key."

    api_client = AsyncOpenAI(api_key=custom_api_key) if custom_api_key else client

    try:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = await api_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("AI service error", error=str(e))
        return f"Error communicating with AI service: {str(e)}"


async def explain_code_error(
    code: str,
    language: str,
    error_message: str,
    response_language: str = "en",
) -> Dict[str, Any]:
    """Provide AI-based error explanation with line-by-line debugging."""
    system_prompt = SYSTEM_PROMPTS.get(response_language, SYSTEM_PROMPTS["en"])

    prompt = f"""Analyze this {language} code that has an error and provide:
1. A clear explanation of what went wrong
2. Line-by-line analysis of the problematic code
3. Specific fixes for each issue
4. An optimized version of the code
5. Best practices suggestions

Code:
```{language}
{code}
```

Error:
```
{error_message}
```

Respond in JSON format:
{{
  "explanation": "Overall explanation of the error",
  "line_fixes": [
    {{
      "line_number": 5,
      "issue": "Description of issue on this line",
      "fix": "How to fix it",
      "fixed_code": "corrected line of code"
    }}
  ],
  "optimized_code": "Complete optimized version of the code",
  "suggestions": ["suggestion 1", "suggestion 2"]
}}"""

    try:
        response = await get_ai_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=0.3,
        )

        # Parse JSON response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except Exception as e:
        logger.error("Error parsing AI debug response", error=str(e))

    return {
        "explanation": f"Error analysis: {error_message}",
        "line_fixes": [],
        "optimized_code": code,
        "suggestions": ["Review your syntax", "Check variable names", "Verify logic flow"],
    }


async def generate_code_feedback(
    code: str,
    language: str,
    problem_description: str = None,
    response_language: str = "en",
) -> str:
    """Generate AI feedback on submitted code."""
    system_prompt = SYSTEM_PROMPTS.get(response_language, SYSTEM_PROMPTS["en"])

    context = f"Problem: {problem_description}\n\n" if problem_description else ""
    prompt = f"""{context}Review this {language} code and provide constructive feedback:

```{language}
{code}
```

Focus on:
- Code correctness
- Efficiency and time complexity
- Code style and readability
- Edge cases handling
- Potential improvements"""

    return await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt,
        temperature=0.5,
    )


async def chat_with_tutor(
    messages: List[Dict[str, str]],
    code_context: Optional[str] = None,
    language: Optional[str] = None,
    response_language: str = "en",
) -> str:
    """Chat with the AI tutor."""
    system_prompt = SYSTEM_PROMPTS.get(response_language, SYSTEM_PROMPTS["en"])

    if code_context:
        system_prompt += f"\n\nCurrent code context ({language or 'code'}):\n```\n{code_context}\n```"

    return await get_ai_response(
        messages=messages,
        system_prompt=system_prompt,
        temperature=0.7,
    )


async def suggest_code_fix(
    code: str,
    language: str,
    issue_description: str,
    response_language: str = "en",
) -> Dict[str, Any]:
    """Suggest specific code fixes."""
    system_prompt = SYSTEM_PROMPTS.get(response_language, SYSTEM_PROMPTS["en"])

    prompt = f"""Given this {language} code with the described issue, provide a fix:

Code:
```{language}
{code}
```

Issue: {issue_description}

Provide:
1. The fixed code
2. Explanation of changes made
3. Where exactly to implement the changes

Respond in JSON:
{{
  "fixed_code": "complete fixed code",
  "changes": [
    {{
      "location": "line number or function name",
      "original": "original code snippet",
      "replacement": "fixed code snippet",
      "explanation": "why this change is needed"
    }}
  ],
  "summary": "brief summary of all changes"
}}"""

    try:
        response = await get_ai_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=0.3,
        )
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except Exception as e:
        logger.error("Error parsing fix suggestion", error=str(e))

    return {
        "fixed_code": code,
        "changes": [],
        "summary": "Could not generate specific fixes",
    }
