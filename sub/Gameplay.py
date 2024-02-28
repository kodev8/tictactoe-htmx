import jsonpickle
from random import choice, random
from copy import deepcopy
from models import User

class DataHandler:

    @staticmethod
    def serialize(obj):
        return jsonpickle.encode(obj)

    @staticmethod
    def deserialize(json):
        return jsonpickle.decode(json)

class  GAMESTATES:
    PLAYING = 0
    X_WON = 1
    O_WON = 2
    DRAW = 3


class ScoreTracker:
    def __init__(self, home, away):

        self.home = home
        self.away = away

        self.draws = 0

        self.home_score = 0
        self.away_score = 0

    def __str__(self):
        return f"Home: {self.home_score} - Away: {self.away_score}"

    def update_score(self, winner):
        print("updating score", winner, self.home, self.away, self.home_score, self.away_score, self.draws)
        if winner == self.home:
            print('HOME WINS')
            self.home_score += 1

        elif winner == self.away:
            print('AWAY WINS')
            self.away_score += 1

        else:
            print('DRAW')
            self.draws += 1
  
    def get_scores(self):
        scores = {
            "home": self.home_score,
            "away": self.away_score,
            "draws": self.draws
        }
        return scores
    
    def forfeit(self, who):
        if who == "home":
            self.update_score(self.away)
        else:
            self.update_score(self.home)
        
class Gameplay(GAMESTATES):

    def __init__(self, x_player, o_player, score_tracker: ScoreTracker):

        self.clear_board()
        self.x_player = x_player
        self.o_player = o_player
        self.turn = x_player
        self.gamestate = self.PLAYING
        self.score_tracker = score_tracker

    def __str__(self):
        sn = "======== GAME BOARD ==========\n"
        for i in range(3):
            for j in range(3):
                ele = self._board[i*3 + j] 

                if ele is not None:
                    str_ele = str(ele)
                    if ele >  0: 
                        ele = "+" + str_ele
                    else:
                        ele = str_ele
                else:
                    ele = "  " 
                sn += ele

                if j < 2:
                    sn += "|"
            if i < 2:
                sn += "\n---------\n"   

        return sn
      
    @property
    def board(self):
        return self._board
    
    @board.setter
    def board(self, board):
        self._board = board

    def clear_board(self):
        self._board = [None] * 9

    def available_moves(self) -> list:
        """Returns a list of available moves"""
        return [i for i, spot in enumerate(self._board) if spot is None]
    
    def valid_move(self, move: int)-> bool:
        """Returns True if move is valid"""
        try:
            return int(move) in self.available_moves()
        
        except ValueError:
            return False

    def has_won(self, player)-> bool:
        """Returns True if player has won"""
        win_states = {
            (self._board[0], self._board[1], self._board[2]): ('h', (0, 2)),
            (self._board[3], self._board[4], self._board[5]): ('h', (3, 5)),
            (self._board[6], self._board[7], self._board[8]): ('h', (6, 8)),
            (self._board[0], self._board[3], self._board[6]): ('v', (0, 6)),
            (self._board[1], self._board[4], self._board[7]): ('v', (1, 7)),
            (self._board[2], self._board[5], self._board[8]): ('v', (2, 8)),
            (self._board[0], self._board[4], self._board[8]): ('d1',(0, 8)),
            (self._board[2], self._board[4], self._board[6]): ('d2', (2, 6)),
        }
         

        return win_states.get((player, player, player))
    
    def is_draw(self)-> bool:
        """Returns True if game is a draw"""
        return len(self.available_moves()) == 0
    
    def player_move(self,  position: int, player: int = None):
        """Places player's move on board"""

        pos = int(position)
        self._board[pos] = self.turn if player is None else player
        
        # running through minimax so dont need to contiue, without player we rely on game.turn
        if player:
            return

        check_win = self.has_won(self.turn)
        if check_win:

            if self.turn == self.x_player:
                self.gamestate = self.X_WON
            else:
                self.gamestate = self.O_WON

            self.score_tracker.update_score(self.turn)
            return check_win
                
        elif self.is_draw():
            self.gamestate = self.DRAW
            # update draw score
            self.score_tracker.update_score(0)
            return self.gamestate
            
        # swap turn after move
        # if not player: 
        self.turn = self.o_player if self.turn == self.x_player else self.x_player
    
    def get_text(self):
        return "X" if self.turn == self.x_player else "O"
    

class ComputerPlayer:

    # inject dependencies

    LEVELS = {

        1: "Easy",
        2: "Medium",
        3: "Expert"
    }
    
    def __init__(self,opponent=None, player=-1, difficulty=3):
        self.player = player
        self.opponent = opponent
        self.difficulty = difficulty
        
    @property
    def difficulty(self):
        return self._difficulty
    
    @difficulty.setter
    def difficulty(self, difficulty):
        if difficulty not in self.LEVELS:
            raise ValueError("Difficulty must be 1 (Easy), 2 (Medium) or 3 (Expert)")
        self._difficulty = difficulty

    def easy_move(self, game : Gameplay):
        """Returns a random move"""
        return choice(game.available_moves())
    
    def minimax(self, game : Gameplay, is_maximising: bool, alpha: int = -10 , beta: int = 10):
        # TODO: add depth to get quicker wins
        """Returns the best move for the computer
        Parameters:
        is_maximising (bool): True if the computer is maximising
        alpha (int): best maximum value that can be guaranteed when maximising
        beta (int): best minimum value that can be guaranteed when minimising
        depth (int): the depth of the tree
        """
        # base case
        # chcek if computer has won
        if game.has_won(self.player):
            return 1, None
        
        # check if opponent has won
        elif game.has_won(self.opponent):
            return -1, None
        
        # check if game is a draw
        elif game.is_draw():
            return 0, None

        # maximising when game.turn is self.player
        if is_maximising:
            best = -10
            best_move = None
            for move in game.available_moves():
                temp_game = deepcopy(game)
                temp_game.player_move(move, self.player)
                score = self.minimax(temp_game, False, alpha, beta)[0]
                if score > best:
                    best = score
                    best_move = move
                
                alpha = max(alpha, best)
                if beta <= alpha:
                    break

            return best, best_move
   
        else:
            best = 10
            best_move = None
            for move in game.available_moves():

                temp_game = deepcopy(game)
                temp_game.player_move(move, self.opponent)
                score = self.minimax(temp_game, True, alpha, beta)[0]
                if score < best:
                    best = score
                    best_move = move
                beta = min(beta, best)
                if beta <= alpha:
                    break

            return best, best_move

    def get_move(self, game : Gameplay):
        """Returns a move for the computer based on the difficulty level"""
        if self.difficulty == 1:
            # choose a random move the board
            return self.easy_move(game)
        
        if self.difficulty == 2:
            move_selection = random()
            # create 50/50 chance of choosing a random move or using minimax
            if move_selection < 0.5:
                return self.easy_move(game)
            return self.minimax(game, game.turn == self.player)[1]

        # use minimax to choose the best move --unbeateable
        if self.difficulty == 3:

            # if first move, choose a random move
            if len(game.available_moves()) == 9:
                return self.easy_move(game)
            
            _, move = self.minimax(game, game.turn == self.player)
            return move
