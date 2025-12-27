from agent.chess_api import update_fen, get_best_move as api_get_best_move
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
import chess
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import os
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# Load environment variables from .env file
load_dotenv()

# Configure OpenAI client based on USE_VSE_GPT setting
USE_VSE_GPT = os.getenv("USE_VSE_GPT", "False").lower() in ("true", "1", "yes")

if USE_VSE_GPT:
    # Use VSE GPT API
    OPENAI_API_KEY = os.getenv("VSE_GPT_API_KEY")
    OPENAI_BASE_URL = "https://api.vsegpt.ru/v1"
else:
    # Use standard OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = None  # Use default OpenAI base URL


class ChessState(TypedDict):
    messages: Annotated[list, add_messages]
    current_position: str  # FEN or None if no game


@tool
async def tool_get_best_move(fen: str) -> str:
    """
    Get the best move for the current position using Stockfish analysis. Use this tool to decide your next move.
    fen is the FEN-string representing the current position. FEN Format is as follows:
    <format>
    A FEN string has 6 fields, separated by spaces:

    <Piece placement> <Side to move> <Castling rights> <En passant> <Halfmove clock> <Fullmove number>

    1. Piece placement
    Describes the board rank by rank (8 → 1), using:
    * Uppercase = White pieces
    * Lowercase = Black pieces
    * r n b q k p = rook, knight, bishop, queen, king, pawn
    * Numbers = empty squares

    2. Side to move
    * w = White
    * b = Black

    3. Castling availability
    * K = White kingside
    * Q = White queenside
    * k = Black kingside
    * q = Black queenside
    *- = none

    4. En passant target square
    * Square like e3, or - if not available

    5. Halfmove clock
    * Number of halfmoves since the last pawn move or capture (used for the 50-move rule)

    6. Fullmove number
    * Starts at 1 and increments after Black’s move

    Example: Starting position
    rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    </format>

    Args:
        fen: FEN string representing the current chess position after the user's move.
    
    Returns:
        Best move in UCI notation (e.g., 'e2e4')
    """
    move = await api_get_best_move(fen=fen)
    return move

@tool
async def tool_register_user_move(move: str) -> str:
    """
    Register the user's move and update the current position.
    The move must be in UCI (Universal Chess Interface) format:
    exactly one lowercase string of the form <from><to>[promotion],
    where squares are file a–h + rank 1–8 (e.g., e2e4).
    Promotions must include the promotion piece (q, r, b, or n),
    e.g., e7e8q. Do not include spaces, piece letters, captures,
    check/mate symbols, or any extra text.
    Castling is represented as a king move:
    - White kingside: e1g1
    - White queenside: e1c1
    - Black kingside: e8g8
    - Black queenside: e8c8
    
    Args:
        move: A single legal chess move in UCI notation (e.g., "e2e4", "e1g1", "e7e8q")

    Returns:
        The move that was registered
    """
    return move

@tool
async def tool_make_move(move: str) -> str:
    """
    Make the agent's move and update the current position.
    The move must be in UCI (Universal Chess Interface) format:
    exactly one lowercase string of the form <from><to>[promotion],
    where squares are file a–h + rank 1–8 (e.g., e2e4).
    Promotions must include the promotion piece (q, r, b, or n),
    e.g., e7e8q. Do not include spaces, piece letters, captures,
    check/mate symbols, or any extra text.
    Castling is represented as a king move:
    - White kingside: e1g1
    - White queenside: e1c1
    - Black kingside: e8g8
    - Black queenside: e8c8
    
    Args:
        move: A single legal chess move in UCI notation (e.g., "e2e4", "e1g1", "e7e8q")
    
    Returns:
        The move that was made
    """
    return move

def validate_move(move: str, current_position: str) -> tuple[bool, str]:
    """
    Validate if a move is legal in the given position.
    
    Args:
        move: Move in UCI notation (e.g., 'e2e4')
        current_position: FEN string representing the current position
    
    Returns:
        Tuple of (is_valid, message):
        - If valid: (True, move)
        - If invalid: (False, error_message)
    """
    try:
        board = chess.Board(current_position)
        chess_move = chess.Move.from_uci(move)
        
        if chess_move not in board.legal_moves:
            # Move is illegal - generate helpful error message
            legal_moves_list = list(board.legal_moves)
            legal_moves_str = ", ".join([m.uci() for m in legal_moves_list[:10]])
            if len(legal_moves_list) > 10:
                legal_moves_str += ", ..."
            
            error_msg = (f"ERROR: Illegal move '{move}' in position {current_position}. "
                       f"Legal moves include: {legal_moves_str}")
            return False, error_msg
        
        # Move is legal
        return True, move
        
    except ValueError as e:
        # Invalid move format
        error_msg = f"ERROR: Invalid move format '{move}': {str(e)}"
        return False, error_msg

# Custom tools node that also updates position
async def tools_node(state: ChessState):
    """Execute tools and update position for move tools."""
    logger.debug("Executing tools node")
    # Execute the tools
    tool_executor = ToolNode([tool_get_best_move, tool_register_user_move, tool_make_move])
    result = await tool_executor.ainvoke(state)
    logger.debug(f"Tools node result: {result}")

    # Update position based on new tool messages
    current_position = state["current_position"]
    # ToolNode returns only the new tool response messages
    new_messages = result["messages"]
    
    for msg in new_messages:
        if msg.type == "tool":
            tool_name = msg.name if hasattr(msg, 'name') else None
            # Only update position for move tools
            if tool_name in ["tool_register_user_move", "tool_make_move"]:
                move = msg.content
                if current_position is None:
                    current_position = chess.STARTING_FEN
                
                # Validate the move before updating position
                is_valid, result_msg = validate_move(move, current_position)
                
                if not is_valid:
                    # Replace tool response with error message
                    msg.content = result_msg
                    logger.warning(f"Tool {tool_name} attempted illegal move: {move}")
                else:
                    # Move is valid - update position
                    current_position = update_fen(current_position, move)
                    logger.debug(f"Updated position after {tool_name}: {current_position}")
    
    return {
        "messages": new_messages,
        "current_position": current_position,
    }


# Initialize LLM with appropriate configuration
if OPENAI_BASE_URL:
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )
else:
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=OPENAI_API_KEY
    )

llm_with_tools = llm.bind_tools([
    tool_get_best_move,
    tool_register_user_move,
    tool_make_move,
])

async def agent_node(state: ChessState):
    logger.debug("Agent node starts")
    logger.debug(f"Agent node state: {state}")
    
    # Prepare messages with current position context
    messages = state["messages"].copy()
    
    # Add current position to the context if available
    current_position = state.get("current_position")
    # Insert position info after system message but before other messages
    position_msg = SystemMessage(
        content=f"Current board position (FEN): {{\"fen\": \"{current_position}\"}}\n"
                f"Use this FEN when calling tool_get_best_move."
    )

    messages = messages + [position_msg]  # after the system message

    logger.debug(f"LLM input messages: {messages}")

    response = await llm_with_tools.ainvoke(messages)
    logger.debug(f"Agent node response: {response}")
    return {
        "messages": [response]
    }

def should_continue(state: ChessState):
    """Determine if we should continue to tools or end."""
    last_message = state["messages"][-1]
    # If there are tool calls, continue to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise, end the graph
    return END


builder = StateGraph(ChessState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tools_node)

# Add conditional edge from agent
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)
# After tools, go back to agent
builder.add_edge("tools", "agent")
builder.set_entry_point("agent")

graph = builder.compile()
