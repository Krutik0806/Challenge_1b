import os
import json
import time
from datetime import datetime, timezone
import fitz
from sentence_transformers import SentenceTransformer, util
import torch
import warnings

# Suppress deprecation warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Configuration with sensible defaults
documents_folder = os.getenv('INPUT_DIR', 'input')
results_folder = os.getenv('OUTPUT_DIR', 'output')
ai_model_name = os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')
model_location = os.getenv('MODEL_PATH', ai_model_name)
max_sections_to_return = int(os.getenv('TOP_SECTIONS_COUNT', '5'))
max_sentences_per_section = int(os.getenv('TOP_SENTENCES_COUNT', '8'))

# --- Main Processing Logic ---

def get_document_sections(pdf_path):
    """Extract sections with headings and content from a PDF document."""
    document = fitz.open(pdf_path)
    document_sections = []
    current_heading = "Introduction"
    current_content = ""
    current_page_number = 1

    for page_number, page in enumerate(document, 1):
        text_blocks = page.get_text("dict")["blocks"]
        for block in text_blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_content = ""
                    might_be_heading = False
                    font_sizes = []
                    text_is_bold = False
                    
                    for text_span in line["spans"]:
                        line_content += text_span["text"]
                        font_sizes.append(text_span["size"])
                        if text_span["flags"] & 2**4:  # Bold text
                            text_is_bold = True
                    
                    line_content = line_content.strip()
                    if not line_content:
                        continue
                    
                    # Check if this line looks like a heading
                    average_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
                    
                    might_be_heading = False
                    words_in_line = line_content.split()
                    
                    if line_content and len(words_in_line) >= 2:
                        might_be_heading = (
                            (text_is_bold and len(line_content) < 120 and len(words_in_line) <= 15) or
                            (average_font_size > 13.5) or
                            (line_content.endswith(":") and len(line_content) < 100) or
                            (len(line["spans"]) == 1 and text_is_bold and len(words_in_line) <= 12)
                        )
                    
                    if might_be_heading and len(line_content) > 5:
                        if current_content.strip():
                            document_sections.append({
                                "title": current_heading.strip(), 
                                "content": current_content.strip(), 
                                "page": current_page_number
                            })
                        current_heading = line_content
                        current_content = ""
                        current_page_number = page_number
                    else:
                        # Clean special characters before adding to content
                        cleaned_line = remove_special_characters(line_content)
                        current_content += cleaned_line + " "

    if current_content.strip():
        # Clean the final content before adding to sections
        cleaned_final_content = remove_special_characters(current_content.strip())
        document_sections.append({"title": current_heading.strip(), "content": cleaned_final_content, "page": current_page_number})

    document.close()
    return document_sections

def remove_special_characters(text):
    """Clean bullet points and special characters that might appear as [?] symbols"""
    if not text:
        return text
    
    # Replace various bullet points and special characters with dashes
    replacements = {
        '•': '- ',  # Bullet point
        '▪': '- ',  # Black small square
        '‣': '- ',  # Triangular bullet
        '◦': '- ',  # White bullet
        '\u2022': '- ',  # Unicode bullet point
        '\u25aa': '- ',  # Unicode black small square
        '\u25ab': '- ',  # Unicode white small square
        '\u2023': '- ',  # Triangular bullet
        '\u2043': '- ',  # Hyphen bullet
        '\uf0b7': '- ',  # Private use area bullet (common in PDFs)
        '\uf06c': '- ',  # Another private use bullet
    }
    
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    # Clean up any remaining non-printable characters
    text = ''.join(char if ord(char) < 127 or char.isalnum() or char in ' .,!?()-:;/[]{}"\'' else ' ' for char in text)
    
    # Clean up multiple spaces
    text = ' '.join(text.split())
    
    return text

