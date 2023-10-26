from stockfish import Stockfish # (pip install stockfish) Documentation: https://pypi.org/project/stockfish/
import chess                    # (pip install python-chess) Documentation: https://python-chess.readthedocs.io/en/latest/

import os

# detect whether we're on windows or linux
STOCKFISH_PATH = {
    'windows': 'stockfish-16-windows\\stockfish-windows-x86-64-avx2.exe',
    'linux': 'stockfish-16-linux/src/stockfish'
}

os_name = os.name
if (os_name == 'nt'): # Windows
    current_os = 'windows'
else:
    current_os = 'linux'

stockfish = Stockfish(STOCKFISH_PATH[current_os])

print(stockfish.get_stockfish_major_version())
