"""
PaddleOCR Text Extraction Utility
Extracts text and metadata from contract PDF documents
Graceful fallback to pypdf if PaddleOCR unavailable due to dependency issues
"""

import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class PaddleOCRExtractor:
    """Wrapper for PaddleOCR for contract document processing with fallback"""
    
    def __init__(self):
        """Initialize PaddleOCR with graceful fallback"""
        self.ocr = None
        self.paddle_available = False
        self.use_pypdf_fallback = False
        
        try:
            from paddleocr import PaddleOCR
            
            # Initialize with settings optimized for document extraction
            # PP-OCRv5 for text recognition with document orientation detection
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Detect document orientation
                use_gpu=False,  # CPU for consistency in production
                lang='en',  # Support English + other languages
                show_log=False,
                det_model_dir=None,  # Use default models
                rec_model_dir=None,
                cls_model_dir=None,
            )
            
            self.paddle_available = True
            logger.info("Initialized PaddleOCR extractor successfully")
            
        except ImportError as e:
            # PaddleOCR not available - use pypdf fallback (sufficient for standard PDFs)
            logger.info(f"PaddleOCR not available ({str(e)}). Using pypdf fallback - optimal for text-based PDFs")
            self.use_pypdf_fallback = True
            self.paddle_available = False
            
        except Exception as e:
            # Other initialization errors - use pypdf fallback
            logger.warning(f"PaddleOCR initialization failed ({str(e)}), using pypdf fallback for text extraction")
            self.use_pypdf_fallback = True
            self.paddle_available = False
    
    def _extract_with_pypdf_fallback(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback text extraction using pypdf when PaddleOCR unavailable
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Dict with extracted text
        """
        try:
            import pypdf
            from pathlib import Path
            
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            pages = []
            all_text = []
            
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_reader = pypdf.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        page_text = page.extract_text() or ""
                        
                        pages.append({
                            'page_number': page_num,
                            'text': page_text,
                            'confidence': 0.95,  # pypdf doesn't have confidence scores
                            'lines': [{'text': line, 'confidence': 0.95} for line in page_text.split('\n') if line.strip()]
                        })
                        all_text.append(page_text)
                
                raw_text = '\n\n---PAGE BREAK---\n\n'.join(all_text)
                
                logger.info(f"Successfully extracted text from {total_pages} pages using pypdf fallback")
                
                return {
                    'raw_text': raw_text,
                    'confidence': 0.95,  # Estimated for pypdf
                    'confidence_percentage': 95,
                    'pages': pages,
                    'total_pages': total_pages,
                    'extraction_method': 'pypdf_fallback',
                    'error': None
                }
                
            except Exception as e:
                logger.error(f"pypdf extraction failed: {str(e)}")
                # Return empty result rather than failing completely
                return {
                    'raw_text': '',
                    'confidence': 0.0,
                    'confidence_percentage': 0,
                    'pages': [],
                    'total_pages': 0,
                    'extraction_method': 'failed',
                    'error': f'Text extraction failed: {str(e)}'
                }
                
        except ImportError:
            logger.error("pypdf not available - cannot extract text from PDF")
            return {
                'raw_text': '',
                'confidence': 0.0,
                'confidence_percentage': 0,
                'pages': [],
                'total_pages': 0,
                'extraction_method': 'unavailable',
                'error': 'No text extraction method available'
            }
    
    def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF contract document
        Uses PaddleOCR if available, falls back to pypdf
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Dict containing:
            {
                'raw_text': str,  # Complete concatenated text
                'confidence': float,  # Average confidence 0-1
                'pages': [  # Per-page details
                    {
                        'page_number': int,
                        'text': str,
                        'confidence': float,
                        'lines': [  # Line-level details
                            {
                                'text': str,
                                'confidence': float,
                                'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] (PaddleOCR only)
                            }
                        ]
                    }
                ],
                'total_pages': int,
                'extraction_method': 'paddle_ocr' | 'pypdf_fallback' | 'failed',
                'error': None or str
            }
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Use fallback if PaddleOCR not available
        if self.use_pypdf_fallback or not self.paddle_available:
            return self._extract_with_pypdf_fallback(file_path)
        
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Extracting text from: {file_path}")
            
            # Perform OCR on the PDF using PaddleOCR
            result = self.ocr.ocr(file_path, cls=True)
            
            if not result or len(result) == 0:
                logger.warning(f"No text extracted from {file_path} using PaddleOCR, trying fallback")
                return self._extract_with_pypdf_fallback(file_path)
            
            # Process results
            pages = []
            all_text = []
            all_confidences = []
            
            for page_num, page_result in enumerate(result, 1):
                page_text = []
                page_lines = []
                page_confidences = []
                
                if page_result:
                    for line_data in page_result:
                        # Each line_data is: [bbox, (text, confidence)]
                        bbox, (text, confidence) = line_data
                        
                        page_text.append(text)
                        page_confidences.append(confidence)
                        all_confidences.append(confidence)
                        
                        page_lines.append({
                            'text': text,
                            'confidence': round(confidence, 4),
                            'bbox': bbox
                        })
                
                page_full_text = '\n'.join(page_text) if page_text else ''
                page_avg_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0
                
                pages.append({
                    'page_number': page_num,
                    'text': page_full_text,
                    'confidence': round(page_avg_confidence, 4),
                    'lines': page_lines
                })
                
                all_text.append(page_full_text)
            
            # Calculate overall statistics
            raw_text = '\n\n---PAGE BREAK---\n\n'.join(all_text)
            overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            confidence_percentage = int(overall_confidence * 100)
            
            result_dict = {
                'raw_text': raw_text,
                'confidence': round(overall_confidence, 4),
                'confidence_percentage': confidence_percentage,
                'pages': pages,
                'total_pages': len(pages),
                'extraction_method': 'paddle_ocr',
                'error': None
            }
            
            logger.info(
                f"Successfully extracted text from {len(pages)} pages "
                f"with {confidence_percentage}% average confidence using PaddleOCR"
            )
            
            return result_dict
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PDF with PaddleOCR: {str(e)}, trying fallback")
            return self._extract_with_pypdf_fallback(file_path)
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from a single image (supporting method for individual pages)
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dict with extracted text and confidence
        """
        try:
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            result = self.ocr.ocr(image_path, cls=True)
            
            if not result or len(result) == 0 or not result[0]:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'lines': [],
                    'error': 'No text could be extracted from the image'
                }
            
            text_lines = []
            confidences = []
            
            for line_data in result[0]:
                bbox, (text, confidence) = line_data
                text_lines.append(text)
                confidences.append(confidence)
            
            full_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'text': full_text,
                'confidence': round(avg_confidence, 4),
                'confidence_percentage': int(avg_confidence * 100),
                'lines': [{'text': t, 'confidence': c} for t, c in zip(text_lines, confidences)],
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}")
            raise


def get_ocr_extractor() -> PaddleOCRExtractor:
    """
    Get or create PaddleOCR extractor instance (singleton)
    Returns successfully even if PaddleOCR initialization fails (uses pypdf fallback)
    
    Returns:
        PaddleOCRExtractor: Initialized extractor with PaddleOCR or pypdf fallback
    """
    if not hasattr(get_ocr_extractor, "_instance"):
        get_ocr_extractor._instance = PaddleOCRExtractor()
    
    return get_ocr_extractor._instance
