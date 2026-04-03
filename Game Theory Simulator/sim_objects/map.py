class Map(object):
    def __init__(self, players):
        self.__count = int(players)

    def init_adj_matrix(self):
        matrix = [[0] * self.__count for _ in range(self.__count) ]
        for i in range(self.__count):
            for j in range(self.__count):
                matrix[i][j] = 1

        return matrix
