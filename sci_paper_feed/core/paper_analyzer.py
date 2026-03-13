"""LLM-powered paper analysis and ranking system."""

from typing import List, Dict, Tuple
import json
import logging
import config
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import LLMClient


PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _load_prompt(filename: str, **kwargs) -> tuple[str, str]:
    """
    Load a prompt file and return (system_prompt, user_prompt).

    The file must contain a '## System' section and a '## User' section.
    Placeholders in the form <<VARIABLE_NAME>> are replaced with kwargs values.
    """
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("## User", 1)
    system_part = parts[0].replace("## System", "").strip()
    user_part = parts[1].strip() if len(parts) > 1 else ""

    for key, value in kwargs.items():
        placeholder = f"<<{key.upper()}>>"
        system_part = system_part.replace(placeholder, value)
        user_part = user_part.replace(placeholder, value)

    return system_part, user_part


class PaperAnalyzer:
    """Analyzes and ranks research papers using LLM."""

    def __init__(self, provider: str = None):
        self.llm_client = LLMClient(provider)
        self.logger = logging.getLogger(__name__)

    def analyze_and_rank_papers(
        self, papers: List[Dict[str, str]], top_k: int = None
    ) -> Tuple[List[Dict], str]:
        """
        Analyze papers and return top k most interesting ones with a daily summary.

        Args:
            papers: List of paper dictionaries with title, abstract, etc.
            top_k: Number of top papers to return (uses config.TOP_PAPERS_COUNT if None)

        Returns:
            Tuple of (top_papers_list, daily_summary)
        """
        if not papers:
            return [], "No papers found for today."

        if top_k is None:
            top_k = config.TOP_PAPERS_COUNT

        # Analyze papers in batches to avoid token limits
        batch_size = config.ANALYSIS_BATCH_SIZE
        all_analyses = []
        num_batches = (len(papers) + batch_size - 1) // batch_size

        for i in range(0, len(papers), batch_size):
            batch = papers[i : i + batch_size]
            batch_analysis = self._analyze_paper_batch(batch)
            all_analyses.extend(batch_analysis)

        # If papers were split across multiple batches, scores may not be
        # calibrated against each other. Run a final re-ranking pass.
        if num_batches > 1 and all_analyses:
            all_analyses = self._recalibrate_scores(all_analyses)

        # Rank all papers
        ranked_papers = self._rank_papers(all_analyses)

        # Get top k papers
        top_papers = ranked_papers[:top_k]

        # Generate daily summary
        daily_summary = self._generate_daily_summary(all_analyses)

        return top_papers, daily_summary

    def _analyze_paper_batch(self, papers: List[Dict[str, str]]) -> List[Dict]:
        """Analyze a batch of papers for novelty, applications, and cleverness."""

        # Prepare papers for analysis
        papers_text = ""
        for i, paper in enumerate(papers):
            papers_text += f"""
Paper {i+1}:
Title: {paper['title']}
Authors: {paper['authors']}
Abstract: {paper['abstract']}
URL: {paper['url']}

---
"""

        try:
            system_prompt, prompt = _load_prompt("batch_analysis.md", papers_text=papers_text)
            response_text = self.llm_client.generate_response(system_prompt, prompt)

            # Extract JSON from response (handle markdown code blocks)
            json_text = self._extract_json_from_response(response_text)

            # Parse the JSON response with error handling
            try:
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                self.logger.debug(f"JSON parsing failed: {e}")
                self.logger.debug(f"JSON text length: {len(json_text)}")
                self.logger.debug(f"First 10 characters (repr): {repr(json_text[:10])}")
                self.logger.debug(f"Problematic JSON text: {json_text[:500]}...")

                # Try a more aggressive cleanup
                cleaned_json = self._aggressive_json_cleanup(json_text)
                self.logger.debug(
                    f"After aggressive cleanup, first 10 chars: {repr(cleaned_json[:10])}"
                )
                try:
                    analysis_data = json.loads(cleaned_json)
                    self.logger.debug("Successfully parsed with aggressive cleanup")
                except json.JSONDecodeError as e2:
                    self.logger.debug(f"JSON parsing still failed after cleanup: {e2}")

                    # Try one more approach - decode literal escape sequences
                    try:
                        # This handles cases where the LLM returns literal \n instead of newlines
                        decoded_json = cleaned_json.encode().decode("unicode_escape")
                        analysis_data = json.loads(decoded_json)
                        self.logger.debug(
                            "Successfully parsed with unicode_escape decode"
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError) as e3:
                        self.logger.debug(f"Unicode escape decode failed: {e3}")

                        # Try one final repair attempt
                        try:
                            repaired_json = self._repair_json_syntax(cleaned_json)
                            analysis_data = json.loads(repaired_json)
                            self.logger.debug("Successfully parsed with JSON repair")
                        except json.JSONDecodeError as e4:
                            self.logger.error(f"Final JSON parsing attempt failed: {e4}")
                            self.logger.warning("Using fallback analysis")
                            return self._create_fallback_analysis(papers)

            # Combine analysis with original paper data
            analyzed_papers = []
            for analysis in analysis_data["analyses"]:
                paper_idx = analysis["paper_index"] - 1
                if 0 <= paper_idx < len(papers):
                    paper_with_analysis = papers[paper_idx].copy()
                    paper_with_analysis.update(
                        {
                            "score": analysis["score"],
                            "explanation": analysis["explanation"],
                            "key_insights": analysis["key_insights"],
                            "analysis_type": "llm",
                        }
                    )
                    analyzed_papers.append(paper_with_analysis)

            return analyzed_papers

        except Exception as e:
            self.logger.error(f"Error analyzing papers: {e}")
            return [
                {
                    **paper,
                    "score": 5,
                    "explanation": "Analysis unavailable",
                    "key_insights": "N/A",
                    "analysis_type": "fallback",
                }
                for paper in papers
            ]

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from response text, handling markdown code blocks and escape issues."""
        import re

        # Remove BOM and other invisible characters at the start
        response_text = response_text.encode("utf-8").decode("utf-8-sig").strip()

        # Try to find JSON within markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(json_pattern, response_text, re.DOTALL)

        if match:
            json_text = match.group(1).strip()
        else:
            # If no code blocks, try to find JSON directly
            # Look for content between first { and last }
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}")

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx : end_idx + 1].strip()
            else:
                # If still no JSON found, return the original text
                return response_text.strip()

        # Remove any BOM or invisible characters from extracted JSON
        json_text = json_text.encode("utf-8").decode("utf-8-sig").strip()

        # Clean up common JSON issues
        json_text = self._clean_json_text(json_text)

        return json_text

    def _clean_json_text(self, json_text: str) -> str:
        """Clean JSON text to fix common escape and formatting issues."""
        import re

        # Fix common escape sequence issues
        # Replace unescaped backslashes (but not already escaped ones)
        json_text = re.sub(
            r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r"\\\\", json_text
        )

        # Fix unescaped quotes in strings (basic heuristic)
        # This is tricky, so we'll be conservative

        # Fix newlines in JSON strings (replace with \n)
        json_text = re.sub(r'(?<!")(\n|\r\n|\r)(?!")', r"\\n", json_text)

        # Fix tabs in JSON strings
        json_text = re.sub(r'(?<!")\t(?!")', r"\\t", json_text)

        # Remove any trailing commas before } or ]
        json_text = re.sub(r",\s*([}\]])", r"\1", json_text)

        return json_text

    def _aggressive_json_cleanup(self, json_text: str) -> str:
        """More aggressive JSON cleanup for problematic responses."""
        import re

        # Strip all leading/trailing whitespace and invisible characters
        json_text = json_text.strip()

        # Remove BOM and other invisible Unicode characters at start
        json_text = json_text.encode("utf-8").decode("utf-8-sig")

        # Remove any invisible characters at the beginning
        while json_text and ord(json_text[0]) < 32 and json_text[0] not in "\n\r\t":
            json_text = json_text[1:]

        # Replace smart quotes with regular quotes
        json_text = json_text.replace('"', '"').replace('"', '"')
        json_text = json_text.replace(""", "'").replace(""", "'")

        # Fix common problematic characters
        json_text = json_text.replace("\u2013", "-")  # en dash
        json_text = json_text.replace("\u2014", "-")  # em dash
        json_text = json_text.replace("\u2019", "'")  # right single quotation mark

        # Remove any non-printable characters except necessary JSON chars
        json_text = re.sub(r"[^\x20-\x7E\n\r\t]", "", json_text)

        # Handle literal escape sequences (when LLM returns \n as literal text instead of newline)
        if "\\n" in json_text and json_text.count("\\n") > json_text.count("\n"):
            # Convert literal \n, \t, etc. to actual escape sequences
            json_text = json_text.replace("\\n", "\n")
            json_text = json_text.replace("\\t", "\t")
            json_text = json_text.replace("\\r", "\r")
            json_text = json_text.replace('\\"', '"')
        else:
            # Standard backslash escaping for actual backslashes
            json_text = json_text.replace("\\", "\\\\")
            # But fix the over-escaping of JSON escape sequences
            json_text = json_text.replace("\\\\n", "\\n")
            json_text = json_text.replace("\\\\t", "\\t")
            json_text = json_text.replace("\\\\r", "\\r")
            json_text = json_text.replace('\\\\"', '\\"')
            json_text = json_text.replace("\\\\/", "\\/")

        # Final strip
        json_text = json_text.strip()

        return json_text

    def _repair_json_syntax(self, json_text: str) -> str:
        """Attempt to repair common JSON syntax errors."""
        self.logger.debug("Attempting JSON syntax repair...")

        # Common repairs
        repaired = json_text

        # Fix missing commas between objects/arrays
        import re

        # Fix missing commas after closing braces/brackets followed by opening ones
        repaired = re.sub(r"}\s*{", "}, {", repaired)
        repaired = re.sub(r"]\s*\[", "], [", repaired)
        repaired = re.sub(r"}\s*\[", "}, [", repaired)
        repaired = re.sub(r"]\s*{", "], {", repaired)

        # Fix missing commas after quoted strings followed by quotes
        repaired = re.sub(r'"\s*"', '", "', repaired)

        # Fix missing commas after numbers followed by quotes
        repaired = re.sub(r'(\d)\s*"', r'\1, "', repaired)

        # Fix missing commas after quotes followed by numbers
        repaired = re.sub(r'"\s*(\d)', r'", \1', repaired)

        # Fix trailing commas before closing braces/brackets
        repaired = re.sub(r",\s*}", "}", repaired)
        repaired = re.sub(r",\s*]", "]", repaired)

        # Fix unescaped quotes in strings (basic attempt)
        # This is tricky, so we'll do a simple fix for common cases
        repaired = re.sub(r'(?<!\\)"(?![\s,:\]}])', '\\"', repaired)

        # Fix missing quotes around keys (if they look like identifiers)
        repaired = re.sub(
            r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', repaired
        )

        self.logger.debug(f"JSON repair complete. Length: {len(repaired)}")
        return repaired

    def _create_fallback_analysis(self, papers: List[Dict[str, str]]) -> List[Dict]:
        """Create fallback analysis when JSON parsing fails."""
        fallback_papers = []
        for i, paper in enumerate(papers):
            # Simple scoring based on title keywords and abstract length
            score = 5  # Default score

            # Boost score for certain keywords in title
            title_lower = paper.get("title", "").lower()
            if any(
                keyword in title_lower
                for keyword in [
                    "novel",
                    "new",
                    "breakthrough",
                    "advanced",
                    "sota",
                    "state-of-the-art",
                ]
            ):
                score += 1
            if any(
                keyword in title_lower
                for keyword in ["llm", "transformer", "neural", "deep learning", "ai"]
            ):
                score += 1
            if any(
                keyword in title_lower
                for keyword in ["multimodal", "vision", "language", "reasoning"]
            ):
                score += 1

            # Boost score for longer abstracts (usually more detailed)
            abstract_len = len(paper.get("abstract", ""))
            if abstract_len > 1000:
                score += 1

            # Cap at 10
            score = min(score, 10)

            paper_with_analysis = paper.copy()
            paper_with_analysis.update(
                {
                    "score": score,
                    "explanation": f"Analysis based on title keywords and content indicators. Score: {score}/10",
                    "key_insights": "Detailed analysis unavailable due to parsing issues.",
                    "analysis_type": "fallback",
                }
            )
            fallback_papers.append(paper_with_analysis)

        return fallback_papers

    def _recalibrate_scores(self, analyzed_papers: List[Dict]) -> List[Dict]:
        """
        After multi-batch scoring, re-rank all papers together to remove
        between-batch score inflation / deflation.
        """
        # Build a compact summary of each paper's batch analysis
        papers_summary = ""
        for i, paper in enumerate(analyzed_papers):
            papers_summary += (
                f"Paper {i+1}: {paper['title']}\n"
                f"  Batch score: {paper.get('score', '?')}\n"
                f"  Summary: {paper.get('explanation', '')}\n\n"
            )

        try:
            system_prompt, prompt = _load_prompt("recalibrate_scores.md", papers_summary=papers_summary)
            response_text = self.llm_client.generate_response(system_prompt, prompt)
            json_text = self._extract_json_from_response(response_text)
            data = json.loads(json_text)

            # Apply recalibrated scores
            score_map = {item["paper_index"] - 1: item["score"] for item in data["recalibrated"]}
            for idx, paper in enumerate(analyzed_papers):
                if idx in score_map:
                    paper["score"] = score_map[idx]
        except Exception as e:
            self.logger.warning(f"Score recalibration failed, keeping batch scores: {e}")

        return analyzed_papers

    def _rank_papers(self, analyzed_papers: List[Dict]) -> List[Dict]:
        """Rank papers by their analysis scores."""
        return sorted(analyzed_papers, key=lambda x: x.get("score", 0), reverse=True)

    def _generate_daily_summary(self, analyzed_papers: List[Dict]) -> str:
        """Generate a 2-sentence daily summary of all analyzed papers."""

        # Prepare summary of all papers
        papers_summary = ""
        for paper in analyzed_papers:
            papers_summary += f"- {paper['title']}: {paper.get('explanation', 'No analysis available')}\n"

        try:
            system_prompt, prompt = _load_prompt("daily_summary.md", papers_summary=papers_summary)
            response_text = self.llm_client.generate_response(system_prompt, prompt)

            return response_text.strip()

        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
            return "Today in the field of AI: Multiple research papers were published covering various aspects of artificial intelligence. The research spans diverse applications and methodological advances in the field."
