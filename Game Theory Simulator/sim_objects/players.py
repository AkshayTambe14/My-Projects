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
    
    def reset_points(self):
        self.__points = 0
