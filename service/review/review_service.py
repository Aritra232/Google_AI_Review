import logging
from typing import Dict, Any, Optional
from service.company.company_service import CompanyService
from service.client.client_service import ClientService
from service.ai.deepseek_service import DeepSeekService

logger = logging.getLogger("review_service")


class ReviewService:
    """Orchestrates company & client lookup from MongoDB and generates AI review request messages."""

    def __init__(
        self,
        company_service: Optional[CompanyService] = None,
        client_service: Optional[ClientService] = None,
        ai_service: Optional[DeepSeekService] = None
    ):
        self.company_service = company_service or CompanyService()
        self.client_service = client_service or ClientService()
        self.ai_service = ai_service or DeepSeekService()

    def _build_prompt(
        self,
        company: Dict[str, Any],
        client: Dict[str, Any],
        service_name: Optional[str] = None,
        channel: str = "SMS",
        tone: str = "friendly and polite",
        language: str = "English",
        custom_instructions: Optional[str] = None
    ) -> str:
        """Construct the prompt for DeepSeek AI."""
        company_name = company.get("name", "our business")
        company_category = company.get("category", "services")
        review_url = company.get("review_url") or company.get("google_review_url") or company.get("website") or ""

        client_name = client.get("name", "valued client")
        client_channel = channel or client.get("channel") or "SMS"
        effective_service = service_name or f"service from {company_name}"

        prompt_lines = [
            f"Scenario:",
            f"- Customer Name: {client_name}",
            f"- Company Name: {company_name}",
            f"- Business Category: {company_category}",
            f"- Service Provided: {effective_service}",
            f"- Review Link: {review_url if review_url else 'N/A'}",
            f"- Target Communication Channel: {client_channel}",
            f"- Tone: {tone}",
            f"- Language: {language}",
            "",
            "Objective:",
            "The customer recently availed service/products from the company but has NOT left a review yet.",
            "Write a simple, polite, concise, and engaging message requesting them to share their feedback/leave a review.",
            "",
            "Instructions:",
            f"1. Greet {client_name} warmly and mention {company_name}.",
            "2. Thank them for choosing the business.",
            "3. Gently let them know how much their feedback matters to help us improve and support the team.",
            f"4. {'Include the review link (' + review_url + ') directly in the message.' if review_url else 'Politely ask them to reply with their feedback or leave a rating.'}",
            f"5. Keep the length appropriate for {client_channel} (short and to the point, avoiding unnecessary fluff).",
            f"6. Write in {language}."
        ]

        if custom_instructions:
            prompt_lines.append(f"7. Special instructions from business: {custom_instructions}")

        prompt_lines.append("")
        prompt_lines.append("Return ONLY the final message text to be sent to the customer. Do not include quotes, markdown headers, or explanations.")

        return "\n".join(prompt_lines)

    async def generate_review_request(
        self,
        company_id: str,
        client_id: str,
        service_name: Optional[str] = None,
        channel: Optional[str] = None,
        tone: Optional[str] = None,
        language: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        1. Fetch company info by company_id from MongoDB.
        2. Fetch client info by client_id from MongoDB.
        3. Use DeepSeek AI to craft a personalized review request message.
        """
        # Fetch data from MongoDB
        company_info = await self.company_service.get_company_by_id(company_id)
        client_info = await self.client_service.get_client_by_id(client_id)

        target_channel = channel or client_info.get("channel") or "SMS"
        target_tone = tone or "friendly and polite"
        target_lang = language or "English"

        # Build prompt
        prompt = self._build_prompt(
            company=company_info,
            client=client_info,
            service_name=service_name,
            channel=target_channel,
            tone=target_tone,
            language=target_lang,
            custom_instructions=custom_instructions
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional customer experience copywriter. "
                    "Your goal is to write polite, short, and effective review request messages for clients "
                    "who have used a service but have not yet provided a review."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call DeepSeek AI
        ai_response = await self.ai_service.generate_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        return {
            "success": True,
            "generated_message": ai_response.get("content"),
            "company": {
                "id": company_info.get("id"),
                "name": company_info.get("name"),
                "category": company_info.get("category"),
                "review_url": company_info.get("review_url")
            },
            "client": {
                "id": client_info.get("id"),
                "name": client_info.get("name"),
                "phone": client_info.get("phone"),
                "email": client_info.get("email"),
                "channel": target_channel
            },
            "metadata": {
                "ai_model": ai_response.get("model"),
                "tokens_used": ai_response.get("usage", {}).get("total_tokens"),
                "channel": target_channel,
                "tone": target_tone,
                "language": target_lang
            }
        }
