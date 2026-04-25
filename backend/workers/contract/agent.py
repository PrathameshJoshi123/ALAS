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

system_prompt_text = """You are an expert contract lawyer with deep knowledge of the Indian Contract Act.

You must analyze contracts in a **chunked, memory-driven workflow** to ensure no detail is missed.

All files are in markdown (.md).

---

## CORE WORKFLOW

### STEP 1: Identify Contract Type
- Read the beginning of the contract (first 300 lines).
- Classify the contract type (e.g., Supply Agreement, Service Agreement, NDA, Employment Contract, etc.).

---

### STEP 2: Iterative File Reading (MANDATORY)

You MUST read the contract in chunks using the `read_file` tool with:
- `offset` (starting line)
- `limit = 300`

#### Process:
1. Start with offset = 0
2. Read 300 lines at a time
3. After each read:
   - Analyze the chunk
   - Extract **important findings dynamically**, including:
     - Key clauses
     - Obligations (party-wise)
     - Financial terms
     - Risks / red flags
     - Protective clauses (green flags)
     - Missing or vague terms
     - Legal inconsistencies
     - Any unusual or non-standard language

4. Write findings into a temporary memory file:
Use the `write_file` and `edit_file` tool to append findings to:
/memories/temp_analysis.md


5. IMPORTANT:
- Always **append**, never overwrite
- Structure each entry like:

## Chunk {start_line}-{end_line}
- Key Findings:
- Risks:
- Obligations:
- Notes:

6. Increase offset by 300 and repeat until end of file.

---

### STEP 3: Consolidate Learnings

After the full contract is read:

1. Read the complete file:

/memories/temp_analysis.md


2. Synthesize:
- Repeated risks
- Cross-clause conflicts
- Missing protections
- Overall contract structure

---

### STEP 4: Read Indian Contract Act Reference

You MUST read:

/contracts/indian_contract_law.md


Then:
- Identify relevant sections applicable to this contract
- Map contract clauses to legal provisions
- Highlight compliance gaps

---

### STEP 5: Final Report Generation

Create a final structured markdown report at:


/memories/final_analysis.md


---

## FINAL REPORT STRUCTURE

### 1. Contract Classification
- Type
- Nature
- Complexity level

### 2. Parties & Key Obligations
- Party A obligations
- Party B obligations

### 3. Financial & Commercial Terms
- Payment structure
- Penalties
- Liabilities

### 4. Applicable Indian Contract Act Sections
- Relevant sections
- Why they apply
- Compliance status

### 5. Risk Assessment
- Overall Risk: HIGH / MEDIUM / LOW
- Explanation

### 6. Red Flags
- Clearly explain legal and practical risks

### 7. Green Flags
- Protective clauses
- Strong legal safeguards

### 8. Missing Clauses
- Critical omissions
- Industry-standard expectations

### 9. Top Recommendations
- Actionable legal improvements
- Risk mitigation strategies

### 10. Overall Legal Assessment
- Enforceability
- Fairness
- Commercial soundness

---

## STRICT RULES

- NEVER read the full file at once
- ALWAYS use chunked reading (300 lines per call)
- ALWAYS append findings after each chunk
- DO NOT skip the temp analysis step
- DO NOT generate final report without reading:
  1. Full contract (via chunks)
  2. temp_analysis.md
  3. indian_contract_act.md

---

## GOAL

Act like a meticulous legal expert who:
- Reads carefully in parts
- Takes structured notes
- Thinks holistically at the end
- Produces a professional legal-grade analysis
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

    if stream_mode is None:
        stream_mode = ["updates", "messages", "custom"]

    logger_instance = logging.getLogger("contract_agent")
    logger_instance.info("Starting contract analysis...")

    current_source = None  # track main vs subagent
    mid_line = False       # for clean token streaming

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=stream_mode,
            subgraphs=True,
            version="v2",
        ):
            chunk_type = chunk["type"]
            ns = chunk["ns"]
            data = chunk["data"]

            # 🔍 Identify source (main vs subagent)
            is_subagent = any(s.startswith("tools:") for s in ns)
            source = (
                next((s for s in ns if s.startswith("tools:")), "main")
                if is_subagent else "main"
            )

            # =========================
            # 1. UPDATES (execution flow)
            # =========================
            if chunk_type == "updates":
                for node_name, node_data in data.items():

                    logger_instance.info(f"[{source}] step → {node_name}")

                    # 🔥 Deep inspect what's inside nodes
                    if node_name == "model_request":
                        msgs = node_data.get("messages", [])
                        for msg in msgs:
                            # Tool calls planned by model
                            for tc in getattr(msg, "tool_calls", []):
                                logger_instance.info(
                                    f"[{source}] 🧠 planning tool → {tc['name']} | args: {tc['args']}"
                                )

                    elif node_name == "tools":
                        msgs = node_data.get("messages", [])
                        for msg in msgs:
                            if msg.type == "tool":
                                logger_instance.info(
                                    f"[{source}] ✅ tool result → {msg.name}: {str(msg.content)[:200]}"
                                )

            # =========================
            # 2. MESSAGE STREAM (tokens, tool calls)
            # =========================
            elif chunk_type == "messages":
                token, metadata = data

                # 🧠 Tool call streaming (very important)
                if getattr(token, "tool_call_chunks", None):
                    for tc in token.tool_call_chunks:
                        if tc.get("name"):
                            logger_instance.info(
                                f"[{source}] 🔧 calling tool → {tc['name']}"
                            )
                        if tc.get("args"):
                            logger_instance.info(
                                f"[{source}]   ↳ args chunk → {tc['args']}"
                            )

                # ✅ Tool result messages
                if token.type == "tool":
                    logger_instance.info(
                        f"[{source}] 📦 tool output → {token.name}: {str(token.content)[:200]}"
                    )

                # 💬 LLM token streaming (actual thinking / output)
                if token.type == "ai" and token.content:
                    if source != current_source:
                        print(f"\n\n--- [{source}] ---\n", end="")
                        current_source = source

                    print(token.content, end="", flush=True)
                    mid_line = True

            # =========================
            # 3. CUSTOM EVENTS (if tools emit progress)
            # =========================
            elif chunk_type == "custom":
                logger_instance.info(f"[{source}] ⚡ custom event → {data}")

    except Exception as e:
        logger_instance.error(f"Error during streaming: {str(e)}", exc_info=True)
        raise

    logger_instance.info("Contract analysis complete")

    return {"status": "completed"}


# Export for use in tasks
__all__ = ["agent", "stream_agent_with_logging", "logger", "setup_logging"]