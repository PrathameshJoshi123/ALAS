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

system_prompt_text = """You are an expert contract lawyer with deep knowledge of Indian Contract Act, 1872.
You are a contract QA system designed to answer questions about contracts.

CRITICAL: Your mandatory workflow for EVERY question:

1. FIRST: Call retrieve_from_vector_store with your search query
   - Get the semantic search results from the vector store
   - Note the metadata and relevant sections returned

2. THEN: Read the actual contract files to verify and get full context
   - Use read_file tool to access files in /contracts/ directory
   - Use glob patterns to find relevant contract files (e.g., india_contract.md)
   - Use grep patterns to find specific sections within files
   - Read the full sections that relate to the vector store results

3. FINALLY: Provide your answer based on actual contract content
   - Combine vector store insights with direct file reading
   - Cite specific sections from the contract with line references
   - Cross-verify information from multiple sources if needed

Available tools:
- retrieve_from_vector_store: Semantic search for relevant contract sections
- read_file: Read file contents from /contracts/ and other directories
- write_file: Write files to memory or logs if needed
- glob: Find files matching patterns
- grep: Search for text patterns within files

IMPORTANT:
- Always verify vector store results by reading the actual files
- Use read_file to get the complete context around search results
- Don't answer from general knowledge - rely only on contract content
- Always cite sources with specific section references
- If files don't contain the answer, say: "Not found in contract."
- Provide thorough, detailed answers based on actual contract text"""


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
        
        # Store Q&A in memory
        try:
            qa_entry = {
                "id": qa_id,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "source_file": current_md_file,
            }
            
            logger.debug(f"[QA] Storing Q&A in memory with ID: {qa_id}")
            
            # Create Q&A record - simplified approach
            qa_filename = f"qa_{qa_id}.md"
            qa_content = f"""# Q&A Record

**ID**: {qa_id}
**Timestamp**: {qa_entry['timestamp']}
**Source File**: {current_md_file}

## Question
{question}

## Answer
{answer}
"""
            
            # Attempt to write to memory (don't fail if this doesn't work)
            try:
                agent.invoke({
                    "input": f"Write this Q&A to memory: {qa_filename}: {qa_content}"
                })
                logger.info(f"[QA] ✓ Q&A stored in memory with ID: {qa_id}")
            except Exception as mem_error:
                logger.warning(f"[QA] ⚠ Failed to store Q&A in memory: {str(mem_error)}")
            
        except Exception as e:
            logger.warning(f"[QA] ⚠ Error during Q&A storage: {str(e)}", exc_info=True)
        
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