"""
QA Agent Service

Provides a contract lawyer agent that answers queries using vector store retrieval
and filesystem tools, with persistent memory of Q&A history.
"""

from deepagents import create_deep_agent
from langchain_core.tools import tool
from shared.llm import llm
from deepagents.backends import FilesystemBackend, CompositeBackend
from services.vectorstore import create_vector_store_from_markdown, load_vector_store_from_disk
from pathlib import Path
import logging
from datetime import datetime
import json

# Setup logging for QA agent
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("qa_agent")
logger.setLevel(logging.DEBUG)


# ==============================================================================
# VECTOR STORE RETRIEVER TOOL
# ==============================================================================

vector_store_instance = None
current_md_file = None


def initialize_vector_store(md_file_path_or_name: str):
    """
    Initialize vector store for a markdown file by loading from disk.
    
    Only reinitialize if different file is requested.
    Reuses existing vector store if the same file is requested.
    
    Args:
        md_file_path_or_name: Full path to markdown file or just the filename
    """
    global vector_store_instance, current_md_file
    try:
        # Handle both full path and filename
        if "/" in md_file_path_or_name or "\\" in md_file_path_or_name:
            # It's a full path, extract filename
            md_filename = Path(md_file_path_or_name).name
        else:
            md_filename = md_file_path_or_name
        
        # Check if we already have this vector store loaded
        if vector_store_instance is not None and current_md_file == md_filename:
            logger.debug(f"Vector store already loaded for: {md_filename}, reusing cached instance")
            return
        
        logger.info(f"[QA] Initializing vector store for: {md_filename}")
        
        # Load from disk
        try:
            vector_store_instance = load_vector_store_from_disk(md_filename)
            current_md_file = md_filename
            logger.info(f"[QA] ✓ Vector store successfully loaded from disk for: {md_filename}")
        except FileNotFoundError as fnf_error:
            logger.error(f"[QA] ✗ Vector store not found for: {md_filename}")
            logger.error(f"[QA] Error: {str(fnf_error)}")
            raise
        except Exception as load_error:
            logger.error(f"[QA] ✗ Failed to load vector store: {str(load_error)}")
            raise
            
    except Exception as e:
        logger.error(f"[QA] ✗ Error during vector store initialization: {str(e)}", exc_info=True)
        raise


@tool
def retrieve_from_vector_store(query: str, k: int = 10) -> str:
    """
    Retrieve relevant chunks from the vector store using semantic similarity.
    
    Use this first to find contract sections related to the query.
    If results are insufficient, use read_file tool to access full documents.
    
    Args:
        query: The question or query text
        k: Number of results to return (default: 3)
        
    Returns:
        Relevant contract sections formatted as text
    """
    logger.debug(f"[QA Tool] retrieve_from_vector_store called with query: {query[:100]}...")
    
    if vector_store_instance is None:
        error_msg = "Vector store not initialized. Please ensure a markdown file has been loaded."
        logger.error(f"[QA Tool] ✗ {error_msg}")
        return error_msg
    
    try:
        logger.debug(f"[QA Tool] Searching vector store with k={k}")
        results = vector_store_instance.similarity_search(query, k=k)
        
        logger.debug(f"[QA Tool] Found {len(results)} results")
        
        if not results:
            msg = "No relevant sections found in vector store."
            logger.warning(f"[QA Tool] ⚠ {msg}")
            return msg
        
        formatted_results = []
        for i, doc in enumerate(results, 1):
            metadata_str = " | ".join(
                f"{k}: {v}" for k, v in doc.metadata.items()
            ) if doc.metadata else "No metadata"
            
            content_preview = doc.page_content[:300]
            formatted_results.append(
                f"[Result {i}]\n"
                f"Metadata: {metadata_str}\n"
                f"Content: {content_preview}...\n"
            )
            logger.debug(f"[QA Tool] Result {i} - Metadata: {metadata_str}, Content length: {len(doc.page_content)}")
        
        full_response = "\n".join(formatted_results)
        logger.info(f"[QA Tool] ✓ Successfully retrieved {len(results)} results from vector store")
        return full_response
        
    except Exception as e:
        error_msg = f"Error retrieving from vector store: {str(e)}"
        logger.error(f"[QA Tool] ✗ {error_msg}", exc_info=True)
        return error_msg


