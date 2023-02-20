# Created by David Jantz in January 2019.

# Further features to add:
#    Play against the computer

import pygame, sys
from pygame.locals import *

#define global variables
WINDOWWIDTH = 900
WINDOWHEIGHT = 700
FPS = 30
BOARDWIDTH = 7 # number of columns
BOARDHEIGHT = 6 # number of rows
SPOTSIZE = 90 # width and height of each spot on the board in pixels
XMARGIN = int((WINDOWWIDTH - BOARDWIDTH * SPOTSIZE) / 2)
YMARGIN = int((WINDOWHEIGHT - BOARDHEIGHT * SPOTSIZE) / 2)
CIRCLERADIUS = int(SPOTSIZE / 2.5)

assert XMARGIN > 0 and YMARGIN > 0, 'Bro. Window is not large enough to accommodate board.'
assert BOARDWIDTH >= 4 or BOARDHEIGHT >= 4, 'How the hell do you expect to connect four on a board this small?'

#define color tuples
BLACK =  (  0,   0,   0)
RED =    (220,   0,   0)
YELLOW = (255, 255,   0)
NAVY =   (150, 150, 200)
WHITE =  (255, 255, 255)
BLUE =   ( 50,  50, 225)
TRANSPARENT = (255, 255, 255, 0)

# Syntactic sugar
BGCOLOR = NAVY
BOARDCOLOR = YELLOW
EMPTY = 'empty'
TIE = 'tie'

def main():
    # more global variables
    global FPSCLOCK, DISPLAYSURF, SURF2
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    SURF2 = DISPLAYSURF.convert_alpha() # second display surface used to animate pieces falling down
    pygame.display.set_caption('Connect Four (code written by David Jantz)')
    
    board = generateEmptyBoard() # 2d list with dimensions BOARDWIDTH x BOARDHEIGHT
    turn = 1 # 1 is RED's turn, -1 is BLACK's turn.
    column = None
    winner = None
    
    while winner == None:        

       # event handling loop includes function calls to update the board.
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                winner = 'Nobody'

            # if the mouse moves, track its location and figure out which column it's in (if any)
            elif event.type == MOUSEMOTION:
                mouseX, mouseY = event.pos
                column = getColumnNumber(mouseX, mouseY, board) # figure out which column was clicked, if any
            
            # if the board is clicked, add the right piece to the correct column.
            elif event.type == MOUSEBUTTONUP:
                mouseX, mouseY = event.pos
                column = getColumnNumber(mouseX, mouseY, board) # this line and the one above have to be here to prevent some funkiness resulting from the dropping piece animation.
                
                if column != None and board[column][0] == EMPTY: # Nothing happens unless you click on the board on a column with empty slots.
                    board = addPiece(column, board, turn, True) # call the animation function, then update the 2d list so that drawBoard() can paint in a new piece.
                    turn *= -1 # change whose turn it is.
                    winner, oneEnd, otherEnd =  hasWon(board) # winner is RED, BLACK, tie, or None. The ends refer to the ends of the winning segment of four pieces (in board coordinates)
                    if winner != None:
                        gameWinAnimation(board, winner, oneEnd, otherEnd)
        
        # starting from the back, paint on all the schtuff.
        DISPLAYSURF.fill(BGCOLOR)
        SURF2.fill(TRANSPARENT) # again, second display surface needed for animation fun. See drawBoard() for details.
        drawBoard(board)
        
        # Outside the event loop -- if the last stored coordinates for mouse location are in a column with empty spots, do the highlight thing.
        if column != None and board[column][0] == EMPTY:
            drawHighlight(column, board, turn)
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)

    pygame.quit()
    sys.exit()

def drawBoard(board): # draw the board in the right spot with the right dimensions.
    pygame.draw.rect(SURF2, YELLOW, (XMARGIN, YMARGIN, BOARDWIDTH * SPOTSIZE, BOARDHEIGHT * SPOTSIZE)) # Drawn on SURF2 so I can "cut holes" in it.
    
    # draw circles the same color as the background if board is empty there. Otherwise, draw red or black.
    for boardX in range(BOARDWIDTH):
        for boardY in range(BOARDHEIGHT):
            pixX, pixY = getPixCoords((boardX, boardY)) # get (center, center) pixel coordinates of every spot on the board.
            if board[boardX][boardY] == EMPTY:
                pygame.draw.circle(SURF2, TRANSPARENT, (pixX, pixY), CIRCLERADIUS) # replace open slots with transparent pixels
            elif board[boardX][boardY] == RED:
                pygame.draw.circle(SURF2, RED, (pixX, pixY), CIRCLERADIUS) # has to go on SURF2 as well or else it would be "covered up" when SURF2 is blitted on top.
            elif board[boardX][boardY] == BLACK:
                pygame.draw.circle(SURF2, BLACK, (pixX, pixY), CIRCLERADIUS)
    
    DISPLAYSURF.blit(SURF2, (0, 0))

