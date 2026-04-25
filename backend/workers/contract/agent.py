from deepagents import create_deep_agent
from shared.llm import llm
from deepagents.backends import FilesystemBackend, CompositeBackend
from pathlib import Path
import logging
import sys
import time


# ==============================================================================
# LOGGING SETUP
# ==============================================================================
# Configure detailed logging to capture all agent thinking and operations

def setup_logging(log_file: str = None):
    """Setup comprehensive logging for agent operations."""
    
    # Create logger
    logger = logging.getLogger("contract_agent")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler - detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler - if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    # Also log LangChain components
    logging.getLogger("langchain").setLevel(logging.DEBUG)
    logging.getLogger("langchain_core").setLevel(logging.DEBUG)
    logging.getLogger("deepagents").setLevel(logging.DEBUG)
    
    return logger

# Setup logging at module import time
logger = setup_logging()

system_prompt_text = """You are an expert contract lawyer with deep knowledge of Indian Contract Act.

## WORKFLOW

1. **Understand Contract Type**: Read the contract briefly to identify its type (Supply Agreement, RFP, Service Agreement, etc.)

2. **Extract Indian Contract Act Requirements**: Use the act_extractor subagent to identify relevant Indian Contract Act sections for this contract type.

3. **Analyze Contract Details**: Use the file_analyzer subagent to read the complete contract and identify:
   - Key clauses and obligations
   - Risks and red flags
   - Missing clauses
   - Green flags (protective clauses)
   - Financial terms

4. **Generate Final Report**: Create a comprehensive markdown analysis at `/memories/{contract_type}_final_analysis.md` with:
   - Contract classification
   - Parties and obligations
   - Applicable Act sections
   - Risk assessment (HIGH/MEDIUM/LOW)
   - Red and green flags
   - Missing clauses
   - Top recommendations
   - Overall assessment

## SUBAGENTS

- **act_extractor**: Extracts relevant Indian Contract Act sections for the contract type
- **file_analyzer**: Reads and analyzes contract files, identifies risks, clauses, obligations

Use filesystem tools with virtual paths: /contracts/, /memories/, /skills/
"""


# ==============================================================================
# PATH MAPPING SETUP
# ==============================================================================
# Map Windows filesystem paths to virtual paths
# This allows the agent to access files at their actual Windows locations
# while using virtual paths in the tools

current_dir = Path(__file__).parent
contracts_dir = current_dir / "contracts"
memories_dir = current_dir / "memories"

# Ensure directories exist
contracts_dir.mkdir(parents=True, exist_ok=True)
memories_dir.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# AGENT CONFIGURATION
# ==============================================================================

# Define subagents for specialized tasks
subagents = [
    {
        "name": "act_extractor",
        "description": "Extracts relevant Indian Contract Act sections for the given contract type. Identifies which sections apply and saves requirements to /memories/act_requirements.md",
        "system_prompt": """You are an Indian Contract Act expert. Your role is to:
1. Identify relevant Indian Contract Act sections for the given contract type
2. Explain how each section applies
3. List key requirements from each section
4. Save findings to /memories/act_requirements.md

Be concise and cite specific sections.""",
    },
    {
        "name": "file_analyzer",
        "description": "Analyzes contract files to identify clauses, risks, obligations, and missing provisions. Saves detailed findings to /memories/contract_analysis.md",
        "system_prompt": """You are a contract analysis specialist. Your role is to:
1. Read the complete contract
2. Identify key clauses and obligations for each party
3. Flag risks and red flags with Act section references
4. Identify protective clauses (green flags)
5. List missing clauses that should be present
6. Extract financial terms
7. Save comprehensive findings to /memories/contract_analysis.md

Be thorough and cite specific line numbers or clause references.""",
    },
]

agent = create_deep_agent(
    model=llm,
    system_prompt=system_prompt_text,
    backend=CompositeBackend(
        default=FilesystemBackend(),
        routes={
            "/memories/": FilesystemBackend(root_dir=str(memories_dir), virtual_mode=True),
            "/contracts/": FilesystemBackend(root_dir=str(contracts_dir), virtual_mode=True),
        }
    ),
    skills=["./skills"],
    subagents=subagents,
)

# 
# ==============================================================================
# STREAMING HELPERS
# ==============================================================================

def stream_agent_with_logging(
    user_message: str,
    log_file: str = None,
    stream_mode: list = None
) -> dict:
    """
    Stream agent execution with logging.
    
    Args:
        user_message: The input message for the agent
        log_file: Optional file path to save streaming log
        stream_mode: Stream modes to use (default: ["updates", "messages"])
        
    Returns:
        Dictionary with execution status
    """
    if stream_mode is None:
        stream_mode = ["updates", "messages"]
    
    logger_instance = logging.getLogger("contract_agent")
    logger_instance.info(f"Starting contract analysis...")
    
    try:
        # Stream agent execution
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=stream_mode,
            subgraphs=True,
            version="v2",
        ):
            chunk_type = chunk.get("type")
            chunk_data = chunk.get("data")
            
            # Log updates (execution steps)
            if chunk_type == "updates":
                for node_name, node_data in chunk_data.items():
                    logger_instance.info(f"Step: {node_name}")
            
            # Log messages (thinking and tool calls)
            elif chunk_type == "messages":
                token, metadata = chunk_data
                
                # Log tool calls
                if hasattr(token, "tool_call_chunks") and token.tool_call_chunks:
                    for tc in token.tool_call_chunks:
                        if tc.get("name"):
                            logger_instance.info(f"Tool: {tc['name']}")
                
                # Log AI thinking/responses
                if token.type == "ai" and token.content:
                    print(token.content, end="", flush=True)
    
    except Exception as e:
        logger_instance.error(f"Error during streaming: {str(e)}", exc_info=True)
        raise
    
    logger_instance.info("Contract analysis complete")
    
    return {"status": "completed"}


# Export for use in tasks
__all__ = ["agent", "stream_agent_with_logging", "logger", "setup_logging"]