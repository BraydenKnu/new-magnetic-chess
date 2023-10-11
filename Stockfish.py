from stockfish import Stockfish # Documentation: https://pypi.org/project/stockfish/
import chess                    # Documentation: https://python-chess.readthedocs.io/en/latest/

stockfish = Stockfish("stockfish-16-windows\\stockfish-windows-x86-64-avx2.exe")

print(stockfish.get_stockfish_major_version())
