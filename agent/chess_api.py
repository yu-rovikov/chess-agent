"""
Chess-API.com integration module.

This module provides functions to interact with the Chess-API.com service,
which offers Stockfish 17 NNUE chess engine analysis via REST API.
"""

import json
from typing import Dict, Any, Optional, List
import aiohttp
import chess


class ChessAPIError(Exception):
    """Custom exception for Chess-API errors."""
    pass


async def analyze_position(
    fen: Optional[str] = None,
    input_text: Optional[str] = None,
    variants: int = 1,
    depth: int = 12,
    max_thinking_time: int = 50,
    searchmoves: str = "",
    api_url: str = "https://chess-api.com/v1"
) -> Dict[str, Any]:
    """
    Analyze a chess position using the Chess-API.
    
    Args:
        fen: FEN string representing the chess position
        input_text: Alternative to FEN - HTML/text input with list of moves
        variants: Number of variants to analyze (max: 5, default: 1)
        depth: Analysis depth (max: 18, default: 12)
            - depth 12 ≈ 2350 FIDE (IM level)
            - depth 18 ≈ 2750 FIDE (GM Nakamura level)
            - depth 20 ≈ 2850 FIDE (GM Carlsen level)
        max_thinking_time: Maximum thinking time in ms (max: 100, default: 50)
        searchmoves: Evaluate specific moves only, e.g., 'd2d4 e2e4'
        api_url: API endpoint URL
        
    Returns:
        Dictionary containing analysis results with fields:
        - text (str): Textual description of the move
        - eval (float): Position evaluation (negative = black winning)
        - move (str): Best move in UCI notation (e.g., 'e2e4')
        - fen (str): The analyzed position FEN
        - depth (int): Analysis depth reached
        - winChance (float): Winning percentage (50 = equal, >50 = white winning)
        - continuationArr (list): Array of continuation moves
        - mate (int|None): Forced mate in N moves (negative for black)
        - centipawns (str): Evaluation in centipawns
        - san (str): Move in short algebraic notation (e.g., 'e4')
        - lan (str): Move in long algebraic notation
        - turn (str): Current player's turn ('w' or 'b')
        - color (str): Color of the piece moved
        - piece (str): Piece type (p/n/b/r/q/k)
        - flags (str): Move flags (n/b/e/c/p/k/q)
        - isCapture (bool): Whether move is a capture
        - isCastling (bool): Whether move is castling
        - isPromotion (bool): Whether move is a promotion
        - from (str): Starting square (e.g., 'e2')
        - to (str): Destination square (e.g., 'e4')
        - fromNumeric (str): Starting square numeric
        - toNumeric (str): Destination square numeric
        - taskId (str): Task identifier
        - time (int): Calculation time in ms
        - type (str): Response type ('move', 'bestmove', 'info')
        
    Raises:
        ChessAPIError: If the API request fails
        ValueError: If neither fen nor input_text is provided or parameters are invalid
        
    Example:
        >>> result = await analyze_position(
        ...     fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        ...     depth=12
        ... )
        >>> print(f"Best move: {result['san']} (eval: {result['eval']})")
    """
    if not fen and not input_text:
        raise ValueError("Either 'fen' or 'input_text' must be provided")
    
    # Validate parameters
    if variants < 1 or variants > 5:
        raise ValueError("variants must be between 1 and 5")
    if depth < 1 or depth > 18:
        raise ValueError("depth must be between 1 and 18")
    if max_thinking_time < 1 or max_thinking_time > 100:
        raise ValueError("max_thinking_time must be between 1 and 100")
    
    # Build request payload
    payload: Dict[str, Any] = {
        "variants": variants,
        "depth": depth,
        "maxThinkingTime": max_thinking_time,
    }
    
    if fen:
        payload["fen"] = fen
    if input_text:
        payload["input"] = input_text
    if searchmoves:
        payload["searchmoves"] = searchmoves
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ChessAPIError(
                        f"API request failed with status {response.status}: {error_text}"
                    )
                
                result = await response.json()
                
                # Check if the API returned an error
                if isinstance(result, dict) and result.get("type") == "error":
                    error_msg = result.get("text", "Unknown error")
                    error_code = result.get("error", "UNKNOWN_ERROR")
                    raise ChessAPIError(f"API error ({error_code}): {error_msg}")
                
                return result
    except aiohttp.ClientError as e:
        raise ChessAPIError(f"Network error during API request: {str(e)}")
    except json.JSONDecodeError as e:
        raise ChessAPIError(f"Failed to parse API response: {str(e)}")


