"""
Continually updates ChessInterface.
"""

PLAYING_GAME = 1

from ChessInterface import ChessInterface
interface = ChessInterface()

"""
programmer_input = "illegal command"
while programmer_input != "":
    programmer_input = input("Press Enter to start. Type c to config. Type s to start immediately without user input.")

    if programmer_input == "c":
        success = False
        while not success:
            try:
                white = input("Enter black's elo (leave blank for maximum): ")
                black = input("Enter white's elo (leave blank for maximum): ")
                white = None if white == "" else int(white)
                black = None if black == "" else int(black)
                interface.setWhiteElo(white)
                interface.setBlackElo(black)
                success = True
            except KeyboardInterrupt:
                exit()
            except:
                print("Invalid input, try again.")
    elif programmer_input == "s":
        interface.update(sendCommands=True)
        interface.gameEnded = False
        interface.state = PLAYING_GAME
        break
"""

interface.loop()