def generateEmptyBoard(): # Generates a 2D list of all False values to denote that those spots are empty.
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY] * BOARDHEIGHT)
    return board

def getPixCoords(boardcoords): # Translates board coordinates to (center, center) pixel coordinates.
    pixX = int(boardcoords[0] * SPOTSIZE + XMARGIN + SPOTSIZE / 2)
    pixY = int(boardcoords[1] * SPOTSIZE + YMARGIN + SPOTSIZE / 2)
    return pixX, pixY

def addPiece(boardX, board, turn, boolean): # Figure out which spot on the board to change and update board. drawBoard() uses the information to update the display on the next loop of main().
    boardY = BOARDHEIGHT - 1 # has to be minus one to account for lists starting at zero.
    
    # while loop starts at the bottom and works its way up, stopping when it reaches an empty slot or the top of the column.
    # When it stops, whatever stored value for boardY it ended with is the correct height.
    while board[boardX][boardY] != EMPTY and boardY >= 0:
        boardY -= 1
    
    # boolean value decides whether to actually update the board or not. If not, returns spot coordinates to drawHighlight function.
    if boolean == False:
        return boardX, boardY
    else:
        if turn == 1:
            addPieceAnimation(board, RED, boardX, boardY) # animate the piece dropping into place.
            board[boardX][boardY] = RED # update the board 2d list
        elif turn == -1:
            addPieceAnimation(board, BLACK, boardX, boardY) #same as above
            board[boardX][boardY] = BLACK # same as above
        return board

def getColumnNumber(mouseX, mouseY, board): # Translate pixel coordinates to a column number.
    # for every column, make a Rect object and check to see if mouse coordinates fall within that rectangle.
    # the Rect object is not strictly necessary, but it's good to practice using pygame's built-in methods.
    for x in range(len(board)):
        left = int(x * SPOTSIZE + XMARGIN)
        top = YMARGIN
        columnrect = pygame.Rect(left, top, SPOTSIZE, SPOTSIZE * BOARDHEIGHT)
        if columnrect.collidepoint(mouseX, mouseY):
            return x
    return None

def drawHighlight(column, board, turn): # Highlights spots on the board that the mouse hovers over.
    boardX, boardY = addPiece(column, board, turn, False) # get board coordinates for spot to highlight.
    pixX, pixY = getPixCoords((boardX, boardY)) # convert to pixel coordinates

    if turn == 1: # Red's turn
        pygame.draw.circle(DISPLAYSURF, RED, (pixX, pixY), CIRCLERADIUS - 5)
    elif turn == -1: # Black's turn
        pygame.draw.circle(DISPLAYSURF, BLACK, (pixX, pixY), CIRCLERADIUS - 5)
    
    pygame.draw.circle(DISPLAYSURF, BGCOLOR, (pixX, pixY), CIRCLERADIUS - 10)

