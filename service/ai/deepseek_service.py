import os
import logging
from typing import Dict, Any, List, Optional
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("deepseek_service")


class DeepSeekService:
    """Service to interact with DeepSeek AI Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = timeout

    def _validate_config(self):
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="DEEPSEEK_API_KEY is not configured in environment variables."
            )

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 350
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to DeepSeek API.
        Returns a dict containing 'content', 'model', and 'usage'.
        """
        self._validate_config()

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

            if response.status_code == 401:
                logger.error("DeepSeek authentication error: Invalid API key.")
                raise HTTPException(
                    status_code=401,
                    detail="DeepSeek API Key is invalid or expired."
                )
            elif response.status_code == 429:
                logger.error("DeepSeek rate limit exceeded.")
                raise HTTPException(
                    status_code=429,
                    detail="DeepSeek API rate limit reached or quota exhausted. Please try again later."
                )
            elif response.status_code >= 400:
                logger.error(f"DeepSeek API error {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"DeepSeek API error: {response.text}"
                )

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise HTTPException(
                    status_code=502,
                    detail="DeepSeek API returned an empty response choices list."
                )

            message_content = choices[0].get("message", {}).get("content", "").strip()
            return {
                "content": message_content,
                "model": data.get("model", self.model),
                "usage": data.get("usage", {})
            }

        except httpx.TimeoutException:
            logger.error("Timeout connecting to DeepSeek API.")
            raise HTTPException(
                status_code=504,
                detail="DeepSeek API request timed out."
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error when connecting to DeepSeek API: {exc}")
            raise HTTPException(
                status_code=502,
                detail=f"Network error communicating with DeepSeek API: {str(exc)}"
            )
