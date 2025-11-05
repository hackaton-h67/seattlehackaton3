"""
LLM Triage Service - Classify service requests using LLM.
"""

from typing import Dict, Any, List, Optional
import orjson
import re
from anthropic import Anthropic

from shared.models.request import ExtractedEntities, Classification
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)

# Import Ollama if available
try:
    from shared.utils.ollama_client import get_ollama_client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("ollama_not_available", message="Install ollama package for local LLM support")

# Import OpenAI if available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


TRIAGE_PROMPT_TEMPLATE = """You are an expert Seattle municipal service classifier. Your task is to accurately categorize citizen service requests.

## Context Retrieved from Databases:
{context}

## User Request:
{user_input}

## Extracted Entities:
- Location: {location}
- Keywords: {keywords}
- Urgency Indicators: {urgency_flags}
- Severity: {severity}

## Available Service Categories:
{service_categories}

## Instructions:
1. Analyze the user's request carefully
2. Consider the location context (some services are area-specific)
3. Match to the MOST SPECIFIC service category that applies
4. If multiple services could apply, choose based on:
   - Primary issue mentioned first
   - Severity/safety implications
   - Historical patterns in the area

## Output Format (JSON):
Return ONLY a JSON object with this exact structure:
{{
    "service_code": "EXACT_CODE_FROM_LIST",
    "service_name": "Human readable name",
    "department": "Department acronym",
    "confidence": 0.95,
    "reasoning": "2-3 sentences explaining the classification",
    "alternative_services": [
        {{
            "service_code": "ALTERNATIVE_CODE",
            "confidence": 0.20,
            "why_not_chosen": "Brief explanation"
        }}
    ]
}}"""


# Common Seattle service types (subset for MVP)
SERVICE_CATEGORIES = {
    "SDOT_POTHOLE": {
        "name": "Pothole Repair",
        "department": "SDOT",
        "keywords": ["pothole", "hole", "road damage", "street damage", "pavement"]
    },
    "SDOT_STREETLIGHT": {
        "name": "Street Light Out",
        "department": "SDOT",
        "keywords": ["streetlight", "street light", "light out", "dark", "lighting"]
    },
    "SDOT_SIGN": {
        "name": "Traffic Sign Repair",
        "department": "SDOT",
        "keywords": ["sign", "stop sign", "street sign", "missing sign"]
    },
    "SDOT_SIGNAL": {
        "name": "Traffic Signal Issue",
        "department": "SDOT",
        "keywords": ["traffic light", "signal", "stoplight", "traffic control"]
    },
    "SPU_GRAFFITI": {
        "name": "Graffiti Removal",
        "department": "SPU",
        "keywords": ["graffiti", "vandalism", "spray paint", "tagging"]
    },
    "SPU_DUMPING": {
        "name": "Illegal Dumping",
        "department": "SPU",
        "keywords": ["dumping", "trash", "garbage", "waste", "litter"]
    },
    "SPU_TREE": {
        "name": "Tree Maintenance",
        "department": "SPU",
        "keywords": ["tree", "branches", "fallen tree", "trimming"]
    },
    "PARKING_ABANDONED": {
        "name": "Abandoned Vehicle",
        "department": "PARKING",
        "keywords": ["abandoned vehicle", "abandoned car", "parked car"]
    },
    "PARKING_VIOLATION": {
        "name": "Parking Enforcement",
        "department": "PARKING",
        "keywords": ["parking", "parked", "blocking", "illegal parking"]
    },
    "NOISE_COMPLAINT": {
        "name": "Noise Complaint",
        "department": "POLICE",
        "keywords": ["noise", "loud", "party", "music", "disturbance"]
    },
}


