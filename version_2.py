import math
import random
import json
import pandas as pd


class Neuron(object):  # Base neuron class
    def __init__(self, inputs):
        self.output = None
        self.bias = random.uniform(-0.5, 0.5)
        self.weights = [random.uniform(-0.5, 0.5) for _ in range(inputs)]
        self.error_contribution = 0  # How much this neuron contributed to total error
        # The most recent inputs used in a forward pass, to ensure the original inputs remain the same
        self.prev_inputs = []
        self.weight_gradients = []
        self.bias_gradient = 0

    def weighted_sum(self, inputs):  # ∑w*x + b
        if len(inputs) != len(self.weights):  # Every input must have a weight
            raise ValueError("Input and weight amounts must match")

        self.prev_inputs = inputs
        weighted_sum = 0
        for i in range(len(inputs)):  # Loop to calculate weighted sum
            weighted_sum += self.weights[i] * inputs[i]
        weighted_sum += self.bias

        # Apply activation function (like sigmoid) to produce output
        self.output = self.activation_function(weighted_sum)
        return self.output

    def activation_function(self, unactivated_output):
        return unactivated_output

    # Calculates gradients of weights and biases for backpropagation
    def gradients_calculator(self):
        # Calculates the partial derivatives of loss, with respect to each weight
        self.weight_gradients = [
            self.error_contribution * x for x in self.prev_inputs]
        # Calculates gradient of loss with respect to the bias
        self.bias_gradient = self.error_contribution

    # Changes weights based on gradient descent function
    def change_weights(self, learning_rate):
        for i in range(len(self.weights)):
            # wi​ = wi − learning rate × gradient of wi
            self.weights[i] -= learning_rate * self.weight_gradients[i]
        # b​ = b − learning rate × gradient of b
        self.bias -= learning_rate * self.bias_gradient

    def dictify(self):
        return {
            'bias': self.bias,
            'weights': self.weights
        }

    def load_from_dict(self, data):
        self.bias = data['bias']
        self.weights = data['weights']

class Sigmoid(Neuron):  # Neuron with σ(z) activation function
    # Sigmoid 'squishification function'
    def activation_function(self, unactivated_output):
        return 1 / (1 + math.exp(-unactivated_output))

    # Derivative of sigmoid function and indicates the sensitivity of its output to its inputs
    def back_derivative(self):
        return self.output * (1 - self.output)  # σ′(x) = σ(x)⋅(1 − σ(x))

class Layer(object):  # Class for each layer
    def __init__(self, number_of_neurons, inputs):
        # Layer with specified number of neurons
        self.neurons = [Sigmoid(inputs) for _ in range(number_of_neurons)]
        self.last_inputs = []  # Stores most recent inputs to the layer

    def forward(self, inputs):  # Passes inputs from last layer into current layer and collects outputs
        self.last_inputs = inputs
        # Activating all neurons in the layer to create outputs
        return [neuron.weighted_sum(inputs) for neuron in self.neurons]

    # Calculates the error contributions for each layer and updates each neurons gradients
    def backward(self, next_layer):
        error_signals = []  # Error contributions
        # Goes through all neurons in this layer
        for i, neuron in enumerate(self.neurons):

            # Calculates the weighted sum of error signals from the next layers neurons
            next_layer_error_sum = sum(
                neur.weights[i] * neur.error_contribution for neur in next_layer.neurons)
            # Computes derivative of activation function for each neuron
            neuron.error_contribution = next_layer_error_sum * neuron.back_derivative()

            error_signals.append(neuron.error_contribution)

        for neuron in self.neurons:  # Calculates he gradients for each neuron in the layer
            neuron.prev_inputs = self.last_inputs
            neuron.gradients_calculator()

        return error_signals  # Used for updating weights and biases