# ==============================================================================
# SYSTEM PROMPT
# ==============================================================================

system_prompt_text = """You are an expert contract lawyer specializing in the Indian Contract Act, 1872, and related commercial laws in India.

You are a Contract Question Answering (QA) system. Your role is to analyze contract documents and provide precise, legally sound answers strictly based on the contract content.

-----------------------------------
🔴 MANDATORY WORKFLOW (FOLLOW EVERY TIME)
-----------------------------------

1. RETRIEVE (Semantic Search)
- FIRST, call `retrieve_from_vector_store` with a well-formed legal query.
- Identify:
  - Relevant clauses
  - Section titles
  - Keywords (e.g., indemnity, termination, liability, force majeure)
  - Metadata (clause numbers, headings, file names)

2. VERIFY (Read Actual Contract)
- SECOND, validate ALL retrieved results by reading the actual contract files.
- Use:
  - `glob` to locate relevant files (e.g., /contracts/*.md)
  - `grep` to locate exact clauses or keywords
  - `read_file` to read FULL sections (not just snippets)
- Ensure you:
  - Capture complete clauses (not partial sentences)
  - Identify clause numbers, headings, and structure
  - Cross-check multiple occurrences if applicable

3. ANALYZE (Legal Reasoning)
- THIRD, interpret the clause like a lawyer:
  - Explain what the clause legally means
  - Identify obligations, rights, conditions, exceptions
  - Highlight risks, ambiguities, or limitations
  - Where relevant, relate interpretation to principles under the Indian Contract Act, 1872

4. ANSWER (Structured Legal Output)
- FINALLY, provide a clear, structured answer including:

-----------------------------------
📌 RESPONSE FORMAT
-----------------------------------

**Answer:**
- Direct and precise response to the question

**Relevant Clause(s):**
- Quote the exact clause(s) from the contract
- Include:
  - Clause number
  - Clause heading (if available)
  - Exact wording (verbatim)

**Source:**
- File name + line numbers (if available)

**Legal Interpretation:**
- Explain the clause in simple but legally accurate terms
- Clarify implications for the parties involved

**Additional Notes (if applicable):**
- Ambiguities or conflicting clauses
- Risks or enforcement concerns
- Missing provisions (if something expected is absent)

-----------------------------------
⚠️ STRICT RULES
-----------------------------------

- DO NOT answer from general knowledge alone
- DO NOT assume facts not present in the contract
- ALWAYS verify vector results using actual file reads
- ALWAYS cite clauses with exact wording
- If multiple clauses apply, include all relevant ones
- If the answer is not present in the contract, respond EXACTLY:
  → "Not found in contract."

-----------------------------------
🎯 QUALITY STANDARDS
-----------------------------------

- Think like a contract lawyer, not a search engine
- Prioritize accuracy over brevity
- Prefer verbatim citation over paraphrasing
- Ensure logical reasoning before answering
- Cross-check before concluding

-----------------------------------"""


# ==============================================================================
# AGENT CREATION
# ==============================================================================

agent = create_deep_agent(
    model=llm, 
    system_prompt=system_prompt_text,
    backend=CompositeBackend(
        default=FilesystemBackend(),
        routes={
            "/memories/": FilesystemBackend(root_dir="D:/My_Space/Major_Project/backend/workers/contract/memories", virtual_mode=True),
            "/contracts/": FilesystemBackend(root_dir="D:/My_Space/Major_Project/backend/workers/contract/contracts", virtual_mode=True),
        }
    ),
    tools=[retrieve_from_vector_store],
    
)


