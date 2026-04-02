import matplotlib.pyplot as plt
import numpy as np
import random

class clustering:
    def __init__(self):
        self.fig,self.ax = plt.subplots()
        self.centroids = [[None,None],[None,None],[None,None]]
        self.clusters = [[],[],[]]
        self.centroid_colours = ['blue']
        self.colours = ['black','yellow','red','green','#eb7734']
        self.create_centroids()

    def main(self):
        for point in self.centroids:
            x1 = point[0]
            y1 = point[1]
            self.ax.scatter(x1, y1, color='#6347ff')
            self.ax.text(x1, y1, "OG", fontsize=12, ha='right', va='bottom', color='black')


        print(self.centroids)
        for i in range(5):
            x = random.randint(0,15)
            y = random.randint(0,15)
            self.closest_centroid(x,y)
            self.ax.scatter(x,y,color = self.colours[i])

        for _ in self.centroids:
            x2 = _[0]
            y2 = _[1]
            self.ax.scatter(x2, y2, color='blue')
            self.ax.text(x2, y2, "NEW", fontsize=12, ha='right', va='bottom', color='black')

            

        print(self.centroids)
        print(self.clusters)
        plt.show()

    def create_centroids(self):
        #Create random data points to base clusters around
        for i in range(3):
            x = random.randint(0,10) + (2*i)
            y = random.randint(0,10) + (2*i)
            self.centroids[i] = [x,y]

    def closest_centroid(self, x, y):
        #Finds which centroid is closest, and adds it to that cluster
        lowest = 0  # Initialize the index of the closest centroid
        min_distance = self.distance(self.centroids[0][0], self.centroids[0][1], x, y)

        for i in range(1, len(self.centroids)): #Goes through centroids and finds the lowest distance one from point
            current_distance = self.distance(x, self.centroids[i][0], y, self.centroids[i][1])
            
            if current_distance < min_distance:
                min_distance = current_distance
                lowest = i 

        self.clusters[lowest].append((x, y)) #Adding new point to its relevent cluster
        self.update_cluster_centroid(self.clusters[lowest],lowest) #So that when a point is added, the new centroid is calculated
        
        
    def update_cluster_centroid(self,group,i):
        #Group is a sub-array, i is the index of the group in clusters, and the centroid in centroids
        #Whenever a new datapoint is added, depending on which cluster is added to, the centroid of the cluster changes
        #It does this by taking the mean of all data points' x and y values in cluster and making a mean value
        x_total = 0
        y_total = 0
        for point in group:
            #Calculating totals for means of all points in that cluster
            x_total += point[0]
            y_total += point[1]

        self.centroids[i] = [x_total / len(group), y_total / len(group)] #Calculates new centroid, replaces original centroid of that cluster

    def distance(self,x1,y1,x2,y2):
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

app = clustering()
app.main()