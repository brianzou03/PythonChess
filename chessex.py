import random
import sys
import os

#Brian Zou's Python Chess game from the summer of 2017
#Uploaded to Github on August 22nd, 2020


class Player(object):
    #player class
    allsquares = [(x, y) for x in range(8) for y in range(8)]
    dullmoves = 0

    def __init__(self, color, nature, name):
        self.color = color
        self.nature = nature
        self.name = name
        self.can_castle_long_this_turn = False
        self.can_castle_short_this_turn = False
        self.playedturns = 0

    def __str__(self):
        if self.nature is 'AI':
        #if is AI
            return self.name + ' (' + self.nature + ')' + ' as ' + self.color
        else:
            return self.name + ' as ' + self.color

    def set_opponent(self, opponent):
        self.opponent = opponent

    def getpieces(self, board):
        return [pos for pos in board if board[pos].color is self.color]

    def potentialtargets(self, playerspieces):
        return [pos for pos in self.allsquares if pos not in playerspieces]

    def kingpos(self, board):
        for mine in self.getpieces(board):
            if board[mine].piecename is 'k':
                return mine

    def validmoves(self, board):
        #checks valid moves
        self.set_castling_flags(board)
        mypieces = self.getpieces(board)
        for mine in mypieces:
            for target in self.potentialtargets(mypieces):
                if self.canmoveto(board, mine, target):
                    if not self.makesusp(mine, target, board):
                        yield (mine, target)

    def set_castling_flags(self, board):
        kingpos = self.kingpos(board)
        if self.king_can_castle(board, kingpos):
            if self.rook_can_castle_long(board, kingpos):
                self.can_castle_long_this_turn = True
            else:
                self.can_castle_long_this_turn = False
            if self.rook_can_castle_short(board, kingpos):
                self.can_castle_short_this_turn = True
            else:
                self.can_castle_short_this_turn = False
        else:
            self.can_castle_long_this_turn = False
            self.can_castle_short_this_turn = False

    def king_can_castle(self, board, kingpos):
        #king castling requires check for king & rook
        if board[kingpos].nrofmoves is 0 and not self.isincheck(board):
            return True

    def rook_can_castle_long(self, board, kingpos):
        #rook swapping with king for castling - long
        if self.rooklong in board and board[self.rooklong].nrofmoves is 0:
            if self.pathclear(self.rooklong, kingpos, board):
                tmptarget = (kingpos[0], kingpos[1] - 1)
                if not self.makesusp(kingpos, tmptarget, board):
                    return True

    def rook_can_castle_short(self, board, kingpos):
        #rook swapping with king for castling - short
        if self.rookshort in board and board[self.rookshort].nrofmoves is 0:
            if self.pathclear(self.rookshort, kingpos, board):
                tmptarget = (kingpos[0], kingpos[1] + 1)
                if not self.makesusp(kingpos, tmptarget, board):
                    return True

    def getposition(self, move):
        #getting position 
        colstart = int(ord(move[0].lower()) - 97)
        rowstart = int(move[1]) - 1
        targetcol = int(ord(move[2].lower()) - 97)
        targetrow = int(move[3]) - 1
        start = (rowstart, colstart)
        target = (targetrow, targetcol)
        return start, target

    def reacheddraw(self, board):
        #if a draw is reached
        if not list(self.validmoves(board)) and not self.isincheck(board):
            return True
        if len(list(self.getpieces(board))) == \
                len(list(self.opponent.getpieces(board))) == 1:
            return True
        if Player.dullmoves / 2 == 50:
            if self.nature is 'AI':
                return True
            else:
                if input("Call a draw? (yes/no) : ") in ['yes', 'y', 'Yes']:
                    return True

    def ischeckmate(self, board):
        #checks if a checkmate is present 
        if not list(self.validmoves(board)) and self.isincheck(board):
            return True

    def turn(self, board):

        turnstring = "\n%s's turn now," % self.name
        warning = " *** Your king is in check *** "
        if self.isincheck(board):
            turnstring = turnstring + warning
        return turnstring
        #provides a warning for whenever a player's king is in check

    def getmove(self, board):
        print
        "\n"
        while True:
            #if the player is a computer, get a move from the computer
            if self.nature is 'AI':
                return random.choice(list(self.validmoves(board)))
            else:
                #if the player is human, get a move from the player
                move = input("\nMake a move please : ")
                if move == 'exit':
                    break
                else:
                    start, target = self.getposition(move)
                    if (start, target) in self.validmoves(board):
                        return start, target
                    else:
                        raise IndexError

    def makesusp(self, start, target, board):
        #make temporary move to test for any checks
        self.domove(board, start, target)
        retval = self.isincheck(board)

        #undoes temporary moves
        self.unmove(board, start, target)
        return retval

    def isincheck(self, board):
        #for whenever a king is in check
        kingpos = self.kingpos(board)
        for enemy in self.opponent.getpieces(board):
            if self.opponent.canmoveto(board, enemy, kingpos):
                return True

    def domove(self, board, start, target):
        #for whenever a move is issued
        self.savedtargetpiece = None
        if target in board:
            self.savedtargetpiece = board[target]
        board[target] = board[start]
        board[target].position = target
        del board[start]
        board[target].nrofmoves += 1
        if board[target].piecename is 'p' and not self.savedtargetpiece:
            if abs(target[0] - start[0]) == 2:
                board[target].turn_moved_twosquares = self.playedturns
            elif abs(target[1] - start[1]) == abs(target[0] - start[0]) == 1:
                #pawn has done an en passant, remove the dead piece
                if self.color is 'white':
                    passant_target = (target[0] - 1, target[1])
                else:
                    passant_target = (target[0] + 1, target[1])
                self.savedpawn = board[passant_target]
                del board[passant_target]
        if board[target].piecename is 'k':
            if target[1] - start[1] == -2:
                #king is castling long, move rook long
                self.domove(board, self.rooklong, self.rooklong_target)
            elif target[1] - start[1] == 2:
                #king is castling short, move rook short
                self.domove(board, self.rookshort, self.rookshort_target)

    def unmove(self, board, start, target):
        #unmove for whenever a move isn't completed
        board[start] = board[target]
        board[start].position = start
        if self.savedtargetpiece:
            board[target] = self.savedtargetpiece
        else:
            del board[target]
        board[start].nrofmoves -= 1
        if board[start].piecename is 'p' and not self.savedtargetpiece:
            if abs(target[0] - start[0]) == 2:
                del board[start].turn_moved_twosquares
            elif abs(target[1] - start[1]) == abs(target[0] - start[0]) == 1:
                #moved back en passant Pawn, restore the eaten pawn
                if self.color is 'white':
                    formerpos_passant_target = (target[0] - 1, target[1])
                else:
                    formerpos_passant_target = (target[0] + 1, target[1])
                board[formerpos_passant_target] = self.savedpawn
        if board[start].piecename is 'k':
            #for whenever the piece is a king
            if target[1] - start[1] == -2:
                #the king's castling long has been unmoved, move back rook long
                self.unmove(board, self.rooklong, self.rooklong_target)
            elif target[1] - start[1] == 2:
                #the king's castling short has been unmoved, move back rook short
                self.unmove(board, self.rookshort, self.rookshort_target)

    def pawnpromotion(self, board, target):
        #for whenever a pawn can be promoted/is promoted
        
        if self.nature is 'AI':
            #checks to see if knight makes opponent checkmate
            board[target].promote('kn')
            if self.opponent.ischeckmate(board):
                return
            else:
                promoteto = 'q'

        else:
            promoteto = 'empty'
            while promoteto.lower() not in ['kn', 'q']:
                promoteto = \
                    input("You can promote your pawn to a :\n[Kn]ight or [Q]ueen : ")
        board[target].promote(promoteto)

    def pathclear(self, start, target, board):
        colstart, rowstart = start[1], start[0]
        targetcol, targetrow = target[1], target[0]
        if abs(rowstart - targetrow) <= 1 and abs(colstart - targetcol) <= 1:
            #the orig. case
            return True
        else:
            if targetrow > rowstart and targetcol == colstart:
                #straight down
                tmpstart = (rowstart + 1, colstart)
            elif targetrow < rowstart and targetcol == colstart:
                #straight up
                tmpstart = (rowstart - 1, colstart)
            elif targetrow == rowstart and targetcol > colstart:
                #straight right
                tmpstart = (rowstart, colstart + 1)
            elif targetrow == rowstart and targetcol < colstart:
                #straight left
                tmpstart = (rowstart, colstart - 1)
            elif targetrow > rowstart and targetcol > colstart:
                #diagonal down right
                tmpstart = (rowstart + 1, colstart + 1)
            elif targetrow > rowstart and targetcol < colstart:
                #diagonal down left
                tmpstart = (rowstart + 1, colstart - 1)
            elif targetrow < rowstart and targetcol > colstart:
                #diagonal up right
                tmpstart = (rowstart - 1, colstart + 1)
            elif targetrow < rowstart and targetcol < colstart:
                #diagonal up left
                tmpstart = (rowstart - 1, colstart - 1)
            #if there are no pieces in the way, test the next square
            if tmpstart in board:
                return False
            else:
                return self.pathclear(tmpstart, target, board)

    def canmoveto(self, board, start, target):
        #places pieces can move to
        startpiece = board[start].piecename.upper()
        if startpiece == 'R' and not self.check_rook(start, target):
            return False
        elif startpiece == 'KN' and not self.check_knight(start, target):
            return False
        elif startpiece == 'P' and not self.check_pawn(start, target, board):
            return False
        elif startpiece == 'B' and not self.check_bishop(start, target):
            return False
        elif startpiece == 'Q' and not self.check_queen(start, target):
            return False
        elif startpiece == 'K' and not self.check_king(start, target):
            return False
        #only the knight piece is allowed to jump over pieces
        if startpiece in 'RPBQK':
            if not self.pathclear(start, target, board):
                return False
        return True

    def check_rook(self, start, target):
        #check for straight lines of movement
        if start[0] == target[0] or start[1] == target[1]:
            return True

    def check_knight(self, start, target):
        #the knight piece may move 2+1 in any direction and jump over pieces
        if abs(target[0] - start[0]) == 2 and abs(target[1] - start[1]) == 1:
            return True
        elif abs(target[0] - start[0]) == 1 and abs(target[1] - start[1]) == 2:
            return True

    def check_pawn(self, start, target, board):
        #disable backwards & sideways movement
        if 'white' in self.color and target[0] < start[0]:
            return False
        elif 'black' in self.color and target[0] > start[0]:
            return False
        if start[0] == target[0]:
            return False
        if target in board:
            # Only attack if one square diagonaly away
            if abs(target[1] - start[1]) == abs(target[0] - start[0]) == 1:
                return True
        else:
            #allow pawns to only move forwards by one, with the exception of 1st turn
            if start[1] == target[1]:
                #the normal one square move for a pawn
                if abs(target[0] - start[0]) == 1:
                    return True
                #the 1st exception to the rule, 2 square move for 1st time
                if board[start].nrofmoves is 0:
                    if abs(target[0] - start[0]) == 2:
                        return True
            #the 2nd exception to the rule, en passant
            if start[0] == self.enpassantrow:
                if abs(target[0] - start[0]) == 1:
                    if abs(target[1] - start[1]) == 1:
                        if target[1] - start[1] == -1:
                            passant_target = (start[0], start[1] - 1)
                        elif target[1] - start[1] == 1:
                            passant_target = (start[0], start[1] + 1)
                        if passant_target in board and \
                                        board[passant_target].color is not self.color and \
                                        board[passant_target].piecename is 'p' and \
                                        board[passant_target].nrofmoves == 1 and \
                                        board[passant_target].turn_moved_twosquares == \
                                                self.playedturns - 1:
                            return True

    def check_bishop(self, start, target):
        #check for non-horizontal/vertical and linear movement of bishop
        if abs(target[1] - start[1]) == abs(target[0] - start[0]):
            return True

    def check_queen(self, start, target):
        #will be true if move can be done as a rook or a bishop (combination of the two)
        if self.check_rook(start, target) or self.check_bishop(start, target):
            return True

    def check_king(self, start, target):
        #the king can move one square in any direction
        if abs(target[0] - start[0]) <= 1 and abs(target[1] - start[1]) <= 1:
            return True
        #exception is when king is castling
        if self.can_castle_short_this_turn:
            if target[1] - start[1] == 2 and start[0] == target[0]:
                return True
        if self.can_castle_long_this_turn:
            if target[1] - start[1] == -2 and start[0] == target[0]:
                return True