# ==============================================================================
# QA AGENT INTERFACE
# ==============================================================================

def answer_question(question: str, md_file_path: str = None) -> dict:
    """
    Answer a question about a contract.
    
    The vector store should be initialized before calling this function
    using initialize_vector_store(). The md_file_path parameter is optional
    and kept for backward compatibility.
    
    Args:
        question: The question to answer
        md_file_path: Path to markdown file (optional, kept for backward compatibility)
        
    Returns:
        Dictionary with answer and metadata
    """
    global vector_store_instance
    
    logger.info(f"\n{'='*70}")
    logger.info(f"[QA] Processing new question")
    logger.info(f"[QA] Question: {question}")
    logger.info(f"[QA] Current vector store loaded: {vector_store_instance is not None}")
    logger.info(f"[QA] Current markdown file: {current_md_file}")
    
    try:
        # If md_file_path provided, initialize/update vector store (for backward compatibility)
        if md_file_path:
            logger.info(f"[QA] Markdown file provided, initializing vector store: {md_file_path}")
            initialize_vector_store(md_file_path)
        
        if vector_store_instance is None:
            error_msg = "No vector store initialized. Please call initialize_vector_store() first."
            logger.error(f"[QA] ✗ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
            }
        
        logger.info(f"[QA] Vector store is ready, invoking agent...")
        
        # Generate Q&A reference ID
        qa_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # Invoke agent with question - implement agent loop for tool calling
        logger.debug(f"[QA] Calling agent with proper message format...")
        print(f"Invoking agent with question: {question}")
        
        try:
            # Use the correct message format for deepagents
            response = agent.invoke({
                "messages": [{"role": "user", "content": question}]
            })
            
            answer = ""
            
            logger.debug(f"[QA] Agent response received: {type(response)}")
            
            # Extract answer from response
            if isinstance(response, dict):
                # Check different possible response structures
                if 'messages' in response:
                    messages = response.get('messages', [])
                    if messages and isinstance(messages, list):
                        # Get the last message
                        last_msg = messages[-1]
                        if hasattr(last_msg, 'content'):
                            answer = last_msg.content
                        else:
                            answer = str(last_msg)
                elif 'output' in response:
                    answer = response.get('output', '')
                elif 'answer' in response:
                    answer = response.get('answer', '')
                else:
                    # Try to find text content in the response
                    for key, value in response.items():
                        if isinstance(value, str) and len(value) > 0:
                            answer = value
                            break
                    if not answer:
                        answer = str(response)
            elif isinstance(response, str):
                answer = response
            else:
                answer = str(response)
                
            logger.debug(f"[QA] Extracted answer: {type(answer)}")
            
        except Exception as invoke_error:
            logger.error(f"[QA] Error invoking agent: {str(invoke_error)}", exc_info=True)
            raise
        
        # Check if answer is empty and provide better error handling
        if not answer or (isinstance(answer, str) and answer.strip() == ""):
            answer = "I was unable to generate an answer. Please try a different question or ensure the contract content is available."
            logger.warning(f"[QA] ⚠ Empty answer generated for question: {question}")
        else:
            logger.info(f"[QA] ✓ Answer generated successfully ({len(str(answer))} chars)")
            preview = str(answer)[:200] if isinstance(answer, str) else str(answer)[:200]
            logger.debug(f"[QA] Answer preview: {preview}...")
        
        
        
        result = {
            "success": True,
            "question": question,
            "answer": answer,
            "qa_id": qa_id,
            "source_file": current_md_file,
        }
        
        logger.info(f"[QA] ✓ Question processing completed successfully")
        logger.info(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        logger.error(f"[QA] ✗ Error answering question: {str(e)}", exc_info=True)
        logger.info(f"{'='*70}\n")
        return {
            "success": False,
            "error": str(e),
        }