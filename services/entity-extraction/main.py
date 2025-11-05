"""
Entity Extraction Service - Extract structured entities from natural language.
"""

from typing import Optional
import re
from anthropic import Anthropic
import orjson

from shared.models.request import ExtractedEntities, Location
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


EXTRACTION_PROMPT = """Extract the following entities from the user's service request.

User Input: {user_input}

Return a JSON object with:
- location: street address, intersection, or landmark (if mentioned)
- location_type: "address" | "intersection" | "landmark" | "area" | null
- service_keywords: list of relevant service-related terms (e.g., "pothole", "graffiti", "streetlight")
- urgency_indicators: list of urgent/safety keywords (e.g., "dangerous", "emergency", "injured")
- temporal_context: any time references (e.g., "since last week", "this morning", "ongoing")
- affected_count: estimated number of people affected (as integer) or null
- damage_severity: "minor" | "moderate" | "severe" | null

Focus on extracting facts, not inferring. If information is not present, use null or empty list.

Example input: "There's a huge pothole on 5th and Pine that damaged my car yesterday"
Example output:
{{
  "location": "5th and Pine",
  "location_type": "intersection",
  "service_keywords": ["pothole", "damaged", "car"],
  "urgency_indicators": [],
  "temporal_context": "yesterday",
  "affected_count": null,
  "damage_severity": "moderate"
}}

Now process the actual user input and return ONLY the JSON object, no other text."""


class EntityExtractor:
    """Extract structured entities from service requests."""

    def __init__(self):
        self.client = None
        if settings.anthropic_api_key and not settings.mock_llm:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("entity_extractor_initialized", provider="anthropic")
        else:
            logger.warning("using_mock_entity_extraction")

    async def extract(self, text: str, location: Optional[Location] = None) -> ExtractedEntities:
        """
        Extract entities from text input.

        Args:
            text: User's service request text
            location: Optional location data from user

        Returns:
            ExtractedEntities with structured information
        """
        if settings.mock_llm or not self.client:
            return self._mock_extraction(text, location)

        try:
            # Call LLM for entity extraction
            prompt = EXTRACTION_PROMPT.format(user_input=text)

            response = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.0,  # Deterministic for extraction
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse JSON response
            content = response.content[0].text
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                extracted_data = orjson.loads(json_match.group())
            else:
                extracted_data = orjson.loads(content)

            # Merge with provided location if available
            if location:
                extracted_location = Location(
                    address=location.address or extracted_data.get("location"),
                    latitude=location.latitude,
                    longitude=location.longitude,
                    zipcode=location.zipcode,
                    council_district=location.council_district,
                    neighborhood=location.neighborhood,
                    police_precinct=location.police_precinct,
                )
            else:
                extracted_location = Location(
                    address=extracted_data.get("location")
                ) if extracted_data.get("location") else None

            entities = ExtractedEntities(
                location=extracted_location,
                location_type=extracted_data.get("location_type"),
                service_keywords=extracted_data.get("service_keywords", []),
                urgency_indicators=extracted_data.get("urgency_indicators", []),
                temporal_context=extracted_data.get("temporal_context"),
                affected_count=extracted_data.get("affected_count"),
                damage_severity=extracted_data.get("damage_severity"),
            )

            logger.info(
                "entities_extracted",
                keywords_count=len(entities.service_keywords),
                has_location=entities.location is not None,
                urgency=len(entities.urgency_indicators) > 0
            )

            return entities

        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e))
            # Fallback to basic extraction
            return self._fallback_extraction(text, location)

    def _mock_extraction(self, text: str, location: Optional[Location]) -> ExtractedEntities:
        """Mock extraction for testing."""
        keywords = self._extract_keywords_basic(text)

        return ExtractedEntities(
            location=location,
            location_type="address" if location else None,
            service_keywords=keywords,
            urgency_indicators=[],
            temporal_context=None,
            affected_count=None,
            damage_severity=None,
        )

    def _fallback_extraction(self, text: str, location: Optional[Location]) -> ExtractedEntities:
        """Simple rule-based extraction as fallback."""
        keywords = self._extract_keywords_basic(text)
        urgency = self._detect_urgency(text)
        severity = self._detect_severity(text)

        return ExtractedEntities(
            location=location,
            location_type=self._detect_location_type(text),
            service_keywords=keywords,
            urgency_indicators=urgency,
            temporal_context=self._extract_temporal(text),
            affected_count=None,
            damage_severity=severity,
        )

    def _extract_keywords_basic(self, text: str) -> list[str]:
        """Extract service keywords using simple rules."""
        keywords = []
        service_terms = [
            "pothole", "graffiti", "streetlight", "traffic", "sign",
            "sidewalk", "tree", "garbage", "noise", "parking",
            "water", "sewer", "leak", "damage", "broken", "missing"
        ]

        text_lower = text.lower()
        for term in service_terms:
            if term in text_lower:
                keywords.append(term)

        return keywords

    def _detect_urgency(self, text: str) -> list[str]:
        """Detect urgency indicators."""
        urgency_terms = [
            "emergency", "urgent", "dangerous", "hazard", "safety",
            "injured", "accident", "severe", "critical"
        ]

        text_lower = text.lower()
        return [term for term in urgency_terms if term in text_lower]

    def _detect_severity(self, text: str) -> Optional[str]:
        """Detect damage severity."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["severe", "major", "critical", "dangerous"]):
            return "severe"
        elif any(word in text_lower for word in ["moderate", "significant", "damaged"]):
            return "moderate"
        elif any(word in text_lower for word in ["minor", "small", "slight"]):
            return "minor"

        return None

    def _detect_location_type(self, text: str) -> Optional[str]:
        """Detect type of location mentioned."""
        text_lower = text.lower()

        if " and " in text_lower or " & " in text_lower:
            return "intersection"
        elif any(word in text_lower for word in ["near", "around", "area", "neighborhood"]):
            return "area"
        elif re.search(r'\d+\s+\w+\s+(street|st|avenue|ave|road|rd|way|drive)', text_lower):
            return "address"

        return None

    def _extract_temporal(self, text: str) -> Optional[str]:
        """Extract temporal context."""
        temporal_patterns = [
            r'(yesterday|today|tonight|this morning|this evening)',
            r'(last|this|next)\s+(week|month|year)',
            r'(for|since)\s+\w+\s+(days|weeks|months)',
            r'\d+\s+(days|weeks|months)\s+ago',
        ]

        text_lower = text.lower()
        for pattern in temporal_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group()

        return None


if __name__ == "__main__":
    import asyncio

    async def test():
        extractor = EntityExtractor()

        test_cases = [
            "There's a huge pothole on 5th and Pine that damaged my car",
            "Graffiti on the wall near 1234 Main Street, been there for 2 weeks",
            "Emergency! Dangerous tree about to fall on busy sidewalk"
        ]

        for text in test_cases:
            print(f"\nInput: {text}")
            entities = await extractor.extract(text)
            print(f"Keywords: {entities.service_keywords}")
            print(f"Urgency: {entities.urgency_indicators}")
            print(f"Severity: {entities.damage_severity}")
            print(f"Temporal: {entities.temporal_context}")

    asyncio.run(test())
