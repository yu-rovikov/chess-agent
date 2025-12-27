"""
Test script for chess_api.py functions.

This script tests the Chess-API integration with various positions.
"""

import asyncio
from agent.chess_api import (
    analyze_position,
    get_best_move,
    get_best_move_san,
    get_position_evaluation,
    get_win_chance,
    check_for_mate,
    get_continuation,
    analyze_specific_moves,
    decode_fen,
    update_fen,
    ChessAPIError
)


async def test_basic_analysis():
    """Test basic position analysis."""
    print("=" * 60)
    print("TEST 1: Basic Position Analysis")
    print("=" * 60)
    
    # Starting position
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"Position: Starting position")
    print(f"FEN: {fen}\n")
    
    try:
        result = await analyze_position(fen=fen, depth=12)
        print(f"✓ Analysis successful!")
        print(f"  Best move (UCI): {result.get('move')}")
        print(f"  Best move (SAN): {result.get('san')}")
        print(f"  Evaluation: {result.get('eval')}")
        print(f"  Win chance: {result.get('winChance'):.2f}%")
        print(f"  Depth: {result.get('depth')}")
        print(f"  Text: {result.get('text')}")
        print(f"  Continuation: {' '.join(result.get('continuationArr', [])[:5])}")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_get_best_move():
    """Test getting best move."""
    print("\n" + "=" * 60)
    print("TEST 2: Get Best Move")
    print("=" * 60)
    
    # Position after 1.e4 (correct FEN without invalid en passant)
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    print(f"Position: After 1.e4")
    print(f"FEN: {fen}\n")
    
    try:
        move_uci = await get_best_move(fen=fen, depth=12)
        move_san = await get_best_move_san(fen=fen, depth=12)
        print(f"✓ Best move retrieved!")
        print(f"  UCI notation: {move_uci}")
        print(f"  SAN notation: {move_san}")
        
        if not move_uci or not move_san:
            print(f"  ⚠️ Warning: Empty move returned!")
            return False
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_evaluation():
    """Test position evaluation."""
    print("\n" + "=" * 60)
    print("TEST 3: Position Evaluation")
    print("=" * 60)
    
    # Slightly better position for white
    fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
    print(f"Position: After 1.e4 e5 2.Nf3 Nf6")
    print(f"FEN: {fen}\n")
    
    try:
        eval_score = await get_position_evaluation(fen=fen, depth=12)
        win_chance = await get_win_chance(fen=fen, depth=12)
        print(f"✓ Evaluation retrieved!")
        print(f"  Evaluation: {eval_score:.2f}")
        print(f"  Win chance: {win_chance:.2f}%")
        
        if eval_score > 0:
            print(f"  → White is better")
        elif eval_score < 0:
            print(f"  → Black is better")
        else:
            print(f"  → Position is equal")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_mate_detection():
    """Test mate detection."""
    print("\n" + "=" * 60)
    print("TEST 4: Mate Detection")
    print("=" * 60)
    
    # Scholar's mate position (mate in 1)
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
    print(f"Position: Scholar's mate setup (Qh5, Bc4 vs ...Nc6, Nf6)")
    print(f"FEN: {fen}\n")
    
    try:
        mate_in = await check_for_mate(fen=fen, depth=12)
        print(f"✓ Mate check completed!")
        if mate_in is not None:
            if mate_in > 0:
                print(f"  → White mates in {mate_in} move(s)")
            else:
                print(f"  → Black mates in {abs(mate_in)} move(s)")
        else:
            print(f"  → No forced mate detected")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_continuation():
    """Test getting continuation line."""
    print("\n" + "=" * 60)
    print("TEST 5: Continuation Line")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"Position: Starting position")
    print(f"FEN: {fen}\n")
    
    try:
        continuation = await get_continuation(fen=fen, depth=12)
        print(f"✓ Continuation retrieved!")
        print(f"  Best line: {' '.join(continuation[:8])}")
        print(f"  ({len(continuation)} moves total)")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_specific_moves():
    """Test analyzing specific moves."""
    print("\n" + "=" * 60)
    print("TEST 6: Analyze Specific Moves")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    moves = ["e2e4", "d2d4", "g1f3"]
    print(f"Position: Starting position")
    print(f"Analyzing only: {', '.join(moves)}")
    print(f"FEN: {fen}\n")
    
    try:
        result = await analyze_specific_moves(fen=fen, moves=moves, depth=12)
        print(f"✓ Specific moves analyzed!")
        print(f"  Best of specified moves: {result.get('san')} ({result.get('move')})")
        print(f"  Evaluation: {result.get('eval'):.2f}")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