async def get_best_move(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> str:
    """
    Get the best move for a position.

    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Best move in UCI notation (e.g., 'e2e4')
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> move = await get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(move)  # e.g., 'e2e4'
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    return result.get("move", "")


async def get_best_move_san(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> str:
    """
    Get the best move in standard algebraic notation (SAN).
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Best move in SAN (e.g., 'e4', 'Nf3', 'O-O')
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> move = await get_best_move_san("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(move)  # e.g., 'e4'
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    return result.get("san", "")


async def get_position_evaluation(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> float:
    """
    Get the evaluation score for a position.
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Evaluation score (negative = black winning, positive = white winning)
        Example: -2.5 means black is winning by 2.5 pawns
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> eval_score = await get_position_evaluation("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(f"Evaluation: {eval_score}")  # e.g., 0.15
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    return result.get("eval", 0.0)


async def get_win_chance(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> float:
    """
    Get the winning chance percentage for the current position.
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Winning chance percentage (50 = equal, >50 = white winning, <50 = black winning)
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> win_pct = await get_win_chance("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(f"White's winning chance: {win_pct}%")  # e.g., 52.3%
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    return result.get("winChance", 50.0)


async def check_for_mate(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> Optional[int]:
    """
    Check if there's a forced mate sequence in the position.
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Number of moves to mate (positive = white mates, negative = black mates)
        None if no forced mate detected
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> mate_in = await check_for_mate("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
        >>> if mate_in:
        ...     print(f"Mate in {abs(mate_in)} moves")
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    mate_value = result.get("mate")
    # Convert to int if it's a string
    if mate_value is not None and isinstance(mate_value, str):
        try:
            mate_value = int(mate_value)
        except ValueError:
            mate_value = None
    return mate_value


async def get_continuation(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> List[str]:
    """
    Get the continuation line (sequence of best moves) from the position.
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        List of moves in UCI notation representing the best continuation
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> continuation = await get_continuation("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(" ".join(continuation))  # e.g., 'e2e4 e7e5 g1f3 b8c6'
    """
    result = await analyze_position(fen=fen, depth=depth, api_url=api_url)
    return result.get("continuationArr", [])


async def analyze_specific_moves(
    fen: str,
    moves: List[str],
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> Dict[str, Any]:
    """
    Analyze only specific moves from a position.
    
    Args:
        fen: FEN string representing the chess position
        moves: List of moves to analyze in UCI notation (e.g., ['e2e4', 'd2d4'])
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Analysis result focusing on the specified moves
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> result = await analyze_specific_moves(
        ...     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        ...     ["e2e4", "d2d4"]
        ... )
        >>> print(f"Best of specified moves: {result['san']}")
    """
    searchmoves = " ".join(moves)
    return await analyze_position(
        fen=fen,
        depth=depth,
        searchmoves=searchmoves,
        api_url=api_url
    )


async def get_full_analysis(
    fen: str,
    depth: int = 12,
    api_url: str = "https://chess-api.com/v1"
) -> Dict[str, Any]:
    """
    Get comprehensive analysis of a position including all available information.
    
    This is an alias for analyze_position with sensible defaults.
    
    Args:
        fen: FEN string representing the chess position
        depth: Analysis depth (max: 18, default: 12)
        api_url: API endpoint URL
        
    Returns:
        Complete analysis dictionary with all fields
        
    Raises:
        ChessAPIError: If the API request fails
        
    Example:
        >>> analysis = await get_full_analysis("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> print(f"Move: {analysis['san']}, Eval: {analysis['eval']}, Win%: {analysis['winChance']}")
    """
    return await analyze_position(fen=fen, depth=depth, api_url=api_url)


def decode_fen(fen: str) -> List[List[Optional[str]]]:
    """
    Decode a FEN string into an 8x8 board representation.
    
    Args:
        fen: FEN string representing the chess position
        
    Returns:
        8x8 list of lists where each element is either:
        - A piece character ('P', 'N', 'B', 'R', 'Q', 'K' for white pieces)
        - A piece character ('p', 'n', 'b', 'r', 'q', 'k' for black pieces)
        - None for empty squares
        
        The board is indexed as board[rank][file] where:
        - rank 0 = 8th rank (top of board, black's back rank)
        - rank 7 = 1st rank (bottom of board, white's back rank)
        - file 0 = a-file (left), file 7 = h-file (right)
        
    Raises:
        ValueError: If the FEN string is invalid
        
    Example:
        >>> board = decode_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        >>> board[0][0]  # a8 square
        'r'
        >>> board[7][4]  # e1 square
        'K'
        >>> board[3][3]  # d5 square (empty in starting position)
        None
    """
    # Split FEN string to get just the board position (first part)
    parts = fen.strip().split()
    if not parts:
        raise ValueError("Empty FEN string")
    
    board_fen = parts[0]
    
    # Split by ranks (separated by '/')
    ranks = board_fen.split('/')
    if len(ranks) != 8:
        raise ValueError(f"FEN must have 8 ranks, got {len(ranks)}")
    
    board: List[List[Optional[str]]] = []
    
    for rank_idx, rank_str in enumerate(ranks):
        rank: List[Optional[str]] = []
        
        for char in rank_str:
            if char.isdigit():
                # Number represents empty squares
                empty_count = int(char)
                if empty_count < 1 or empty_count > 8:
                    raise ValueError(f"Invalid empty square count: {empty_count}")
                rank.extend([None] * empty_count)
            elif char in 'pnbrqkPNBRQK':
                # Valid piece character
                rank.append(char)
            else:
                raise ValueError(f"Invalid character in FEN: '{char}'")
        
        if len(rank) != 8:
            raise ValueError(f"Rank {rank_idx + 1} has {len(rank)} squares, expected 8")
        
        board.append(rank)
    
    return board


def update_fen(fen: str, move: str) -> str:
    """
    Update a FEN string by applying a move in UCI notation.
    
    Args:
        fen: FEN string representing the current chess position
        move: Move in UCI notation (e.g., 'e2e4', 'e7e5', 'e1g1' for castling)
              Format: source_square + destination_square + [promotion_piece]
              Examples: 'e2e4', 'e7e8q' (pawn promotion to queen)
        
    Returns:
        New FEN string after applying the move
        
    Raises:
        ValueError: If the FEN string or move is invalid, or if the move is illegal
        
    Example:
        >>> new_fen = update_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4")
        >>> print(new_fen)
        'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1'
    """
    try:
        # Create a board from the FEN string
        board = chess.Board(fen)
    except ValueError as e:
        raise ValueError(f"Invalid FEN string: {e}")
    
    try:
        # Parse the move in UCI notation
        chess_move = chess.Move.from_uci(move)
    except ValueError as e:
        raise ValueError(f"Invalid move format: {e}")
    
    # Check if the move is legal
    if chess_move not in board.legal_moves:
        raise ValueError(f"Illegal move: {move} in position {fen}")
    
    # Apply the move
    board.push(chess_move)
    
    # Return the new FEN string
    return board.fen()
