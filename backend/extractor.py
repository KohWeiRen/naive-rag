from pathlib import Path
from typing import List, Optional
import json, os
from pypdf import PdfReader
from bs4 import BeautifulSoup as bs

supported_extensions = [".pdf", ".html", ".json", ".md", ".txt"]

def get_files_from_directory(directory: str, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Get all files from a directory with specified extensions.

    Args:
        directory (str): The directory to search for files.
        extensions (Optional[List[str]]): A list of file extensions to filter by. If None, all files are returned.

    Returns:
        List[Path]: A list of Path objects representing the files found.
    """
    if extensions is not None:
        extensions = [ext.lower() for ext in extensions]
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions is None or file_path.suffix.lower() in extensions:
                files.append(file_path)
    
    return files

def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_html(html_path: Path) -> str:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = bs(f)
    return soup.get_text(separator="\n").strip()

def extract_text_from_json(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if isinstance(data, dict):
        return json.dumps(data, indent=4)
    elif isinstance(data, list):
        return "\n".join(json.dumps(item, indent=4) for item in data)
    
def extract_text_from_md_and_txt(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()
    
def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        file_path (Path): The path to the file.

    Returns:
        str: The extracted text.
    """
    if file_path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() == ".html":
        return extract_text_from_html(file_path)
    elif file_path.suffix.lower() == ".json":
        return extract_text_from_json(file_path)
    elif file_path.suffix.lower() in [".md", ".txt"]:
        return extract_text_from_md_and_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