class Piece(object):
    #piece class
    def __init__(self, piecename, position, player):
        self.color = player.color
        self.nature = player.nature
        self.piecename = piecename
        self.position = position
        self.nrofmoves = 0

    def __str__(self):
        if self.color is 'white':
            if self.piecename is 'p':
                return 'WP'
            else:
                return self.piecename.upper()
        else:
            return self.piecename

    def canbepromoted(self):
        if str(self.position[0]) in '07':
            return True

    def promote(self, to):
        self.piecename = to.lower()


class Game(object):
    #game class
    def __init__(self, playera, playerb):
        self.board = dict()
        for player in [playera, playerb]:
            if player.color is 'white':
                brow, frow = 0, 1
                player.enpassantrow = 4
            else:
                brow, frow = 7, 6
                player.enpassantrow = 3
            player.rooklong = (brow, 0)
            player.rooklong_target = \
                (player.rooklong[0], player.rooklong[1] + 3)

            player.rookshort = (brow, 7)
            player.rookshort_target = \
                (player.rookshort[0], player.rookshort[1] - 2)

            [self.board.setdefault((frow, x), Piece('p', (frow, x), player)) \
             for x in range(8)]
            [self.board.setdefault((brow, x), Piece('r', (brow, x), player)) \
             for x in [0, 7]]
            [self.board.setdefault((brow, x), Piece('kn', (brow, x), player)) \
             for x in [1, 6]]
            [self.board.setdefault((brow, x), Piece('b', (brow, x), player)) \
             for x in [2, 5]]
            self.board.setdefault((brow, 3), Piece('q', (brow, 3), player))
            self.board.setdefault((brow, 4), Piece('k', (brow, 4), player))

    def printboard(self):
        #board printing, output is below
        topbottom = ['*', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', '*']
        sides = ['1', '2', '3', '4', '5', '6', '7', '8']
        tbspacer = ' ' * 6
        rowspacer = ' ' * 5
        cellspacer = ' ' * 4
        empty = ' ' * 3
        print
        for field in topbottom:
            print("%4s" % field,)
            print(tbspacer + ("_" * 4 + ' ') * 8)
        for row in range(8):
            print(rowspacer + (('|' + cellspacer) * 9))
            print("%4s" % sides[row], ('|'),)
            for col in range(8):
                if (row, col) not in self.board:
                    print(empty + '|',)
                else:
                    print("%2s" % self.board[(row, col)], ('|'),)
            print("%2s" % sides[row],)
            print(rowspacer + '|' + (("_" * 4 + '|') * 8))
        for field in topbottom:
            print("%4s" % field,)
        print("\n")

    def refreshscreen(self, player):
        #refreshing the screen
        if player.color is 'white':
            playera, playerb = player, player.opponent
        else:
            playera, playerb = player.opponent, player
        os.system('clear')
        print("   Now playing: %s vs %s" % (playera, playerb))
        self.printboard()

    def run(self, player):
        #running the program
        self.refreshscreen(player)
        while True:
            print(player.turn(self.board))
            try:
                start, target = player.getmove(self.board)
            except (IndexError, ValueError):
                self.refreshscreen(player)
                print("\n\nPlease enter a valid move.")
            except TypeError:
                #doesn't start, targets if the user exits
                break
            else:
                if target in self.board or self.board[start].piecename is 'p':
                    Player.dullmoves = 0
                else:
                    Player.dullmoves += 1
                player.domove(self.board, start, target)
                player.playedturns += 1
                # Check if there is a Pawn up for promotion
                if self.board[target].piecename is 'p':
                    if self.board[target].canbepromoted():
                        player.pawnpromotion(self.board, target)
                player = player.opponent
                if player.reacheddraw(self.board):
                    return 1, player
                elif player.ischeckmate(self.board):
                    return 2, player
                else:
                    self.refreshscreen(player)

    def end(self, player, result):
        #end of a match determined
        looser = player.name
        winner = player.opponent.name
        if result == 1:
            endstring = "\n%s and %s reached a draw." % (winner, looser)
            #1st result, if a draw is reached
        elif result == 2:
            endstring = "\n%s put %s in checkmate." % (winner, looser)
            #2nd result, if a player is checkmated
        os.system('clear')
        self.printboard()
        return endstring


def newgame():
    #start of a new game
    os.system('clear')

    playera, playerb = getplayers()
    playera.set_opponent(playerb)
    playerb.set_opponent(playera)
    game = Game(playera, playerb)
    infostring = \
        """
        Alright, %s and %s, it's time to play.
    
        Player A: %s (uppercase)
        Player B: %s (lowercase)
        (Use moves on form 'a2b3' or type 'exit' at any time.) """
    print(infostring % (playera.name, playerb.name, playera, playerb))
    input("\n\nPress [Enter] when ready")
    # white starts
    player = playera
    try:
        result, player = game.run(player)
    except TypeError:
        #there is no result if the user exits
        pass
    else:
        print(game.end(player, result))
        input("\n\nPress any key if you wish to continue.")


def getplayers():
    #player names
    ainames = ['Dude 1', 'Dude 2']
    name1 = input("\nPlayer A (white): ")
    if not name1:
        playera = Player('white', 'AI', ainames[0])
        #first player name
    else:
        playera = Player('white', 'human', name1)
    name2 = input("\nPlayer B (black): ")
    if not name2:
        playerb = Player('black', 'AI', ainames[1])
        #second player name
    else:
        playerb = Player('black', 'human', name2)
        #for real players
    return playera, playerb


def main():
    """ Display the menu after game has ended. """

    menu = """
    Thanks for playing Brian's Python chess game, would you like to go again?
    Hit [Enter] to play again or type 'exit' to exit. """
    try:
        while True:
            newgame()
            choice = input(menu)
            if choice == 'exit':
                print("\nOkay! Welcome back player!")
                break
    except KeyboardInterrupt:
        sys.exit("\n\nOkok. Ending program.")

if __name__ == '__main__':
    #cProfile.run('main()')
    main()
    #boilerplate