class SoftMaxLayer(Layer):
    def __init__(self, number_of_neurons, inputs):
        # Layer with specified number of neurons
        self.neurons = [Neuron(inputs) for _ in range(number_of_neurons)]
        self.last_inputs = []  # Stores most recent inputs to the layer

    def forward(self, inputs):  # Passes inputs from last layer into current layer and collects outputs
        self.last_inputs = inputs
        # Activating all neurons in the layer to create outputs
        z = [neuron.weighted_sum(inputs) for neuron in self.neurons]
    
        max_z = max(z)
        exp_z = [math.exp(x - max_z) for x in z]
        sum_exp_z = sum(exp_z)

        softmax_outputs = [x / sum_exp_z for x in exp_z]

        for i, neuron in enumerate(self.neurons):
            neuron.output = softmax_outputs[i]

        return softmax_outputs
    
    def backward(self, expected_output):
        for i, neuron in enumerate(self.neurons):
            neuron.error_contribution = neuron.output - expected_output[i]
            neuron.gradients_calculator()

class Network(object):  # Class with all layers
    def __init__(self, layer_sizes):
        # Forms network from layers of specified sizes
        self.layers = [Layer(layer_sizes[i+1], layer_sizes[i]) for i in range(len(layer_sizes) - 2)]
        self.layers.append(SoftMaxLayer(layer_sizes[-1], layer_sizes[-2]))

    def feed_forward(self, inputs):  # Feeds inputs through to each layer
        for layer in self.layers:
            inputs = layer.forward(inputs)
        return inputs

    def backpropagation(self, expected_output, learning_rate=0.1):
        # Specifies which layer is the final layer
        output_layer = self.layers[-1]

        if isinstance(output_layer, SoftMaxLayer):
            # Softmax and Cross-Entropy loss uses simplified derivative
            output_layer.backward(expected_output)
        else:
            # Calculate error for non-softmax output neurons
            for i, neuron in enumerate(output_layer.neurons):
                error_derivative = 2 * (neuron.output - expected_output[i])
                neuron.error_contribution = error_derivative * neuron.back_derivative()
                neuron.gradients_calculator()

        # Continue with backpropagation for hidden layers
        for i in range(len(self.layers) - 2, -1, -1):
            current_layer = self.layers[i]
            next_layer = self.layers[i+1]
            current_layer.backward(next_layer)

        self.update_weights(learning_rate)

    # Changes weights for each neuron in each layer
    def update_weights(self, learning_rate):
        for layer in self.layers:
            for neuron in layer.neurons:
                neuron.change_weights(learning_rate)

    # Loss function, calculates the difference between desired and actual output before squaring it
    def mean_squared_error(self, expected_outputs, actual_outputs):
        total = 0
        for i in range(len(expected_outputs)):
            error_squared = (expected_outputs[i] - actual_outputs[i])**2
            total += error_squared
        # MSE = ∑(expected - actual)^2 / n
        return total / len(expected_outputs)

    def cross_entropy_loss(self, expected_outputs, actual_outputs):
        epsilon = 1e-12
        return -sum(y * math.log(p + epsilon) for y, p in zip(expected_outputs, actual_outputs))