async def test_complex_position():
    """Test a complex middlegame position."""
    print("\n" + "=" * 60)
    print("TEST 7: Complex Position")
    print("=" * 60)
    
    # Complex position from the API documentation
    fen = "8/1P1R4/n1r2B2/3Pp3/1k4P1/6K1/Bppr1P2/2q5 w - - 0 1"
    print(f"Position: Complex endgame")
    print(f"FEN: {fen}\n")
    
    try:
        result = await analyze_position(fen=fen, depth=12)
        print(f"✓ Complex position analyzed!")
        print(f"  Best move: {result.get('san')} ({result.get('move')})")
        print(f"  Evaluation: {result.get('eval'):.2f}")
        print(f"  Win chance: {result.get('winChance'):.2f}%")
        print(f"  Text: {result.get('text')}")
        
        mate_in = result.get('mate')
        if mate_in:
            print(f"  Mate in: {abs(mate_in)} moves")
        return True
    except ChessAPIError as e:
        print(f"✗ Error: {e}")
        return False


def print_board(board):
    """Print the board in a readable format."""
    print("\n  a b c d e f g h")
    print("  ---------------")
    for rank_idx, rank in enumerate(board):
        rank_num = 8 - rank_idx
        pieces = []
        for piece in rank:
            if piece is None:
                pieces.append('.')
            else:
                pieces.append(piece)
        print(f"{rank_num}|{' '.join(pieces)}|{rank_num}")
    print("  ---------------")
    print("  a b c d e f g h\n")


