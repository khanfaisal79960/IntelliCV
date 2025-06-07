import re
import io
from docx import Document
from PyPDF2 import PdfReader

# NLTK and its preprocessing parts have been removed.
# The parser now relies solely on regex and basic keyword matching for sections.

class ResumeParser:
    def __init__(self):
        # Define common regex patterns for extraction
        self.email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_regex = r'(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        
        # Keywords to identify sections (can be expanded)
        self.education_keywords = ['education', 'academic background', 'qualifications']
        self.experience_keywords = ['experience', 'work history', 'employment', 'professional experience']
        # Skills and Summary extraction via NLTK are removed.
        # If you need skill extraction without NLTK, you'd need a very extensive
        # predefined list and more complex regex/string matching.

    def _read_docx(self, file_stream):
        """Reads text from a .docx file stream."""
        try:
            document = Document(file_stream)
            full_text = []
            for paragraph in document.paragraphs:
                full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading DOCX file: {e}")
            return None

    def _read_pdf(self, file_stream):
        """Reads text from a .pdf file stream."""
        try:
            reader = PdfReader(file_stream)
            full_text = []
            for page in reader.pages:
                full_text.append(page.extract_text())
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return None

    def _read_txt(self, file_stream):
        """Reads text from a .txt file stream."""
        try:
            return file_stream.read().decode('utf-8')
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            return None

    def parse_resume(self, file_stream, filename):
        """
        Parses a resume file to extract information.

        Args:
            file_stream: A file-like object (e.g., from request.files['file']).
            filename: The original filename to determine file type.

        Returns:
            A dictionary containing extracted resume data.
        """
        text = None
        if filename.endswith('.docx'):
            text = self._read_docx(file_stream)
        elif filename.endswith('.pdf'):
            text = self._read_pdf(file_stream)
        elif filename.endswith('.txt'):
            text = self._read_txt(file_stream)
        else:
            return {"error": "Unsupported file type. Please upload a .pdf, .docx, or .txt file."}

        if not text:
            return {"error": "Could not extract text from the file."}

        # Normalize text for easier parsing (lowercase, remove extra whitespace)
        processed_text = text.lower().replace('\n', ' ').replace('\r', ' ').strip()
        processed_text = re.sub(r'\s+', ' ', processed_text) # Replace multiple spaces with single space

        extracted_data = {
            "full_text": text, # Keep original text for display/debugging
            "email": self._extract_email(processed_text),
            "phone": self._extract_phone(processed_text),
            # Skills and Summary extraction removed as NLTK is no longer used
            "education": self._extract_section(processed_text, self.education_keywords),
            "experience": self._extract_section(processed_text, self.experience_keywords),
        }
        return extracted_data

    def _extract_email(self, text):
        """Extracts email addresses from text."""
        emails = re.findall(self.email_regex, text)
        return emails[0] if emails else None

    def _extract_phone(self, text):
        """Extracts phone numbers from text."""
        phones = re.findall(self.phone_regex, text)
        # Filter out short/invalid matches if any, and return the first valid one
        for phone in phones:
            # Simple validation: phone number should have at least 10 digits
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 10:
                return phone
        return None

    def _extract_section(self, text, keywords):
        """
        Extracts a section of text based on keywords.
        This is a very basic implementation. A more robust parser would use NLP
        techniques like dependency parsing or machine learning models.
        """
        section_content = ""
        # Look for the first occurrence of any keyword
        start_index = -1
        for keyword in keywords:
            idx = text.find(keyword)
            if idx != -1 and (start_index == -1 or idx < start_index):
                start_index = idx

        if start_index != -1:
            # Extract content from the keyword's position to the next major section or end of document
            # This is highly heuristic and might not work well for all resume formats.
            # We'll try to find the next section header or just take a chunk.
            
            # Define potential next section headers (simplified)
            next_section_headers = ['education', 'experience', 'skills', 'projects', 'awards', 'publications', 'references']
            
            end_index = len(text)
            for header in next_section_headers:
                if header not in keywords: # Don't look for current section's keywords as next header
                    header_idx = text.find(header, start_index + len(keywords[0])) # Search after current section start
                    if header_idx != -1 and header_idx < end_index:
                        end_index = header_idx

            section_content = text[start_index:end_index].strip()
            # Clean up by removing the keyword itself from the start of the section content
            for keyword in keywords:
                if section_content.lower().startswith(keyword):
                    section_content = section_content[len(keyword):].strip()
                    break
        return section_content if section_content else None

