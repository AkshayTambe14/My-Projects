class Game(object):
    def __init__(self, name):
        self.__name = name
        self.__matrix = self.__create_matrix(name)

    def __create_matrix(self, game):
        matrix = [[0,0] for _ in range(4)]
        if game == "Prisoner's Dilemma":
            matrix[0] = [3,3]
            matrix[1] = [0,5]
            matrix[2] = [5,0]
            matrix[3] = [1,1]

        elif game == "Stag Hunt":
            matrix[0] = [4,4]
            matrix[1] = [0,3]
            matrix[2] = [3,0]
            matrix[3] = [3,3]

        return matrix
    
    def get_matrix(self):
        return self.__matrix
