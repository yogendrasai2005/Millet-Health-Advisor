# rag_engine.py - UPDATED WITH PRODUCT URL MAPPING

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from config import Config
import re
import html

class MilletRAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = Chroma(
            persist_directory=Config.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        self.llm = ChatGroq(
            groq_api_key=Config.GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
            temperature=0.3
        )
        
        # Product URL mapping for milletamma.com
        self.millet_product_urls = {
            'pearl': 'https://milletamma.com/products/bajra-perl-milet-flour-organic-500gm',
            'foxtail': 'https://milletamma.com/products/foxtail-millet-grains-organic-500gm',
            'finger': 'https://milletamma.com/products/ragi-finger-millet-flour-organic-500gm',
            'barnyard': 'https://milletamma.com/products/barnyard-millet-grains-organic-500gm',
            'little': 'https://milletamma.com/products/little-millet-flour-organic-500gm',
            'kodo': 'https://milletamma.com/products/kodo-millet-grains-organic-500gm',
            'proso': 'https://milletamma.com/products/proso-millet-organic-500gm', # proso millet flour
            'sorghum': 'https://milletamma.com/products/jowar-millet-grain-organic-500gm',
            'bajra': 'https://milletamma.com/products/bajra-methi-khakhra-180gm',
            'ragi': 'https://milletamma.com/products/ragi-grains-finger-millet-organic-500gm',
            'jowar': 'https://milletamma.com/products/jowar-sorghum-flour-organic-500gm',
            'kangni': 'https://milletamma.com/products/foxtail-millet-organic-500gm',
            'kutki': 'https://milletamma.com/products/little-millet-organic-500gm',
            'sama': 'https://milletamma.com/products/barnyard-millet-organic-500gm',
            'chena': 'https://milletamma.com/products/proso-millet-organic-500gm'
        }

    def get_millet_product_url(self, millet_name: str) -> str:
        """
        Get the product URL for a millet from milletamma.com
        Returns a default URL if specific millet not found
        """
        # Clean the millet name
        millet_lower = millet_name.lower().strip()
        
        # Try exact match first
        if millet_lower in self.millet_product_urls:
            return self.millet_product_urls[millet_lower]
        
        # Try partial matches
        for key, url in self.millet_product_urls.items():
            if key in millet_lower or millet_lower in key:
                return url
        
        # Default to millet products page
        return "https://milletamma.com/collections/millet-basket"

    # [Keep all existing methods exactly as they were...]
    # format_llm_output_to_html, get_scientific_evidence, generate_benefits_summary, etc.
    # ... all previous methods remain unchanged ...

    def format_llm_output_to_html(self, text: str) -> str:
        """
        ROBUST FORMATTER: Converts AI text into beautiful, structured HTML cards.
        """
        if not text:
            return "<p>No summary available.</p>"

        # 1. Clean up the raw text artifacts
        text = re.sub(r'\*+#', '#', text)  # Fix *# artifacts
        text = re.sub(r'\*\*', '', text)   # Remove random bolding stars for cleaner look
        
        # 2. Split into main sections based on headers (#)
        # We look for lines starting with # or words like "Recommended", "Key Benefits"
        sections = re.split(r'(?m)^#+\s*(.+)$', text)
        
        html_output = '<div class="summary-container">'
        
        # The split creates empty string at start, then Header, then Content...
        # We skip the first empty string and iterate in pairs
        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                header = sections[i].strip()
                content = sections[i+1].strip() if i+1 < len(sections) else ""
                
                # Assign icons based on header content
                icon = "fa-info-circle"
                if "Recommend" in header: icon = "fa-star"
                elif "Benefit" in header: icon = "fa-heart-pulse"
                elif "Usage" in header or "Tip" in header: icon = "fa-lightbulb"
                elif "Note" in header: icon = "fa-exclamation-circle"
                
                html_output += f"""
                <div class="summary-card">
                    <div class="summary-header">
                        <i class="fas {icon}"></i>
                        <h4>{header}</h4>
                    </div>
                    <div class="summary-body">
                """
                
                # Process the content (Lists vs Paragraphs)
                # Split by newlines or bullets
                lines = [line.strip() for line in re.split(r'\n+|•|- ', content) if line.strip()]
                
                if lines:
                    html_output += '<ul class="summary-list">'
                    for line in lines:
                        # Highlight keywords (anything before a colon or dash)
                        line = re.sub(r'^([^:-]+)([:-]\s*)', r'<strong>\1</strong>\2', line)
                        html_output += f'<li>{line}</li>'
                    html_output += '</ul>'
                    
                html_output += "</div></div>"
        else:
            # Fallback for unstructured text
            html_output += f'<div class="summary-card"><div class="summary-body"><p>{text}</p></div></div>'
            
        html_output += '</div>'
        return html_output

    def _clean_text_structure(self, text: str) -> str:
        """Fix structural issues in the text before HTML conversion"""
        # Remove excessive empty lines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Fix common LLM formatting issues
        text = re.sub(r'(\d+)\.\s*\n', r'\1. ', text)  # Fix numbered list line breaks
        text = re.sub(r'[-*•]\s*\n', '', text)  # Fix bullet list line breaks
        
        # Remove redundant conversational phrases
        redundant_phrases = [
            r"Dear (?:valued customer|user),?\s*",
            r"Best regards,?\s*\[.*?\]\s*",
            r"As a nutrition expert,?\s*",
            r"Our team has\s*",
            r"We understand that\s*",
            r"Below, you'll find\s*",
            r"In conclusion,?\s*",
            r"Remember to always consult\s*"
        ]
        
        for phrase in redundant_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def _convert_markdown_to_html(self, text: str) -> str:
        """Convert markdown formatting to clean HTML"""
        # Convert headers
        text = re.sub(r'^#\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
        
        # Convert bold - handle both **bold** and *bold* formats
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', text)
        
        # Convert numbered lists (1. item)
        lines = text.split('\n')
        in_ol = False
        result = []
        
        for line in lines:
            ol_match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
            if ol_match:
                if not in_ol:
                    result.append('<ol>')
                    in_ol = True
                result.append(f'<li>{ol_match.group(2)}</li>')
            else:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append(line)
        
        if in_ol:
            result.append('</ol>')
        
        text = '\n'.join(result)
        
        # Convert bullet lists (- item, * item)
        lines = text.split('\n')
        in_ul = False
        result = []
        
        for line in lines:
            ul_match = re.match(r'^[-*•]\s+(.+)$', line.strip())
            if ul_match:
                if not in_ul:
                    result.append('<ul>')
                    in_ul = True
                result.append(f'<li>{ul_match.group(1)}</li>')
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                result.append(line)
        
        if in_ul:
            result.append('</ul>')
        
        text = '\n'.join(result)
        
        return text

    def _structure_html_properly(self, text: str) -> str:
        """Ensure proper HTML structure without nesting issues"""
        lines = text.split('\n')
        structured = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # If line is already an HTML tag, add as-is
            if re.match(r'^<(h[1-6]|ul|ol|li|p|strong|em)', line):
                structured.append(line)
            # If line contains text but no HTML, wrap in paragraph
            elif line and not re.match(r'^<', line):
                structured.append(f'<p>{line}</p>')
        
        return '\n'.join(structured)

    def _final_html_cleanup(self, text: str) -> str:
        """Final cleanup of HTML"""
        # Remove empty paragraphs
        text = re.sub(r'<p>\s*</p>', '', text)
        
        # Fix nested paragraphs in lists
        text = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', text)
        
        # Fix nested paragraphs in headers
        text = re.sub(r'<h[1-6]>\s*<p>(.*?)</p>\s*</h[1-6]>', r'<h4>\1</h4>', text)
        
        # Remove any script tags for safety
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Ensure proper spacing
        text = re.sub(r'>\s+<', '><', text)
        
        return text.strip()

    def get_scientific_evidence(self, health_concern: str, millet_type: str = None):
        try:
            if millet_type:
                query = f"health benefits of {millet_type} millet for {health_concern}"
            else:
                query = f"millets for {health_concern} health benefits nutritional composition"
            
            results = self.vector_store.similarity_search(query, k=4)
            
            evidence = []
            for doc in results:
                page = doc.metadata.get('source_page', 'N/A')
                content = doc.page_content.replace('\n', ' ').strip()
                evidence.append(f"Page {page}: {content}")
            
            return evidence
        except Exception as e:
            return [f"Scientific data temporarily unavailable: {str(e)}"]

    def generate_benefits_summary(self, millet_type: str, health_concerns: list, scientific_evidence: list):
        prompt = f"""
        Provide a CLEAN, STRUCTURED summary of {millet_type} millet benefits for {', '.join(health_concerns)}.

        Structure it clearly with these sections:

        # Key Health Benefits
        - Benefit 1 with brief explanation
        - Benefit 2 with brief explanation
        - Benefit 3 with brief explanation

        # How It Helps
        - Mechanism 1
        - Mechanism 2

        # Nutritional Highlights  
        - Key nutrient 1 and benefit
        - Key nutrient 2 and benefit

        # Usage Tips
        - Practical tip 1
        - Practical tip 2
        - Practical tip 3

        Use ONLY the sections above. No introductory phrases. No concluding remarks.
        Keep each bullet point concise - one line only.
        Use **bold** for key terms only.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return self.format_llm_output_to_html(response.content)
        except Exception as e:
            return self.format_llm_output_to_html(f"""
            # Key Health Benefits
            - Supports {', '.join(health_concerns)}
            - Rich in essential nutrients
            - Easy to incorporate into diet

            # Usage Tips  
            - Substitute for rice or wheat
            - Start with 1-2 servings weekly
            - Combine with vegetables
            """)

    def get_combined_recommendation(self, health_concerns: list, user_data: dict):
        # 1. EXTRACT THE CALCULATED WINNERS (The Ordering Fix)
        top_millets = [rec['name'] for rec in user_data.get('recommendations', [])]
        millet_list_string = ", ".join(top_millets)

        # 2. EXTRACT USER'S SPECIFIC NOTES (The New Fix)
        user_query = user_data.get('user_query', '')
        
        # Create a specific instruction if the user typed something
        custom_instruction = ""
        if user_query:
            custom_instruction = f"""
            CRITICAL USER CONTEXT: The user specifically mentioned: "{user_query}". 
            You MUST address this specific need in your benefits and usage tips, 
            even if it goes beyond the selected tags.
            """

        # 3. UPDATE THE PROMPT
        prompt = f"""
        Our data analysis has determined that the best millets for {', '.join(health_concerns)} are: {millet_list_string}.
        
        {custom_instruction}

        Create a recommendation summary specifically for these 3 millets in this exact order.

        Structure it like this:

        # Recommended Millets
        1. {top_millets[0] if len(top_millets) > 0 else 'First Millet'} - key reason relative to user needs
        2. {top_millets[1] if len(top_millets) > 1 else 'Second Millet'} - key reason
        3. {top_millets[2] if len(top_millets) > 2 else 'Third Millet'} - key reason

        # Key Benefits
        - Primary benefit 1 (Connect to: {user_query if user_query else ', '.join(health_concerns)})
        - Primary benefit 2
        - Primary benefit 3

        # Usage Tips
        - Tip 1 for getting started
        - Tip 2 for best results
        - Tip 3 for variety

        # Important Notes
        - Consult healthcare professional
        - Start gradually
        - Individual results may vary

        Be direct. No greetings. No conversational fluff.
        Use **bold** only for millet names and section headers.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return self.format_llm_output_to_html(response.content)
        except Exception as e:
            # Fallback
            return self.format_llm_output_to_html(f"""
            # Recommended Millets
            1. {top_millets[0]} - Excellent choice
            2. {top_millets[1]} - Great alternative
            3. {top_millets[2]} - Good option

            # Key Benefits
            - Addresses your specific health goals
            - Nutrient rich
            - versatile
            """)