def test_decode_fen_starting_position():
    """Test decoding the starting position FEN."""
    print("\n" + "=" * 60)
    print("TEST 8: Decode FEN - Starting Position")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"FEN: {fen}\n")
    
    try:
        board = decode_fen(fen)
        print(f"✓ FEN decoded successfully!")
        print_board(board)
        print(f"  Board dimensions: {len(board)}x{len(board[0])}")
        
        # Verify key squares
        assert board[0][0] == 'r', "a8 should be black rook"
        assert board[0][4] == 'k', "e8 should be black king"
        assert board[1][0] == 'p', "a7 should be black pawn"
        assert board[6][0] == 'P', "a2 should be white pawn"
        assert board[7][4] == 'K', "e1 should be white king"
        assert board[3][3] is None, "d5 should be empty"
        
        print(f"  ✓ a8 = {board[0][0]} (black rook)")
        print(f"  ✓ e8 = {board[0][4]} (black king)")
        print(f"  ✓ e1 = {board[7][4]} (white king)")
        print(f"  ✓ d5 = {board[3][3]} (empty)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decode_fen_after_e4():
    """Test decoding FEN after 1.e4."""
    print("\n" + "=" * 60)
    print("TEST 9: Decode FEN - After 1.e4")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    print(f"FEN: {fen}\n")
    
    try:
        board = decode_fen(fen)
        print(f"✓ FEN decoded successfully!")
        print_board(board)

        # Verify the pawn moved
        assert board[4][4] == 'P', "e4 should have white pawn"
        assert board[6][4] is None, "e2 should be empty"
        
        print(f"  ✓ e4 = {board[4][4]} (white pawn)")
        print(f"  ✓ e2 = {board[6][4]} (empty)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_decode_fen_complex():
    """Test decoding a complex position."""
    print("\n" + "=" * 60)
    print("TEST 10: Decode FEN - Complex Position")
    print("=" * 60)
    
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
    print(f"FEN: {fen}\n")
    
    try:
        board = decode_fen(fen)
        print(f"✓ FEN decoded successfully!")
        print_board(board)

        
        # Verify some pieces
        assert board[3][7] == 'Q', "h5 should have white queen"
        assert board[4][2] == 'B', "c4 should have white bishop"
        assert board[2][5] == 'n', "f6 should have black knight"
        assert board[2][2] == 'n', "c6 should have black knight"
        
        print(f"  ✓ h5 = {board[3][7]} (white queen)")
        print(f"  ✓ c4 = {board[4][2]} (white bishop)")
        print(f"  ✓ f6 = {board[2][5]} (black knight)")
        print(f"  ✓ c6 = {board[2][2]} (black knight)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_decode_fen_empty_board():
    """Test decoding an empty board."""
    print("\n" + "=" * 60)
    print("TEST 11: Decode FEN - Empty Board")
    print("=" * 60)
    
    fen = "8/8/8/8/8/8/8/8 w - - 0 1"
    print(f"FEN: {fen}\n")
    
    try:
        board = decode_fen(fen)
        print(f"✓ FEN decoded successfully!")
        
        # Verify all squares are empty
        empty_count = sum(1 for rank in board for square in rank if square is None)
        assert empty_count == 64, "All 64 squares should be empty"
        
        print(f"  ✓ All {empty_count} squares are empty")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_decode_fen_invalid():
    """Test error handling for invalid FEN strings."""
    print("\n" + "=" * 60)
    print("TEST 12: Decode FEN - Invalid Input Handling")
    print("=" * 60)
    
    invalid_fens = [
        ("", "Empty FEN"),
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP", "Too few ranks"),
    ]
    
    all_passed = True
    for fen, description in invalid_fens:
        print(f"\n  Testing: {description}")
        try:
            decode_fen(fen)
            print(f"  ✗ Should have raised ValueError!")
            all_passed = False
        except ValueError as e:
            print(f"  ✓ Correctly raised ValueError: {e}")
    
    return all_passed


def test_update_fen_basic():
    """Test basic move application with update_fen."""
    print("\n" + "=" * 60)
    print("TEST 13: Update FEN - Basic Move")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "e2e4"
    print(f"Starting FEN: {fen}")
    print(f"Move: {move}\n")
    
    try:
        new_fen = update_fen(fen, move)
        print(f"✓ Move applied successfully!")
        print(f"New FEN: {new_fen}\n")
        
        # Verify the result - python-chess doesn't set en passant if no capture is possible
        expected_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        if new_fen == expected_fen:
            print(f"  ✓ FEN matches expected result")
            return True
        else:
            print(f"  ✗ FEN mismatch!")
            print(f"  Expected: {expected_fen}")
            print(f"  Got:      {new_fen}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_update_fen_invalid_move():
    """Test error handling for invalid moves."""
    print("\n" + "=" * 60)
    print("TEST 14: Update FEN - Invalid Move Handling")
    print("=" * 60)
    
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    invalid_move = "e2e5"  # Illegal move - pawn can't jump
    
    print(f"Starting FEN: {fen}")
    print(f"Invalid move: {invalid_move} (pawn can't jump two squares to e5)\n")
    
    try:
        update_fen(fen, invalid_move)
        print(f"✗ Should have raised ValueError for illegal move!")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🦆" * 30)
    print("CHESS-API.COM INTEGRATION TEST")
    print("🦆" * 30 + "\n")
    
    # Async tests
    async_tests = [
        ("Basic Analysis", test_basic_analysis),
        ("Get Best Move", test_get_best_move),
        ("Position Evaluation", test_evaluation),
        ("Mate Detection", test_mate_detection),
        ("Continuation Line", test_continuation),
        ("Specific Moves", test_specific_moves),
        ("Complex Position", test_complex_position),
    ]
    
    # Sync tests for decode_fen and update_fen
    sync_tests = [
        ("Decode FEN - Starting Position", test_decode_fen_starting_position),
        ("Decode FEN - After 1.e4", test_decode_fen_after_e4),
        ("Decode FEN - Complex Position", test_decode_fen_complex),
        ("Decode FEN - Empty Board", test_decode_fen_empty_board),
        ("Decode FEN - Invalid Input", test_decode_fen_invalid),
        ("Update FEN - Basic Move", test_update_fen_basic),
        ("Update FEN - Invalid Move", test_update_fen_invalid_move),
    ]
    
    results = []
    
    # Run async tests
    for name, test_func in async_tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Run sync tests
    for name, test_func in sync_tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Chess-API integration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())