def save(network, filename="network.json"):
    data = {
        "layers": [
            {"neurons": [neuron.dictify() for neuron in layer.neurons]}
            for layer in network.layers
        ]
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def load(filename="network.json"):
    with open(filename, "r") as f:
        data = json.load(f)

    layer_sizes = [len(layer['neurons']) for layer in data['layers']]
    network = Network(layer_sizes)

    for layer, layer_data in zip(network.layers, data['layers']):
        for neuron, neuron_data in zip(layer.neurons, layer_data['neurons']):
            neuron.load_from_dict(neuron_data)

    return network


def import_data():
    train_data = pd.read_csv('train.csv')
    labels = train_data['label'].values  # Get the labels (digits)
    # Drop the label column to get the pixel values
    images = train_data.drop(columns=['label']).values
    # MNIST images are between 0-255, so we divide by 255 to normalize
    images = images / 255.0
    images = images.reshape(-1, 28, 28)  # Reshape to (num_samples, 28, 28)
    images = images.reshape(images.shape[0], -1)
    return images, labels


def train(network, epochs, learning_rate, batch_size, images, labels, data_size):
    for epoch in range(epochs):
        total_loss = 0  # This accumulates total loss across all batches for current epoch
        correct_predictions = 0

        indices = list(range(data_size))
        random.shuffle(indices)
        shuffled_images = images[indices]
        shuffled_labels = labels[indices]

        # len(images) Iterates through dataset in batches, for each gradient descent updates
        for i in range(0, data_size, batch_size):
            # Creates batchsize subset of images from data set
            batch_images = shuffled_images[i:i+batch_size]
            # List of labels for that batch
            batch_labels = [int(label) for label in shuffled_labels[i:i+batch_size]]
            batch_loss = 0

            for img, label in zip(batch_images, batch_labels):
                inputs = img.flatten()
                target = [0] * 10
                target[int(label)] = 1

                output = network.feed_forward(inputs)
                loss = network.cross_entropy_loss(target, output)
                batch_loss += loss

                if output.index(max(output)) == label:
                    correct_predictions += 1

                network.backpropagation(target, learning_rate=learning_rate)
            network.update_weights(learning_rate)

            total_loss += batch_loss / len(batch_images)

        mean_loss = total_loss / (data_size / batch_size)
        accuracy = correct_predictions / data_size * 100
        print(f"Epoch {epoch+1}/{epochs}, Loss: {mean_loss:.4f}, Accuracy: {accuracy:.2f}%")


def evaluate(network, images, labels, num_samples=1000):
    correct = 0
    total_loss = 0
    
    for i in range(num_samples):
        image = images[i]
        label = int(labels[i])
        
        target = [0] * 10
        target[label] = 1
        
        output = network.feed_forward(image.flatten())
        loss = network.cross_entropy_loss(target, output)
        total_loss += loss
        
        predicted = output.index(max(output))
        if predicted == label:
            correct += 1
    
    accuracy = (correct / num_samples) * 100
    avg_loss = total_loss / num_samples
    
    return accuracy, avg_loss


def check(network, image, label):
    output = network.feed_forward(image.flatten())
    #print(max(output))
    #print(f"Predicted: {output.index(max(output))}")
    #print(f"Meant to be: {label}")
    if output.index(max(output)) == label:
        print("Success")
    else:
        print("Fail")


def main():
    network = Network([784, 128, 64, 16, 10])
    epochs = 250
    learning_rate = 0.12
    batch_size = 32
    dataset_size = 25000
    
    images, labels = import_data()
    
    # Split into training and validation sets
    val_size = 2000
    train_images = images[:dataset_size-val_size]
    train_labels = labels[:dataset_size-val_size]
    val_images = images[dataset_size-val_size:dataset_size]
    val_labels = labels[dataset_size-val_size:dataset_size]
    
    # Train or load pre-trained model
    train_model = True  # Set to False to load pre-trained
    
    if train_model:
        train(network, epochs, learning_rate, batch_size, train_images, train_labels, len(train_images))
        save(network, "250epoch_25000size_0.12learn_32batch_5layer_softmax.json")
    else:
        network = load("250epoch_25000size_0.12learn_32batch_5layer_softmax.json")
    
    # Evaluate on validation set
    val_accuracy, val_loss = evaluate(network, val_images, val_labels)
    print(f"Validation Accuracy: {val_accuracy:.2f}%, Loss: {val_loss:.4f}")
    
    # Test on specific examples
    num_test = 100
    for i in range(num_test):
        test_idx = dataset_size + i  # Use examples outside training set
        test_image = images[test_idx]
        test_label = int(labels[test_idx])
        
        output = network.feed_forward(test_image.flatten())
        predicted = output.index(max(output))
        
        print(f"Example {i+1}: Predicted {predicted}, Actual {test_label}, {'✓' if predicted == test_label else '✗'}")

main()
