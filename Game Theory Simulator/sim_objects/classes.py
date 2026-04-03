class Game(object):
    def __init__(self, name):
        self.__name = name
        self.__matrix = self.__create_matrix(name)

    def __create_matrix(self, game):
        matrix = [[0,0] for _ in range(4)]
        if game == "PD":
            matrix[0] = [3,3]
            matrix[1] = [0,5]
            matrix[2] = [5,0]
            matrix[3] = [1,1]

        elif game == "SH":
            matrix[0] = [4,4]
            matrix[1] = [0,3]
            matrix[2] = [3,0]
            matrix[3] = [3,3]

        return matrix
    
    def get_matrix(self):
        return self.__matrix
       
class Map(object):
    def __init__(self, players):
        self.__count = int(players)

    def init_adj_matrix(self):
        matrix = [[0] * self.__count for _ in range(self.__count) ]
        for i in range(self.__count):
            for j in range(self.__count):
                matrix[i][j] = 1

        return matrix

class Player(object):
    def __init__(self, name, strategy):
        self.__name = name
        self.__strategy = strategy 
        self.__points = 0

    def get_strategy(self):
        return self.__strategy
    
    def get_points(self):
        return self.__points
    
    def add_points(self, points):
        self.__points += points

    def get_name(self):
        return self.__name
    
import random

class Strategy(object):
    def __init__(self):
        self.__history = {}

    def make_move(self, opponent_history=None):
        """Base method - should be overridden by subclasses"""
        pass

    def reset(self):
        self.__history.clear()

class Tit_For_Tat(Strategy):
    def __init__(self):
        super().__init__()

    def make_move(self, opponent_history=None):
        if not opponent_history:
            return 1  # Cooperate on first move
        return opponent_history[-1]  # Copy opponent's last move
    
class Always_Cooperate(Strategy):
    def __init__(self):
        super().__init__()
        self.cooperativity = 1

    def make_move(self, opponent_history=None):  # Add optional parameter
        return 1

    def add_performance(self, points):
        """Dummy method for compatibility"""
        pass

class Always_Defect(Strategy):
    def __init__(self):
        super().__init__()
        self.cooperativity = 0

    def make_move(self, opponent_history=None):  # Add optional parameter
        return 0

    def add_performance(self, points):
        """Dummy method for compatibility"""
        pass
    
class Random_Choice(Strategy):
    def __init__(self):
        super().__init__()
        self.cooperativity = 0.5

    def make_move(self, opponent_history=None):  # Add optional parameter
        return random.choice([1,0])

    def add_performance(self, points):
        """Dummy method for compatibility"""
        pass
    
class Custom(Strategy):
    def __init__(self, cooperativity=0.5):
        super().__init__()
        self.cooperativity = max(0.0, min(1.0, cooperativity))  # Clamp between 0 and 1
        self.performance_history = []  # Track recent performance
        self.max_history = 20  # Keep last 20 games
        self.games_played = 0
        self.total_score = 0

    def make_move(self):
        """Make a move based on cooperativity probability"""
        check_num = random.random()  # Use random.random() for float between 0-1
        return 1 if check_num < self.cooperativity else 0

    def add_performance(self, points):
        """Add performance data for strategy updating"""
        self.performance_history.append(points)
        self.games_played += 1
        self.total_score += points
        
        # Keep only recent history
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)

    def get_recent_performance(self):
        """Get recent performance data"""
        return self.performance_history.copy()

    def get_average_performance(self):
        """Get average performance over all games"""
        if self.games_played == 0:
            return 0
        return self.total_score / self.games_played

    def adjust_cooperativity(self, adjustment):
        """Adjust cooperativity level"""
        old_cooperativity = self.cooperativity
        self.cooperativity = max(0.0, min(1.0, self.cooperativity + adjustment))
        return self.cooperativity != old_cooperativity  # Return True if changed

    def reset(self):
        """Reset strategy state"""
        super().reset()
        self.performance_history = []
        self.games_played = 0
        self.total_score = 0

    def get_strategy_info(self):
        """Get detailed strategy information"""
        return {
            'cooperativity': self.cooperativity,
            'games_played': self.games_played,
            'average_score': self.get_average_performance(),
            'recent_performance': self.get_recent_performance()
        }
    
class Grudger(Strategy):
    def __init__(self):
        super().__init__()
        self.has_been_defected = False

    def make_move(self, opponent_history=None):
        if opponent_history and 0 in opponent_history:
            self.has_been_defected = True
        
        return 0 if self.has_been_defected else 1

    def reset(self):
        super().reset()
        self.has_been_defected = False

    def add_performance(self, points):
        """Dummy method for compatibility"""
        pass

class Pavlov(Strategy):
    def __init__(self):
        super().__init__()
        self.last_move = 1
        self.last_payoff = 0

    def make_move(self, opponent_history=None):
        # Win-stay, lose-shift strategy
        if self.last_payoff >= 3:  # Cooperate if last payoff was good
            return self.last_move
        else:  # Switch if last payoff was bad
            self.last_move = 1 - self.last_move
            return self.last_move

    def add_performance(self, points):
        """Track last payoff for decision making"""
        self.last_payoff = points

    def reset(self):
        super().reset()
        self.last_move = 1
        self.last_payoff = 0