def hasWon(board): # checks to see if anyone has won with 4 in a row. need to add comments and / or make it shorter.
    # check for tie game
    tiegame = True
    for l in board:
        if EMPTY in l:
            tiegame = False
    if tiegame:
        return TIE, None, None
    
    # check vertical
    for column in range(len(board)):    
        for row in range(len(board[0]) - 3):
            if board[column][row] == board[column][row + 1] == board[column][row + 2] == board[column][row + 3] == RED:
                print('Red wins')
                return RED, (column, row), (column, row + 3)
            if board[column][row] == board[column][row + 1] == board[column][row + 2] == board[column][row + 3] == BLACK:
                print('Black wins')
                return BLACK, (column, row), (column, row + 3)
    
    # check horizontal
    for column in range(len(board) - 3):    
        for row in range(len(board[0])):
            if board[column][row] == board[column + 1][row] == board[column + 2][row] == board[column + 3][row] == RED:
                print('Red wins')
                return RED, (column, row), (column + 3, row)
            if board[column][row] == board[column + 1][row] == board[column + 2][row] == board[column + 3][row] == BLACK:
                print('Black wins')
                return BLACK, (column, row), (column + 3, row)
    
    # check diagonal sloping down to the right
    for column in range(len(board) - 3):    
        for row in range(len(board[0]) - 3):
            if board[column][row] == board[column + 1][row + 1] == board[column + 2][row + 2] == board[column + 3][row + 3] == RED:
                print('Red wins')
                return RED, (column, row), (column + 3, row + 3)
            if board[column][row] == board[column + 1][row + 1] == board[column + 2][row + 2] == board[column + 3][row + 3] == BLACK:
                print('Black wins')
                return BLACK, (column, row), (column + 3, row + 3)
    
    # check diagonal sloping up to the right
    for column in range(len(board) - 3):    
        for row in range(3, len(board[0])):
            if board[column][row] == board[column + 1][row - 1] == board[column + 2][row - 2] == board[column + 3][row - 3] == RED:
                print('Red wins')
                return RED, (column, row), (column + 3, row - 3)
            if board[column][row] == board[column + 1][row - 1] == board[column + 2][row - 2] == board[column + 3][row - 3] == BLACK:
                print('Black wins')
                return BLACK, (column, row), (column + 3, row - 3)

    return None, None, None

def gameWinAnimation(board, winner, lineStart, lineEnd): # some cool flashy stuff based on who won
    fontsize = 50
    fontObj = pygame.font.Font('freesansbold.ttf', fontsize)
    
    if winner == RED:
        textSurfaceObj = fontObj.render('Red Wins!', True, WHITE, None) # create a new surface to do all the text stuff on
        linecolor = BLACK
    elif winner == BLACK:
        textSurfaceObj = fontObj.render('Black Wins!', True, WHITE, None) # create a new surface to do all the text stuff on
        linecolor = RED
    elif winner == TIE: # Since there's no animation for a tie game, draw everything to the board and then exit the function.
        textSurfaceObj = fontObj.render('Tie game. God, that was boring.', True, WHITE, None)
        textRectObj = textSurfaceObj.get_rect()
        textRectObj.center = (int(WINDOWWIDTH / 2), int(fontsize / 2))
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(board)
        DISPLAYSURF.blit(textSurfaceObj, textRectObj)
        pygame.display.update()
        pygame.time.wait(4000)
        return None
    
    #If winner was RED or BLACK, we're calling these guys for the first time.
    textRectObj = textSurfaceObj.get_rect()
    textRectObj.center = (int(WINDOWWIDTH / 2), int(fontsize / 2))
    
    lineStart = getPixCoords(lineStart)
    lineEnd = getPixCoords(lineEnd)
    
    color1 = BLUE
    color2 = BGCOLOR
    
    for i in range(10): # Flash the new background color 5 times.
        color1, color2 = color2, color1
        DISPLAYSURF.fill(color1)
        drawBoard(board)
        DISPLAYSURF.blit(textSurfaceObj, textRectObj) # computer interprets textRectObj as a two-item tuple for location
        pygame.draw.line(DISPLAYSURF, linecolor, lineStart, lineEnd, 5)
        pygame.display.update()
        pygame.time.wait(500)

def addPieceAnimation(board, color, boardX, boardY): # Animate the piece falling into place.
    endX, endY = getPixCoords((boardX, boardY)) #ending position of the piece
    Y = YMARGIN - CIRCLERADIUS #starting height
    framerate = 20
    timefalling = 0
    
    while Y < endY:
        DISPLAYSURF.fill(BGCOLOR) #start from the back, paint stuff in.
        pygame.draw.circle(DISPLAYSURF, color, (endX, Y), CIRCLERADIUS) # draw the falling piece
        drawBoard(board) # draw the board, which allows falling piece to show through empty slots.
        pygame.display.update()
        pygame.time.wait(framerate)
        
        Y += int(timefalling / 15) # Increase Y an increasing amount each loop in proportion to timefalling.
        timefalling += framerate # increase timefalling by the same number of milliseconds as the program waited for.


if __name__ == '__main__':
    main()