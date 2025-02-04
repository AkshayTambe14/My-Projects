# y = b + m1*x + m2*z
# b = mean(y) - m1*mean(x) - m2*mean(z)

def custom_sum(list_to_sum):
        total = 0
        for num in list_to_sum:
            total += num
        return total

def mean(array):
        bar = custom_sum(array)/len(array)
        return bar

def create_gradients(dim_count, data, gradients, y_list):
    mean_y = mean(y_list)
    for i in range(dim_count):
        cov = custom_sum((data[i][j] - mean(data[i])) * (y_list[j] - mean_y) for j in range(n) ) / n
        var = custom_sum((data[i][j] - mean(data[i])) ** 2 for j in range(n)) / n
        m = cov/var
        gradients.append(m)
    return gradients
       
def intercept(dim_count, data, gradients, y_list):

        mean_y = mean(y_list)
        for i in range(dim_count):
               mean_y -= gradients[i]*mean(data[i])

        return mean_y

def make_prediction(dim_count, data, gradients, inputs, y_list):
        total = 0
        b = intercept(dim_count,data,gradients,y_list)
        for i,gradient in enumerate(gradients):
              total += gradient*inputs[i]

        return round(total + b,3)

data_set = [
        ]

dimensions = int(input("How many variables? > "))
for i in range(dimensions):
      bdata = input(f"Input {dimensions} b{i+1} values with a space in between each one > ")
      _ = bdata.split()
      processed_list = [int(item) for item in _]
      data_set.append(processed_list)

y_inp = input(f"Input {dimensions} y values with a space in between each one > ")
y_split = y_inp.split()
y = [int(item) for item in y_split]

n = len(y)
gradient_list = []

dim_inp = input(f"Input {dimensions} values with a space in between each one for which you want to predict an output > ")
dim_split = dim_inp.split()
dims = [int(item) for item in dim_split]

create_gradients(dimensions, data_set, gradient_list, y)
print(make_prediction(dimensions,data_set,gradient_list,dims, y))
