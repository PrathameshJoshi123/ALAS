import pymupdf4llm
from pathlib import Path


def parse_pdf(pdf_path: str, company_name: str = None, output_dir: str = None) -> str:
    """
    Parse a PDF file and convert it to markdown.
    Automatically saves the markdown to the contracts folder.
    
    Args:
        pdf_path: Path to the PDF file to parse
        company_name: Name of the company (used for filename)
        
    Returns:
        str: Filename of the saved markdown file
    """
    # Parse PDF to markdown
    md_text = pymupdf4llm.to_markdown(pdf_path)
    
    # Save to the requested contract markdown directory
    contracts_dir = (
        Path(output_dir)
        if output_dir
        else Path(__file__).parent.parent / "workers" / "contract" / "contracts"
    )
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    if company_name:
        md_filename = f"{company_name.replace(' ', '_').lower()}_contract.md"
    else:
        md_filename = Path(pdf_path).stem + ".md"
    
    # Save markdown file
    md_filepath = contracts_dir / md_filename
    md_filepath.write_text(md_text, encoding="utf-8")
    
    return md_filename


# ==============================================================================
# LEGACY CODE (kept for backward compatibility)
# ==============================================================================

# md_text = pymupdf4llm.to_markdown("test.pdf")
# print(md_text)
# pathlib.Path("4llm-output.md").write_bytes(md_text.encode())