def analyze_documents():
    """Main function to process PDF documents and extract relevant sections."""
    start_time = time.time()

    print("✅ Initializing document analysis system...")
    # Use CPU-only to avoid graphics card dependencies
    processing_device = "cpu"
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # Work offline - no internet needed
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    
    ai_model = SentenceTransformer(model_location, device=processing_device)
    print("✅ System ready for document processing.")

    # Find the input configuration file
    config_file_path = None
    for filename in os.listdir(documents_folder):
        if filename.lower().endswith('.json'):
            config_file_path = os.path.join(documents_folder, filename)
            break

    if not config_file_path:
        print(f"Error: No configuration file found in {documents_folder}")
        return

    with open(config_file_path, 'r') as file:
        user_requirements = json.load(file)

    user_role = user_requirements.get("persona", {}).get("role", "")
    user_task = user_requirements.get("job_to_be_done", {}).get("task", "")
    
    # Create a natural query from user requirements
    search_query = f"As a {user_role}, I need to {user_task}"

    document_list = user_requirements.get("documents", [])
    pdf_filenames = [doc["filename"] for doc in document_list if "filename" in doc]

    all_document_sections = []
    print(f"✅ Processing documents: {len(pdf_filenames)} files detected")
    for pdf_filename in pdf_filenames:
        # Look for PDFs in common locations
        pdf_folders = os.getenv('PDF_SUBFOLDERS', 'PDFs,pdfs,documents,docs').split(',')
        possible_locations = [
            os.path.join(documents_folder, pdf_filename),
        ]
        
        # Check subfolders
        for folder in pdf_folders:
            folder = folder.strip()
            if folder:
                possible_locations.append(os.path.join(documents_folder, folder, pdf_filename))
        
        # Add absolute path as fallback
        possible_locations.append(pdf_filename)
        
        pdf_file_path = None
        for location in possible_locations:
            if os.path.exists(location):
                pdf_file_path = location
                break
        
        if not pdf_file_path:
            print(f"Document not found: {pdf_filename}")
            continue
        try:
            sections_from_document = get_document_sections(pdf_file_path)
            for section in sections_from_document:
                section["document"] = pdf_filename
                all_document_sections.append(section)
        except Exception as error:
            print(f"Processing error: {pdf_filename}")

    if not all_document_sections:
        print("No content extracted from documents.")
        return

    # Filter out very short sections
    substantial_sections = [section for section in all_document_sections if len(section["content"]) > 20]
    
    if not substantial_sections:
        print("Insufficient content for analysis.")
        return

    print("✅ Analyzing document content...")
    
    # Use AI to understand semantic similarity
    query_embedding = ai_model.encode(search_query, convert_to_tensor=True)
    
    section_texts = [section["content"] for section in substantial_sections]
    section_embeddings = ai_model.encode(section_texts, convert_to_tensor=True)

    print("✅ Ranking content by relevance...")
    
    # Find the most relevant sections
    similarity_scores = util.cos_sim(query_embedding, section_embeddings)

    for index, section in enumerate(substantial_sections):
        section['relevance_score'] = similarity_scores[0][index].item()
        
    # Sort by how relevant they are
    ranked_sections = sorted(substantial_sections, key=lambda x: x['relevance_score'], reverse=True)
    
    # Take the most relevant sections
    top_sections = ranked_sections[:max_sections_to_return]

    print("✅ Generating detailed analysis...")
    final_results = []
    detailed_analysis = []

    for rank, section in enumerate(top_sections):
        final_results.append({
            "document": section["document"],
            "section_title": section["title"],
            "importance_rank": rank + 1,
            "page_number": section["page"]
        })

        # Break content into sentences and find the best ones
        sentences = []
        content_text = section["content"].replace('\n', ' ')
        
        # Clean up special characters
        content_text = remove_special_characters(content_text)
        
        # Split into sentences
        raw_sentences = content_text.split('.')
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                sentence = ' '.join(sentence.split())
                if not sentence.endswith('.') and sentence:
                    sentence += '.'
                sentences.append(sentence)
        
        # Handle very long sentences by splitting further
        improved_sentences = []
        for sentence in sentences:
            if len(sentence) > 200:
                # Split long sentences at natural breaks
                sub_parts = []
                for delimiter in [';', ':']:
                    if delimiter in sentence:
                        sub_parts = sentence.split(delimiter)
                        break
                if sub_parts:
                    for part in sub_parts:
                        part = part.strip()
                        if len(part) > 10:
                            if not part.endswith('.') and part:
                                part += '.'
                            improved_sentences.append(part)
                else:
                    improved_sentences.append(sentence)
            else:
                improved_sentences.append(sentence)
        
        sentences = improved_sentences

        refined_content = section["content"].strip()
        if sentences and len(sentences) > 1:
            sentence_embeddings = ai_model.encode(sentences, convert_to_tensor=True)
            # Find sentences most relevant to the user's query
            sentence_scores = util.cos_sim(query_embedding, sentence_embeddings)[0]
            best_sentences = sorted(zip(sentences, sentence_scores), key=lambda x: x[1], reverse=True)
            
            # Take the best sentences for detailed analysis
            sentences_to_include = min(len(best_sentences), max_sentences_per_section)
            selected_sentences = [s[0].strip() for s in best_sentences[:sentences_to_include]]
            
            # Use full content if selection is too short
            initial_content = ' '.join(selected_sentences)
            if len(initial_content) < 150 and len(section["content"]) < 800:
                refined_content = section["content"].strip()
            else:
                refined_content = initial_content
            
            # Clean up the final text
            refined_content = ' '.join(refined_content.split())
            
            # Keep only meaningful sentences with cooking-related content
            sentence_list = refined_content.split('.')
            meaningful_sentences = []
            for sentence in sentence_list:
                sentence = sentence.strip()
                # Look for cooking-related keywords
                cooking_words = ['ingredient', 'instruction', 'cup', 'tablespoon', 'teaspoon', 'pound', 'ounce', 'clove', 'cook', 'add', 'mix', 'serve', 'bake', 'heat']
                if len(sentence) > 15 and any(word in sentence.lower() for word in cooking_words):
                    if not sentence.endswith('.') and sentence:
                        sentence += '.'
                    meaningful_sentences.append(sentence)
            
            if meaningful_sentences:
                refined_content = ' '.join(meaningful_sentences)
            else:
                # Fallback to original content if filtering removes too much
                refined_content = section["content"].strip()[:500] + "..." if len(section["content"]) > 500 else section["content"].strip()
        else:
            # For short sections, use the full content
            refined_content = section["content"].strip()

        detailed_analysis.append({
            "document": section["document"],
            "refined_text": refined_content,
            "page_number": section["page"]
        })

    processing_time = time.time() - start_time
    
    # Get challenge information for output filename
    challenge_details = user_requirements.get("challenge_info", {})
    challenge_identifier = challenge_details.get("challenge_id", "challenge")
    
    final_output = {
        "metadata": {
            "input_documents": pdf_filenames,
            "persona": user_role,
            "job_to_be_done": user_task,
            "processing_timestamp": datetime.now(timezone.utc).isoformat()
        },
        "extracted_sections": final_results,
        "subsection_analysis": detailed_analysis
    }

    # Create output filename based on challenge identifier
    output_filename = os.path.join(results_folder, f"{challenge_identifier.replace('round_', '')}_output.json")
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        json.dump(final_output, output_file, indent=4, ensure_ascii=False)

    print(f"✅ Document analysis completed. Output: {os.path.basename(output_filename)}")

