from __future__ import annotations

import base64
import json
import logging
from typing import Dict, List

from openai import OpenAI

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def analyze_image(self, image_data: bytes) -> Dict[str, List[str] | str]:
        logger.info("Starting AI analysis using model %s", self.settings.openai_model)
        
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data))
            mime_type = f"image/{img.format.lower()}" if img.format else "image/jpeg"
        except Exception:
            mime_type = "image/jpeg"
        
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        image_url = f"data:{mime_type};base64,{encoded_image}"

        prompt = (
            "You are assisting with an AI-powered photo gallery. "
            "Describe the image in one concise, vivid sentence (max 35 words). "
            "Return 5-10 short keyword tags (single or double words) describing the most important concepts. "
            "Respond ONLY with valid JSON (no markdown, no code blocks, no explanations). "
            "Required JSON format: {\"description\": \"...\", \"tags\": [\"tag1\", \"tag2\", ...]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a world-class visual analyst. Respond ONLY with valid JSON. Do not use markdown code blocks."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
            )
        except Exception as e:
            logger.error("OpenAI API call failed: %s", e)
            raise RuntimeError(f"Failed to analyze image with OpenAI: {e}") from e

        response_text = response.choices[0].message.content or ""

        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()
        
        try:
            parsed = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI JSON response: %s. Response was: %s", exc, response_text[:200])
            raise RuntimeError(f"AI returned invalid JSON: {exc}") from exc

        tags = [tag.strip() for tag in parsed.get("tags", []) if isinstance(tag, str)]
        description = parsed.get("description", "")

        if not tags:
            logger.warning("AI response returned no tags; falling back to empty list")
        if not description:
            logger.warning("AI response returned no description")

        return {
            "tags": tags[: self.settings.max_tags],
            "description": description,
        }


ai_service = AIService()
