from groq import AsyncGroq
from app.config import settings
from typing import Any
import json

client = AsyncGroq(api_key=settings.groq_api_key)


async def review_diff(diff: str) -> dict[str, Any]:
    prompt = f"""You are a senior software engineer reviewing a pull request.
Analyze the following code diff and identify:
1. Security vulnerabilities
2. Code quality issues
3. Missing error handling
4. Performance concerns
5. Suggested fixes

Be specific, mention line context where possible.
Respond in JSON format with a key "issues" containing a list of strings.

Diff:
{diff}
"""
    response = await client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    content = response.choices[0].message.content
    return json.loads(content)