def test_system():
    """Test if all components are working correctly."""
    print("✅ System diagnostic initiated...")
    
    try:
        # Check if AI model files exist locally
        print("✅ Checking model availability...")
        if os.path.exists('models/all-MiniLM-L6-v2'):
            print("✅ Local model detected")
        else:
            print("✅ Using default model configuration")
        
        # Test AI model loading
        print("✅ Loading analysis engine...")
        ai_model = SentenceTransformer(model_location, device='cpu')
        print("✅ Analysis engine ready")
        
        # Test model functionality
        print("✅ Verifying system functionality...")
        test_sentences = ["This is a test sentence.", "Another test sentence."]
        embeddings = ai_model.encode(test_sentences)
        similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        print(f"✅ System verification complete (score: {similarity.item():.3f})")
        
        # Check input and output directories
        print("✅ Validating directory structure...")
        if os.path.exists(documents_folder):
            print(f"✅ Input directory: {documents_folder}")
        else:
            print(f"❌ Input directory missing: {documents_folder}")
        
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)
            print(f"✅ Output directory created: {results_folder}")
        else:
            print(f"✅ Output directory: {results_folder}")
        
        print("✅ System ready for operation")
        return True
        
    except Exception as error:
        print(f"❌ System diagnostic failed: {error}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if user wants to test the system
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = test_system()
        sys.exit(0 if success else 1)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    analyze_documents()