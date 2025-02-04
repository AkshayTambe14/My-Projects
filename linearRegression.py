#To calculate a least squares regresson line (LSRL):
#Find sum of x, y, x^2 and xy
#Calculate gradient: (n * sum(xy) - sum(x)*sum(y)) / (n * sum(x^2) - (sum(x))^2 )
#Calculate y-intercept: (sum(y) - m * sum(x)) / n
#Where n is the number of points and m is the gradient
import matplotlib.pyplot as plt
import numpy as np

class LSRL(object):
    def __init__(self):
        self.x_list = []
        self.y_list = []
        self.line = ""

    def sum(self, list_to_sum):
        total = 0
        for num in list_to_sum:
            total += num
        return total

    def sum_squares(self, list_to_sum):
        total = 0 
        for num in list_to_sum:
            to_add = num**2
            total += to_add
        return total
    
    def sum_two_params(self, list_one, list_two):
        total = 0
        for i in range(len(list_one)):
            to_add = list_one[i]*list_two[i]
            total += to_add
        return total

    def gradient(self):
        if len(self.x_list) != len(self.y_list):
            raise Exception("Data Incomplete")
        
        n = len(self.x_list)

        numerator = (n * self.sum_two_params(self.x_list, self.y_list)) - (sum(self.x_list)*sum(self.y_list))
        denominator = (n * self.sum_squares(self.x_list)) - (sum(self.x_list)**2)

        return numerator/denominator
    
    def intercept(self):
        m = self.gradient()
        #Calculate y-intercept: (sum(y) - m * sum(x)) / n
        return (sum(self.y_list) - (m * sum(self.x_list))) / len(self.x_list)

    def create_line(self):
        m = round(self.gradient(),3)
        b = round(self.intercept(),3)

        self.line = f"y = {m}x + {b}"
        return m,b

    def make_prediction(self, x_val):
        m = self.gradient()
        b = self.intercept()

        y_val = (m*x_val) + b

        return round(y_val,3)

    def plot_graph(self):
        m,b = self.create_line()
        x_line = np.linspace(min(self.x_list) - 1, max(self.x_list) + 1, 100)
        y_line = m * x_line + b 

        plt.figure(figsize=(8, 6))

        # Scatter plot for points
        plt.scatter(self.x_list, self.y_list, color='red', label='Data Points')

        # Line plot for equation
        plt.plot(x_line, y_line, color='blue', label=f"y = {m}x + {b}")

        # Labels and title
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.title('Scatter Plot with Line')
        plt.legend()
        plt.grid(True)
        plt.show()


app = LSRL()
#Input for x data (label and values)
x_label = input("What is the independent variable?: ")
x = input(f"{x_label} values (space in between each): ")
x_data = [int(_) for _ in x.split()]
app.x_list = x_data

#Input for y data (label and value)
y_label = input("What is the dependent variable?: ")
y = input(f"{y_label} values (space in between each): ")
y_data = [int(_) for _ in y.split()]
app.y_list = y_data

inp = int(input("> "))
print(app.make_prediction(inp))

_ = input("Do you want the graph? (y or n) > ").lower()
if _ == "y": app.plot_graph()
else: exit()