class LLMTriageService:
    """LLM-powered service classification."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.client = None
        self.ollama_client = None
        self.openai_client = None

        if settings.mock_llm:
            logger.warning("using_mock_llm_triage")
            return

        # Initialize based on provider
        if self.provider == "claude" or self.provider == "anthropic":
            if settings.anthropic_api_key:
                self.client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("llm_triage_initialized", provider="claude", model=settings.claude_model)
            else:
                logger.warning("anthropic_api_key_missing")

        elif self.provider == "openai":
            if settings.openai_api_key and OPENAI_AVAILABLE:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("llm_triage_initialized", provider="openai", model=settings.openai_model)
            else:
                logger.warning("openai_api_key_missing_or_not_installed")

        elif self.provider == "ollama":
            if OLLAMA_AVAILABLE:
                self.ollama_client = get_ollama_client()
                if self.ollama_client.is_available():
                    logger.info("llm_triage_initialized", provider="ollama", model=settings.ollama_model)
                else:
                    logger.warning("ollama_not_running", message="Start Ollama with: ollama serve")
            else:
                logger.warning("ollama_package_not_installed")

        else:
            logger.warning("unknown_llm_provider", provider=self.provider)

        if not any([self.client, self.openai_client, self.ollama_client]):
            logger.warning("no_llm_available_using_fallback")

    async def classify(
        self,
        user_input: str,
        entities: ExtractedEntities,
        context: str = ""
    ) -> Classification:
        """
        Classify a service request.

        Args:
            user_input: Original user text
            entities: Extracted entities
            context: Retrieved context from GraphRAG (optional)

        Returns:
            Classification with service code and reasoning
        """
        if settings.mock_llm or not any([self.client, self.openai_client, self.ollama_client]):
            return self._fallback_classification(user_input, entities)

        try:
            # Format the prompt
            prompt = self._format_prompt(user_input, entities, context)

            # Call appropriate LLM provider
            if self.provider in ["claude", "anthropic"] and self.client:
                content = await self._call_claude(prompt)
            elif self.provider == "openai" and self.openai_client:
                content = await self._call_openai(prompt)
            elif self.provider == "ollama" and self.ollama_client:
                content = await self._call_ollama(prompt)
            else:
                return self._fallback_classification(user_input, entities)

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = orjson.loads(json_match.group())
            else:
                result = orjson.loads(content)

            classification = Classification(
                service_code=result["service_code"],
                service_name=result["service_name"],
                department=result["department"],
                confidence_score=result["confidence"],
                alternative_classifications=result.get("alternative_services", [])
            )

            logger.info(
                "classification_complete",
                service_code=classification.service_code,
                confidence=classification.confidence_score,
                alternatives=len(classification.alternative_classifications)
            )

            return classification

        except Exception as e:
            logger.error("llm_classification_failed", error=str(e))
            # Fallback to rule-based classification
            return self._fallback_classification(user_input, entities)

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = await self.openai_client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama local LLM."""
        return await self.ollama_client.generate(
            prompt=prompt,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

    def _format_prompt(
        self,
        user_input: str,
        entities: ExtractedEntities,
        context: str
    ) -> str:
        """Format the classification prompt."""
        location_str = entities.location.address if entities.location else "Not specified"
        keywords_str = ", ".join(entities.service_keywords) if entities.service_keywords else "None"
        urgency_str = ", ".join(entities.urgency_indicators) if entities.urgency_indicators else "None"
        severity_str = entities.damage_severity or "Not specified"

        # Format service categories for prompt
        categories_str = "\n".join([
            f"- {code}: {info['name']} ({info['department']}) - Keywords: {', '.join(info['keywords'][:3])}"
            for code, info in SERVICE_CATEGORIES.items()
        ])

        return TRIAGE_PROMPT_TEMPLATE.format(
            context=context or "No additional context available",
            user_input=user_input,
            location=location_str,
            keywords=keywords_str,
            urgency_flags=urgency_str,
            severity=severity_str,
            service_categories=categories_str
        )

    def _mock_classification(
        self,
        user_input: str,
        entities: ExtractedEntities
    ) -> Classification:
        """Mock classification for testing."""
        return Classification(
            service_code="SDOT_POTHOLE",
            service_name="Pothole Repair",
            department="SDOT",
            confidence_score=0.85,
            alternative_classifications=[]
        )

    def _fallback_classification(
        self,
        user_input: str,
        entities: ExtractedEntities
    ) -> Classification:
        """Simple keyword-based classification as fallback."""
        text_lower = user_input.lower()

        # Score each service category
        scores = {}
        for code, info in SERVICE_CATEGORIES.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword in text_lower:
                    score += 1

            # Bonus for entity keywords match
            for entity_keyword in entities.service_keywords:
                if entity_keyword in info["keywords"]:
                    score += 2

            if score > 0:
                scores[code] = score

        if not scores:
            # Default to generic request
            return Classification(
                service_code="GENERAL_REQUEST",
                service_name="General Service Request",
                department="CUSTOMER_SERVICE",
                confidence_score=0.5,
                alternative_classifications=[]
            )

        # Get top match
        best_match = max(scores.items(), key=lambda x: x[1])
        code = best_match[0]
        info = SERVICE_CATEGORIES[code]

        # Calculate confidence (normalize score)
        max_score = len(info["keywords"]) + len(entities.service_keywords) * 2
        confidence = min(0.95, (best_match[1] / max_score) * 0.9 + 0.3)

        # Get alternatives
        alternatives = []
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:3]
        for alt_code, alt_score in sorted_scores:
            alt_info = SERVICE_CATEGORIES[alt_code]
            alt_confidence = min(0.8, (alt_score / max_score) * 0.7 + 0.1)
            alternatives.append({
                "service_code": alt_code,
                "confidence": alt_confidence,
                "why_not_chosen": f"Lower keyword match ({alt_score} vs {best_match[1]})"
            })

        return Classification(
            service_code=code,
            service_name=info["name"],
            department=info["department"],
            confidence_score=confidence,
            alternative_classifications=alternatives
        )


if __name__ == "__main__":
    import asyncio

    async def test():
        triage = LLMTriageService()

        from shared.models.request import ExtractedEntities

        test_cases = [
            ("There's a pothole on 5th Avenue", ["pothole", "road"]),
            ("Graffiti on the building wall", ["graffiti"]),
            ("Street light is out at my corner", ["streetlight", "light"]),
        ]

        for text, keywords in test_cases:
            entities = ExtractedEntities(service_keywords=keywords)
            result = await triage.classify(text, entities)
            print(f"\nInput: {text}")
            print(f"Service: {result.service_name} ({result.service_code})")
            print(f"Department: {result.department}")
            print(f"Confidence: {result.confidence_score:.2f}")

    asyncio.run(test())
