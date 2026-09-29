import os
import io
import logging
from typing import Dict, Any, Union
import pymupdf as fitz
from services.openai_service import openai_service
from models.schemas import ExtractedResumeData

logger = logging.getLogger("edupath.resume_parser")

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(pdf_bytes_or_path: Union[bytes, str]) -> str:
        """Extract plain text from PDF using PyMuPDF."""
        try:
            if isinstance(pdf_bytes_or_path, bytes):
                doc = fitz.open(stream=pdf_bytes_or_path, filetype="pdf")
            else:
                doc = fitz.open(pdf_bytes_or_path)

            full_text = []
            for page in doc:
                full_text.append(page.get_text("text"))
            doc.close()
            return "\n".join(full_text).strip()
        except Exception as e:
            logger.error(f"PyMuPDF text extraction failed: {e}")
            return ""

    @staticmethod
    def parse_resume(pdf_bytes_or_path: Union[bytes, str], fallback_text: str = "") -> ExtractedResumeData:
        """Extract text and structure resume data into ExtractedResumeData."""
        raw_text = ResumeParser.extract_text_from_pdf(pdf_bytes_or_path)
        if not raw_text and fallback_text:
            raw_text = fallback_text

        if not raw_text.strip():
            return ExtractedResumeData(
                skills=["Python", "Problem Solving"],
                education=["Computer Science"],
                experience=["Academic Projects"],
                projects=["Personal Projects"],
                certifications=[],
                achievements=[],
                tools=["Git", "VS Code"],
                technologies=["Python"],
                domains=["Software Development"],
                raw_text="No extractable text found in PDF. Default skeleton provided."
            )

        extracted_dict = openai_service.extract_resume_entities(raw_text)
        return ExtractedResumeData(
            skills=extracted_dict.get("skills", []),
            education=extracted_dict.get("education", []),
            experience=extracted_dict.get("experience", []),
            projects=extracted_dict.get("projects", []),
            certifications=extracted_dict.get("certifications", []),
            achievements=extracted_dict.get("achievements", []),
            tools=extracted_dict.get("tools", []),
            technologies=extracted_dict.get("technologies", []),
            domains=extracted_dict.get("domains", []),
            raw_text=raw_text
        )

resume_parser = ResumeParser()
