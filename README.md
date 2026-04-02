# My Projects/Programs
1. Trigonometry Programs (C/Python): Uses Taylor Series approximations to compute trigonometric functions on an input.

2. Linear Regression Line (Python): A simple model that fits a straight line to a set of data points using the least squares method. The resulting equation is used to predict and output value.

3. Multiple Regression Line (Python): A multiple regression model built from scratch in python without any external libraries. Uses the least squares method to calculate a gradient and intercept for each input variable. The fitted equation is used to predict a specified output value.

4. Neural Network (Python): A Neural Network trained to recognise and classify handwritten digits from the MNIST dataset. Trained using a sigmoid activation function, with the output layers having a softmax activation function. The loss function used was cross-entropy loss. The network has a 5 layer architecture, with support for saving and loading models using JSON.

5. K-Means Clustering (Python): A K-Means clustering algorithm trained to group randomly generated data points into clusters. Points are assigned to the nearest centroid using Euclidean distance, with centroids recalculated as the mean of their cluster after a new point is added. The results are visualised using Matplotlib, displaying the original and updated centroid positions on a scatter plot.

6. Chronocare Appointment Management System (Python Flask/HTML/JS/PostgreSQL): Chronocare is a full stack web application using Flask, PostgreSQL and TailwindCSS, desinged specifically for improving the appointment booking systems for doctors, patients and administrators. The system has appointment management, clinical notetaking and patient record access allowing doctors and administrators alike to complete many tasks under one application. It also includes a voice-to-text transcription feature using Vosk's API as well as automated email reminders queued using a custom built dynamic queue data structure.

The two key goals of the project was the data security and the schedule optimisation. Every piece of sensitive data is encrypted using a fully self implemented AES-256 algorithm, while passwords are protected using a self made SHA-256 hashing algorithm, that includes unique salting per user. I built a priority scheudling algorithm that generates available appointment times for patients to request appointments. Doctors can optimise specific days in their schedule by triggering a custom simulated annealing optimisation algorithm, that iteratively creates and then evaluates schedules, by penalising overlaps, gaps and late finishes.
