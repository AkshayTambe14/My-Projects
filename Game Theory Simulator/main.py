import math
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.messagebox import showerror
import csv
from datetime import datetime

from GUI import Paramter_Set_Window, Player_Set_Window
from sim_objects import *


class Simulation(object):
    """Initialisation"""
    def __init__(self, root, players, params):
        self.__root = root
        self.__root.title("Game Theory Simulation")
        
        # Window setup
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Store parameters and player data
        self.__players_data = players
        self.__params = params
        self.__player_objects = self.__create_player_objects()
        
        # Create map
        num_players = len(self.__player_objects)
        map_obj = Map(num_players)
        self.__map = map_obj.init_adj_matrix()

        # UI elements
        self.__canvas = None
        self.__player_positions = {}
        self.__score_texts = {}
        self.__current_iteration = 0
        self.__is_running = False
        
        # Game state tracking
        self.__game_histories = {}  # Track histories for each player pair
        self.__step_through_mode = False
        self.__waiting_for_step = False
        self.__export_data = []
        
        self.__create_ui()
    def __create_player_objects(self):
        #Converts raw player data into Player objects with their associated strategy classes
        #Called in initialisation to turn the player data into objects that can make moves and track scores

        strategy_classes = {
            "Always Cooperate": Always_Cooperate,
            "Always Defect": Always_Defect,
            "Random": Random_Choice,
            "Tit-for-Tat": Tit_For_Tat,
            "Custom": Custom,
            "Grudger": Grudger,
            "Pavlov": Pavlov
        }
        
        players = {}
        for name, data in self.__players_data.items():
            if isinstance(data, dict):
                strategy_name = data.get("strategy", "Random")
                cooperativity = data.get("cooperativity", 0.5)
            elif isinstance(data, str):
                strategy_name = data
                cooperativity = 0.5
            else:
                strategy_name = "Random"
                cooperativity = 0.5
            
            if strategy_name == "Custom":
                strategy = Custom(cooperativity)
            else:
                strategy_class = strategy_classes.get(strategy_name, Random_Choice)
                strategy = strategy_class()
            
            players[name] = Player(name, strategy)
        
        return players  
    def __create_ui(self):
        #Builds the graphical user interface including the visual player display, player/game selection, buttons, results and the status bar

        control_frame = tk.Frame(self.__root)
        control_frame.pack(pady=10)
        
        player_row = 0
        tk.Label(control_frame, text="Player 1:").grid(row=player_row, column=0, padx=5)
        self.__player1_var = tk.StringVar()
        player_names = list(self.__player_objects.keys())
        self.__player1_dropdown = ttk.Combobox(control_frame, textvariable=self.__player1_var, values=player_names, state="readonly", width=15)
        if player_names:
            self.__player1_dropdown.set(player_names[0])
        self.__player1_dropdown.grid(row=player_row, column=1, padx=5)
        
        tk.Label(control_frame, text="Player 2:").grid(row=player_row, column=2, padx=5)
        self.__player2_var = tk.StringVar()
        self.__player2_dropdown = ttk.Combobox(control_frame, textvariable=self.__player2_var, values=player_names, state="readonly", width=15)
        if len(player_names) > 1:
            self.__player2_dropdown.set(player_names[1])
        self.__player2_dropdown.grid(row=player_row, column=3, padx=5)
        
        tk.Label(control_frame, text="Game:").grid(row=player_row, column=4, padx=5)
        self.__game_var = tk.StringVar()
        self.__game_dropdown = ttk.Combobox(control_frame, textvariable=self.__game_var, values=["Prisoner's Dilemma", "Stag Hunt"], state="readonly", width=10)
        self.__game_dropdown.set("Prisoner's Dilemma")
        self.__game_dropdown.grid(row=player_row, column=5, padx=5)
        
        button_row = 1
        tk.Label(control_frame, text="Iterations:").grid(row=button_row, column=0, padx=5)
        self.__iterations_var = tk.StringVar(value=str(self.__params.get("Iteration Number", 100)))
        self.__iterations_entry = tk.Entry(control_frame, textvariable=self.__iterations_var, width=10)
        self.__iterations_entry.grid(row=button_row, column=1, padx=5)
        
        tk.Label(control_frame, text="Speed:").grid(row=button_row, column=2, padx=5)
        self.__speed_var = tk.StringVar(value="Normal")
        self.__speed_dropdown = ttk.Combobox(control_frame, textvariable=self.__speed_var, values=["Slow", "Normal", "Fast"], state="readonly", width=10)
        self.__speed_dropdown.grid(row=button_row, column=3, padx=5)
        
        button_frame = tk.Frame(self.__root)
        button_frame.pack(pady=10)
        
        self.__run_single_button = tk.Button(button_frame, text="Run Single Game", command=self.__run_single_game)
        self.__run_single_button.pack(side="left", padx=5)
        
        self.__run_iterative_button = tk.Button(button_frame, text="Run Iterative Games", command=self.__run_iterative_games)
        self.__run_iterative_button.pack(side="left", padx=5)
        
        self.__run_tournament_button = tk.Button(button_frame, text="Run Tournament", command=self.__run_tournament)
        self.__run_tournament_button.pack(side="left", padx=5)
        
        self.__stop_button = tk.Button(button_frame, text="Stop", command=self.__stop_simulation, state="disabled")
        self.__stop_button.pack(side="left", padx=5)
        
        self.__reset_button = tk.Button(button_frame, text="Reset Scores", command=self.__reset_scores)
        self.__reset_button.pack(side="left", padx=5)
        
        results_frame = tk.LabelFrame(self.__root, text="Game Results", padx=5, pady=5)
        results_frame.pack(pady=10, fill="both", expand=True)
        
        text_frame = tk.Frame(results_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.__results_text = tk.Text(text_frame, height=8, wrap="word", font=("Courier", 10))
        scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=self.__results_text.yview)
        self.__results_text.configure(yscrollcommand=scrollbar.set)
        
        self.__results_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.__status_label = tk.Label(self.__root, text="Ready", relief="sunken", anchor="w")
        self.__status_label.pack(side="bottom", fill="x")
        
        self.__step_button = tk.Button(button_frame, text="Step Through", command=self.__toggle_step_through)
        self.__step_button.pack(side="left", padx=5)
        
        self.__next_step_button = tk.Button(button_frame, text="Next Step", command=self.__next_step, state="disabled")
        self.__next_step_button.pack(side="left", padx=5)
        
        self.__export_button = tk.Button(button_frame, text="Export Results", command=self.__export_results)
        self.__export_button.pack(side="left", padx=5)

        self.__show_players()
    

    """Game Execution"""
    def __run_single_game(self):
        #Performs one game between two chosen players and gets/created a history for the pair. 
        #Plays the game with an animation and calculates the results. Displays outcome with move details and new scores

        player1_name = self.__player1_var.get()
        player2_name = self.__player2_var.get()
        game_type = self.__game_var.get()
        
        if not self.__validate_player_selection(player1_name, player2_name):
            return
        
        player1 = self.__player_objects[player1_name]
        player2 = self.__player_objects[player2_name]
        
        pair_key = self.__get_pair_key(player1_name, player2_name)
        if pair_key not in self.__game_histories:
            self.__game_histories[pair_key] = {"p1_history": [], "p2_history": []}
        
        result = self.__play_single_game(player1, player2, game_type, pair_key, animate=True)
        
        if result:
            p1_points, p2_points, p1_move, p2_move = result
            move_names = {0: "Defect", 1: "Cooperate"}
            
            result_text = f"=== SINGLE GAME RESULT ===\n"
            result_text += f"Game: {game_type} | {player1_name} vs {player2_name}\n"
            result_text += f"Moves: {player1_name}({move_names[p1_move]}) vs {player2_name}({move_names[p2_move]})\n"
            result_text += f"Points: {player1_name}: +{p1_points}, {player2_name}: +{p2_points}\n"
            result_text += f"Total Scores: {player1_name}: {player1.get_points()}, {player2_name}: {player2.get_points()}\n\n"
            
            self.__display_result(result_text)
            self.__update_score_display()
    def __run_iterative_games(self):
        #Begins a series of games between two chosen players
        #Begins iterative process by calling the run iteration method

        if self.__is_running:
            return
        
        player1_name = self.__player1_var.get()
        player2_name = self.__player2_var.get()
        game_type = self.__game_var.get()
        
        if not self.__validate_player_selection(player1_name, player2_name):
            return
        
        try:
            iterations = int(self.__iterations_var.get())
            if iterations <= 0:
                raise ValueError("Iterations must be positive")
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please enter a valid number of iterations (positive integer)")
            return
        
        self.__start_simulation()
        
        player1 = self.__player_objects[player1_name]
        player2 = self.__player_objects[player2_name]
        
        pair_key = self.__get_pair_key(player1_name, player2_name)
        self.__game_histories[pair_key] = {"p1_history": [], "p2_history": []}
        
        result_text = f"=== STARTING ITERATIVE GAMES ===\n"
        result_text += f"Players: {player1_name} vs {player2_name}\n"
        result_text += f"Game: {game_type} | Iterations: {iterations}\n\n"
        self.__display_result(result_text)
        
        self.__run_iteration(player1, player2, game_type, iterations, 0, pair_key)
    def __run_iteration(self, player1, player2, game_type, total_iterations, current_iteration, pair_key):
        #Executes one iteration, handles the step through mode, plays the game and updates strategy performance tracking.
        #It is called recursively to create the iterative game loop and manages the flow of repeated games with delay and updates

        if not self.__is_running or current_iteration >= total_iterations:
            self.__finish_iterative_games(player1, player2, total_iterations)
            return
        
        self.__current_iteration = current_iteration
        self.__status_label.config(text=f"Running iteration {current_iteration + 1}/{total_iterations}")
        
        if self.__step_through_mode:
            self.__wait_for_step()
            if not self.__is_running:  
                return
        
        animate = (current_iteration < 5)
        result = self.__play_single_game(player1, player2, game_type, pair_key, animate=animate)
        
        if result:
            p1_points, p2_points, p1_move, p2_move = result
            
            if hasattr(player1.get_strategy(), 'add_performance'):
                player1.get_strategy().add_performance(p1_points)
            if hasattr(player2.get_strategy(), 'add_performance'):
                player2.get_strategy().add_performance(p2_points)
            
            if ((current_iteration + 1) % 10 == 0 or 
                self.__step_through_mode or 
                total_iterations <= 20):
                
                move_names = {0: "Defect", 1: "Cooperate"}
                result_text = f"Iteration {current_iteration + 1}: "
                result_text += f"{player1.get_name()}({move_names[p1_move]}) vs "
                result_text += f"{player2.get_name()}({move_names[p2_move]}) | "
                result_text += f"Points: +{p1_points}/+{p2_points}\n"
                self.__display_result(result_text)
        
        if (current_iteration + 1) % 20 == 0:
            self.__update_strategies()
        
        self.__update_score_display()
        
        delay = self.__get_delay_ms() if not self.__step_through_mode else 100
        self.__root.after(delay, lambda: self.__run_iteration(player1, player2, game_type, total_iterations, current_iteration + 1, pair_key))
    def __run_tournament(self):
        #Organises a round-robin tournament where everyone plays each other

        if self.__is_running:
            return
        
        game_type = self.__game_var.get()
        
        try:
            iterations = int(self.__iterations_var.get())
            if iterations <= 0:
                raise ValueError("Iterations must be positive")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of iterations")
            return
        
        if len(self.__player_objects) < 2:
            messagebox.showwarning("Not Enough Players", "Need at least 2 players for a tournament")
            return
        
        self.__start_simulation()
        
        result_text = f"=== STARTING TOURNAMENT ===\n"
        result_text += f"Game: {game_type} | Iterations per match: {iterations}\n"
        result_text += f"Players: {', '.join(self.__player_objects.keys())}\n\n"
        self.__display_result(result_text)
        
        self.__game_histories = {}
        
        self.__run_tournament_matches(list(self.__player_objects.keys()), game_type, iterations, 0)
    def __run_tournament_matches(self, player_names, game_type, iterations, match_index):
        #Manages the tournament bracket by creating all the unique player pairs before running matches sequentially
        #Progress through matches is tracked and when the tournament is finished, the completion method is called

        pairs = []
        for i in range(len(player_names)):
            for j in range(i + 1, len(player_names)):
                pairs.append((player_names[i], player_names[j]))
        
        if match_index >= len(pairs):
            self.__finish_tournament()
            return
        
        if not self.__is_running:
            return
        
        player1_name, player2_name = pairs[match_index]
        self.__status_label.config(text=f"Tournament: {player1_name} vs {player2_name} (Match {match_index + 1}/{len(pairs)})")
        
        player1 = self.__player_objects[player1_name]
        player2 = self.__player_objects[player2_name]
        
        pair_key = self.__get_pair_key(player1_name, player2_name)
        self.__game_histories[pair_key] = {"p1_history": [], "p2_history": []}
        
        result_text = f"Match {match_index + 1}: {player1_name} vs {player2_name}\n"
        self.__display_result(result_text)
        
        self.__run_tournament_iteration(player1, player2, game_type, iterations, 0, pair_key, player_names, match_index)
    def __run_tournament_iteration(self, player1, player2, game_type, total_iterations, current_iteration, pair_key, player_names, match_index):
        #Runs the individual iterations in a tournament's matches
        #Slightly different to normal iterations, but progress updates less frequent and faster delays

        if not self.__is_running:
            return
        
        if current_iteration >= total_iterations:
            delay = self.__get_delay_ms() * 2  # Pause between matches
            self.__root.after(delay, lambda: self.__run_tournament_matches(player_names, game_type, total_iterations, match_index + 1))
            return
        
        animate = (current_iteration == 0)
        result = self.__play_single_game(player1, player2, game_type, pair_key, animate=animate)
        
        if result and (current_iteration + 1) % 20 == 0:  # Show progress every 20 iterations
            p1_points, p2_points, _, _ = result
            progress_text = f"  Iteration {current_iteration + 1}/{total_iterations} complete\n"
            self.__display_result(progress_text)
        
        self.__update_score_display()
        
        delay = max(1, self.__get_delay_ms() // 4)  # Faster for tournaments
        self.__root.after(delay, lambda: self.__run_tournament_iteration(
            player1, player2, game_type, total_iterations, current_iteration + 1, 
            pair_key, player_names, match_index))
    

    """Main Game Logic"""
    def __play_single_game(self, player1, player2, game_type, pair_key, animate=False):
        #Executes one complete game: gets payer moves based on their strategy and history.
        #Updates histories, calculates payoffs using the games' matrices and awards points
        #This is where the key game thoery mechanic is occuring

        game_obj = Game(game_type)
        
        histories = self.__game_histories[pair_key]
        p1_opponent_history = histories["p2_history"]
        p2_opponent_history = histories["p1_history"]
        
        try:
            if hasattr(player1.get_strategy(), 'make_move'):
                if 'opponent_history' in player1.get_strategy().make_move.__code__.co_varnames:
                    player1_move = player1.get_strategy().make_move(p1_opponent_history)
                else:
                    player1_move = player1.get_strategy().make_move()
            else:
                player1_move = 1  
                
            if hasattr(player2.get_strategy(), 'make_move'):
                if 'opponent_history' in player2.get_strategy().make_move.__code__.co_varnames:
                    player2_move = player2.get_strategy().make_move(p2_opponent_history)
                else:
                    player2_move = player2.get_strategy().make_move()
            else:
                player2_move = 1  
                
        except Exception as e:
            print(f"Error getting moves: {e}")
            player1_move, player2_move = 1, 1  
        
        histories["p1_history"].append(player1_move)
        histories["p2_history"].append(player2_move)
        
        if player1_move == 1 and player2_move == 1:     
            matrix_index = 0
        elif player1_move == 1 and player2_move == 0:  
            matrix_index = 1
        elif player1_move == 0 and player2_move == 1:   
            matrix_index = 2
        else:                                           
            matrix_index = 3
        
        payoff_matrix = game_obj.get_matrix()
        player1_points = payoff_matrix[matrix_index][0]
        player2_points = payoff_matrix[matrix_index][1]
        
        player1.add_points(player1_points)
        player2.add_points(player2_points)
        
        if animate:
            self.__play_game_with_animation(player1, player2)
        
        return (player1_points, player2_points, player1_move, player2_move)
    

    """Simulation Control"""
    def __start_simulation(self):
        #Switches the interface to a running mode by enabling/disabling specific buttons
        #Called at the start of any simulation run to stop multiple simulations happening at the same time

        self.__is_running = True
        self.__run_single_button.config(state="disabled")
        self.__run_iterative_button.config(state="disabled")
        self.__run_tournament_button.config(state="disabled")
        self.__stop_button.config(state="normal")
        
        if self.__step_through_mode:
            self.__next_step_button.config(state="normal")
    def __finish_simulation(self):
        #Returns the interface to the normal state by enabling/disabling specific buttons
        #Called when any simulation is completed to make sure the interface is ready for the next run

        self.__is_running = False
        self.__waiting_for_step = False
        self.__run_single_button.config(state="normal")
        self.__run_iterative_button.config(state="normal")
        self.__run_tournament_button.config(state="normal")
        self.__stop_button.config(state="disabled")
        self.__next_step_button.config(state="disabled")
        self.__status_label.config(text="Simulation completed")
    def __stop_simulation(self):
        #Force stops any running simulation and displays a stop message

        self.__is_running = False
        self.__finish_simulation()
        self.__status_label.config(text="Simulation stopped")
        self.__display_result("=== SIMULATION STOPPED ===\n\n")
    def __reset_scores(self):
        #Resets every players score to 0, resets strategy states and clears any histories

        for player in self.__player_objects.values():
            player.reset_points() 
        
        for player in self.__player_objects.values():
            if hasattr(player.get_strategy(), 'reset'):
                player.get_strategy().reset()
        
        self.__game_histories = {}
        self.__update_score_display()
        self.__results_text.delete(1.0, tk.END)
        self.__status_label.config(text="Scores and histories reset")
    

    """Completion"""
    def __finish_iterative_games(self, player1, player2, total_iterations):
        #Completes iterations by displaying final scores, the winner and any other summary stats

        self.__finish_simulation()
        
        final_text = f"\n=== ITERATIVE GAMES COMPLETE ===\n"
        final_text += f"Total iterations: {total_iterations}\n"
        final_text += f"Final Scores:\n"
        final_text += f"  {player1.get_name()}: {player1.get_points()} points\n"
        final_text += f"  {player2.get_name()}: {player2.get_points()} points\n"
        
        if player1.get_points() > player2.get_points():
            final_text += f"Winner: {player1.get_name()}\n"
        elif player2.get_points() > player1.get_points():
            final_text += f"Winner: {player2.get_name()}\n"
        else:
            final_text += "Result: Tie\n"
        
        final_text += "\n" + "="*50 + "\n\n"
        self.__display_result(final_text)
    def __finish_tournament(self):
        #Calculates the final rankings of tournament and displays them in order

        self.__finish_simulation()
        
        rankings = sorted(self.__player_objects.items(), key=lambda x: x[1].get_points(), reverse=True)
        
        final_text = f"\n=== TOURNAMENT COMPLETE ===\n"
        final_text += f"Final Rankings:\n"
        for i, (name, player) in enumerate(rankings, 1):
            final_text += f"  {i}. {name}: {player.get_points()} points\n"
        
        final_text += f"\nWinner: {rankings[0][0]}\n"
        final_text += "\n" + "="*50 + "\n\n"
        self.__display_result(final_text) 
    

    """Utility"""
    def __validate_player_selection(self, player1_name, player2_name):
        #Checks that two different players have been chosen

        if not player1_name or not player2_name:
            messagebox.showwarning("Invalid Selection", "Please select both players")
            return False
        if player1_name == player2_name:
            messagebox.showwarning("Invalid Selection", "Please select two different players")
            return False
        return True
    def __get_pair_key(self, player1_name, player2_name):
        #Creates a consistant identifier for pairs of players independent of order

        return tuple(sorted([player1_name, player2_name]))
    def __get_delay_ms(self):
        #Returns delay times based on the chosen speed

        speed = self.__speed_var.get()
        if speed == "Slow":
            return 500
        elif speed == "Fast":
            return 10
        else: 
            return 100
    def __get_hexagon_points(self, x, y, readius):
        #Calculates the six corner coordinates needed to draw a hexagon at a given center

        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            px = x + radius * math.cos(angle_rad)
            py = y + radius * math.sin(angle_rad)
            points.extend([px, py])
        return points


    """Display and Visualisation"""
    def __show_players(self):
        #Creates the visual canvas and arranges players as hexagons in a circle

        num_players = len(self.__player_objects)
        if num_players == 0:
            return
        
        self.__root.update_idletasks()  
        window_width = self.__root.winfo_width()
        window_height = self.__root.winfo_height()
        
        canvas_width = int(window_width * 0.95)
        canvas_height = int((window_height - 300) * 0.9)
        canvas_size = min(canvas_width, canvas_height, 800) 
        
        hex_radius = max(20, min(60, 150 / max(1, num_players ** 0.75)))
        
        center_x = canvas_size // 2
        center_y = canvas_size // 2
        circle_radius = (canvas_size // 2) - hex_radius - 20  

        self.__canvas = tk.Canvas(self.__root, width=canvas_size, height=canvas_size)
        self.__canvas.pack(expand=True)

        angle_between = 360 / num_players if num_players > 0 else 0
        colors = ["lightblue", "lightgreen", "lightcoral", "lightyellow", 
                 "lightpink", "lightgray", "lightcyan", "wheat", "lavender", "peachpuff"]

        for i, (name, player) in enumerate(self.__player_objects.items()):
            angle_deg = i * angle_between
            angle_rad = math.radians(angle_deg)

            cx = center_x + circle_radius * math.cos(angle_rad)
            cy = center_y + circle_radius * math.sin(angle_rad)

            self.__player_positions[name] = (cx, cy)

            points = self.__get_hexagon_points(cx, cy, hex_radius)
            color = colors[i % len(colors)]
            self.__canvas.create_polygon(points, fill=color, outline="black", width=2)
            
            font_size = max(6, min(10, int(hex_radius / 4)))
            strategy_name = type(player.get_strategy()).__name__.replace('_', ' ')
            
            display_text = f"  {name}\n  {strategy_name}\n  Score: {player.get_points()}"
            score_text = self.__canvas.create_text(cx, cy, text=display_text, font=("Arial", font_size, "bold"), fill="black", anchor="center")
              
            self.__score_texts[name] = score_text
    def __play_game_with_animation(self, player1, player2):
        #Creates animated arrows between players during games

        if not self.__canvas:
            return
            
        name1 = player1.get_name()
        name2 = player2.get_name()

        pos1 = self.__player_positions.get(name1)
        pos2 = self.__player_positions.get(name2)

        if not pos1 or not pos2:
            return

        x1, y1 = pos1
        x2, y2 = pos2

        arrow1 = self.__canvas.create_line(x1, y1, x1, y1, arrow=tk.LAST, fill="red", width=2)
        arrow2 = self.__canvas.create_line(x2, y2, x2, y2, arrow=tk.LAST, fill="green", width=2)

        steps = 20
        delay = 15  

        dx1 = (x2 - x1) / steps
        dy1 = (y2 - y1) / steps
        dx2 = (x1 - x2) / steps
        dy2 = (y1 - y2) / steps

        for step in range(1, steps + 1):
            self.__canvas.coords(arrow1, x1, y1, x1 + dx1 * step, y1 + dy1 * step)
            self.__canvas.coords(arrow2, x2, y2, x2 + dx2 * step, y2 + dy2 * step)
            self.__canvas.update()
            self.__root.after(delay)

        self.__root.after(300)
        self.__canvas.delete(arrow1)
        self.__canvas.delete(arrow2)
    def __update_score_display(self):
        #Refreshes text on player hexagons to show current scores and strategy information

        for name, player in self.__player_objects.items():
            if name in self.__score_texts:
                strategy_name = type(player.get_strategy()).__name__.replace('_', ' ')
                score_text = f"{name}\n{strategy_name}\nScore: {player.get_points()}"
                self.__canvas.itemconfig(self.__score_texts[name], text=score_text)
    def __display_result(self, text):
        #Adds text to scrollable resulst area
        #Scrolls automatically to show up to date information

        self.__results_text.insert(tk.END, text)
        self.__results_text.see(tk.END)
        self.__root.update_idletasks()
    

    """Step-Through"""
    def __toggle_step_through(self):
        #Switches between normal mode and a step-by-step mode
        #This means users can look at individual iterations for analysis

        self.__step_through_mode = not self.__step_through_mode
        
        if self.__step_through_mode:
            self.__step_button.config(text="Disable Step Through", bg="orange")
            if self.__is_running:
                self.__next_step_button.config(state="normal")
        else:
            self.__step_button.config(text="Step Through", bg="lightsteelblue")
            self.__next_step_button.config(state="disabled")
            self.__waiting_for_step = False
    def __next_step(self):
        #Releases simulation from waiting mode so it can go to the next iteration

        self.__waiting_for_step = False
    def __wait_for_step(self):
        #Pauses the simulation to wait for the user to continue

        if not self.__step_through_mode or not self.__is_running:
            return
        
        self.__waiting_for_step = True
        self.__next_step_button.config(state="normal")
        
        while self.__waiting_for_step and self.__is_running:
            self.__root.update()
            self.__root.after(50)
        
        self.__next_step_button.config(state="disabled" if not self.__is_running else "normal")
    
    
    """Strategy/Analysis"""
    def __update_strategies(self):
        #Changes cooperativity of players with the custom strategy, to improve performance

        if not self.__params.get("Updating Strategies", False):
            return
        
        for player in self.__player_objects.values():
            strategy = player.get_strategy()
            if isinstance(strategy, Custom):
                recent_performance = strategy.get_recent_performance()
                if len(recent_performance) >= 5:  
                    avg_score = sum(recent_performance) / len(recent_performance)
                    
                    if avg_score < 2.0:  
                        strategy.adjust_cooperativity(-0.05)
                    elif avg_score > 3.0:  
                        strategy.adjust_cooperativity(0.02)
                    
                    self.__display_result(f"Updated {player.get_name()}'s strategy: cooperativity = {strategy.cooperativity:.2f}\n")
    def __export_results(self):
        #Saves all simulation data into a CSV file, which includes parameters, results and game histories

        if not self.__player_objects:
            messagebox.showwarning("No Data", "No player data to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_theory_results_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow(['Export Time', timestamp])
                writer.writerow(['Game Parameters'])
                writer.writerow(['Parameter', 'Value'])
                for key, value in self.__params.items():
                    writer.writerow([key, value])
                
                writer.writerow([])  
                writer.writerow(['Player Results'])
                writer.writerow(['Player Name', 'Strategy', 'Final Score', 'Cooperativity (if Custom)'])
                
                for name, player in self.__player_objects.items():
                    strategy = player.get_strategy()
                    strategy_name = type(strategy).__name__.replace('_', ' ')
                    cooperativity = getattr(strategy, 'cooperativity', 'N/A')
                    
                    writer.writerow([name, strategy_name, player.get_points(), cooperativity])
                
                writer.writerow([])  
                writer.writerow(['Game Histories'])
                writer.writerow(['Player 1', 'Player 2', 'P1 Moves', 'P2 Moves', 'Game Length'])
                
                for pair_key, history in self.__game_histories.items():
                    p1_name, p2_name = pair_key
                    p1_moves = ','.join(map(str, history['p1_history']))
                    p2_moves = ','.join(map(str, history['p2_history']))
                    game_length = len(history['p1_history'])
                    
                    writer.writerow([p1_name, p2_name, p1_moves, p2_moves, game_length])
            
            messagebox.showinfo("Export Successful", f"Results exported to {filename}")
            self.__display_result(f"Results exported to {filename}\n")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")


if __name__ == "__main__":
    # Initialize parameter window
    params = tk.Tk()
    part_one = Paramter_Set_Window(params)
    params.mainloop()
    param_values = part_one.get_values()
    
    # Extract parameter values
    player_count = param_values["Player Number"]
    iteration_count = param_values["Iteration Number"]
    
    # Initialize player window
    player_window = tk.Tk()
    part_two = Player_Set_Window(player_window, player_count)
    player_window.mainloop()
    players = part_two.get_values()
    
    # Start main simulation
    main = tk.Tk()
    simulation = Simulation(main, players, param_values)
    main.mainloop()
