from datetime import datetime, timedelta
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ddgs import DDGS
from sqlalchemy.orm import Session
from uuid import uuid4
import logging

from shared.database.models import LegalWebSearch

logger = logging.getLogger(__name__)

# Cache TTL: 30 days by default for general searches, 90 days for statute caches
CACHE_TTL_DAYS = 30
STATUTE_CACHE_TTL_DAYS = 90

# India Code website - official source for Indian laws
INDIA_CODE_DOMAIN = "indiacode.nic.in"


def search_and_cache(db: Session, tenant_id, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Run a DDGS text search and cache results in the database.

    Args:
        db: SQLAlchemy session
        tenant_id: Tenant UUID
        query: Search query string
        max_results: Number of results to return

    Returns:
        List of result dicts (as returned by DDGS.text)
    """
    # Try to find a cached result within TTL
    cutoff = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS)
    existing = db.query(LegalWebSearch).filter(
        LegalWebSearch.tenant_id == tenant_id,
        LegalWebSearch.query == query,
        LegalWebSearch.created_at >= cutoff
    ).order_by(LegalWebSearch.created_at.desc()).first()

    if existing:
        try:
            return existing.results
        except Exception:
            pass

    # Not cached: perform DDGS search
    ddgs = DDGS()
    try:
        results = ddgs.text(query, max_results=max_results)
    except Exception as e:
        logger.error(f"DDGS search failed: {str(e)}")
        # Fallback to empty list on network / library error
        results = []

    # Persist cache entry (best-effort)
    try:
        entry = LegalWebSearch(
            id=uuid4(),
            tenant_id=tenant_id,
            query=query,
            results=results,
            source="ddgs",
            created_at=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to cache search results: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass

    return results


def search_india_code(db: Session, tenant_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search Indian laws from indiacode.nic.in - the official government source.
    
    This function specifically restricts searches to the India Code website
    to ensure legal accuracy and prevent reliance on third-party interpretations.
    
    Args:
        db: SQLAlchemy session
        tenant_id: Tenant UUID
        query: Search query (e.g., "Indian Contract Act 1872 section 73")
        max_results: Maximum results to return (default 5)
    
    Returns:
        List of result dicts filtered for indiacode.nic.in results only
        Each result contains:
        - 'title': Act name and relevant section
        - 'href': Direct link to indiacode.nic.in
        - 'body': Brief description or statute excerpt
        - 'source': Always 'indiacode.nic.in'
    """
    # Check cache first (longer TTL for statute caches)
    cache_key = f"india_code_{query}"
    cutoff = datetime.utcnow() - timedelta(days=STATUTE_CACHE_TTL_DAYS)
    
    try:
        cached = db.query(LegalWebSearch).filter(
            LegalWebSearch.tenant_id == tenant_id,
            LegalWebSearch.query == cache_key,
            LegalWebSearch.created_at >= cutoff
        ).order_by(LegalWebSearch.created_at.desc()).first()
        
        if cached and cached.results:
            logger.info(f"Returning cached India Code results for: {query}")
            return cached.results
    except Exception as e:
        logger.warning(f"Cache lookup failed: {str(e)}")

    # Construct search query with India Code domain restriction
    search_query = f"site:{INDIA_CODE_DOMAIN} {query}"
    
    logger.info(f"Searching India Code for: {query}")
    
    # Perform DDGS search restricted to indiacode.nic.in
    ddgs = DDGS()
    results = []
    
    try:
        all_results = ddgs.text(search_query, max_results=max_results * 2)  # Get more to filter
        
        # Filter results to ensure they're from indiacode.nic.in
        for result in all_results:
            href = result.get('href', '')
            if INDIA_CODE_DOMAIN in href.lower():
                # Ensure only official NIC domain results
                results.append({
                    'title': result.get('title', ''),
                    'href': href,
                    'body': result.get('body', ''),
                    'source': 'indiacode.nic.in'
                })
                if len(results) >= max_results:
                    break
        
        if not results:
            logger.warning(f"No indiacode.nic.in results found for: {query}")
    
    except Exception as e:
        logger.error(f"India Code search failed: {str(e)}")
        return []

    # Cache the India Code results with longer TTL
    try:
        cache_entry = LegalWebSearch(
            id=uuid4(),
            tenant_id=tenant_id,
            query=cache_key,
            results=results,
            source="indiacode.nic.in",
            created_at=datetime.utcnow()
        )
        db.add(cache_entry)
        db.commit()
        logger.info(f"Cached India Code results: {len(results)} results for '{query}'")
    except Exception as e:
        logger.error(f"Failed to cache India Code results: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass

    return results


def search_statute_section(
    db: Session, 
    tenant_id: str, 
    act_name: str, 
    year: str, 
    section_number: Optional[str] = None,
    chapter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for a specific statute section from Indian law.
    
    Example:
        search_statute_section(db, tenant_id, 
                             act_name="Indian Contract Act",
                             year="1872",
                             section_number="73")
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        act_name: Name of the Act (e.g., "Indian Contract Act")
        year: Year of the Act (e.g., "1872")
        section_number: Optional specific section (e.g., "73")
        chapter: Optional chapter reference
    
    Returns:
        Dict containing:
        - 'found': Boolean indicating if statute was found
        - 'act': Full act name with year
        - 'sections': List of matching section results
        - 'url': Direct link to statute
        - 'raw_text': Statute text if retrievable
        - 'source': Always 'indiacode.nic.in'
    """
    # Build query
    query_parts = [act_name, year]
    if section_number:
        query_parts.append(f"section {section_number}")
    if chapter:
        query_parts.append(f"chapter {chapter}")
    
    query = " ".join(query_parts)
    
    logger.info(f"Searching for statute: {query}")
    
    # Search India Code
    results = search_india_code(db, tenant_id, query, max_results=3)
    
    if not results:
        return {
            'found': False,
            'act': f"{act_name}, {year}",
            'sections': [],
            'url': None,
            'raw_text': None,
            'source': 'indiacode.nic.in',
            'error': f"No results found for {act_name}, {year}"
        }
    
    # Return the primary result with metadata
    primary_result = results[0]
    
    return {
        'found': True,
        'act': f"{act_name}, {year}",
        'sections': [s.get('body', '') for s in results],
        'url': primary_result.get('href'),
        'raw_text': primary_result.get('body', ''),
        'source': 'indiacode.nic.in',
        'title': primary_result.get('title', '')
    }


def validate_india_code_url(url: str) -> bool:
    """
    Validate that a URL is from the official indiacode.nic.in domain.
    
    Args:
        url: URL to validate
    
    Returns:
        True if URL is from indiacode.nic.in, False otherwise
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return INDIA_CODE_DOMAIN in domain


def extract_section_number_from_text(text: str) -> Optional[List[str]]:
    """
    Extract section numbers from statute text.
    Pattern: "Section XXX" or "Sec. XXX"
    
    Args:
        text: Text to search for section numbers
    
    Returns:
        List of section numbers found, or None if none found
    """
    # Match patterns like "Section 73", "Sec. 28", "section 50-55"
    pattern = r'(?:Section|Sec\.?\s+)(\d+(?:-\d+)?)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches if matches else None


def extract_act_and_section(text: str) -> Optional[Tuple[str, str]]:
    """
    Extract Act name and section from contract clause text.
    
    Examples:
    - "As per Section 73 of Indian Contract Act, 1872"
    - "in compliance with Section 37 of Copyright Act, 1957"
    
    Args:
        text: Text to analyze
    
    Returns:
        Tuple of (act_name, section_number) or None if not found
    """
    # Pattern: "Section XXX of [Act Name], YYYY"
    pattern = r'Section\s+(\d+)\s+of\s+(.+?),\s+(\d{4})'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        section = match.group(1)
        act_base = match.group(2)
        year = match.group(3)
        return (f"{act_base}, {year}", section)
    
    return None
