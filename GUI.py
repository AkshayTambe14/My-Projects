import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
from sim_objects import Player, Map, Strategy, Game

class Paramter_Set_Window(object):
    def __init__(self, root):
        self.__root = root
        self.__root.title("Parameter Setter")
    

        self.__player_prompt = tk.Label(root, text="Enter Number of Players:")
        self.__player_num_entry = tk.Entry(root)
        self.__player_prompt.pack()
        self.__player_num_entry.pack(pady=5)
        self.__player_num_entry.focus()

        self.__iteration_prompt = tk.Label(root, text="Enter Number of Iterations:")
        self.__iteration_num_entry = tk.Entry(root)
        self.__iteration_prompt.pack()
        self.__iteration_num_entry.pack(pady=5)

        self.__submit_button = tk.Button(root, text="Submit", command=self.onclick)
        self.__submit_button.pack()

        self.__values = {}

    def onclick(self):
        self.__values["Player Number"] = self.__player_num_entry.get()
        self.__values["Iteration Number"] = self.__iteration_num_entry.get()
        self.close()

    def get_values(self):
        return self.__values
    
    def close(self):
        self.__root.destroy()

class Player_Set_Window(object):
    def __init__(self, root, number_of_players, strategies=["Tit-for-Tat", "Always Cooperate", "Always Defect", "Random", "Grudger", "Pavlov"]):
        self.__root = root
        self.__root.title("Player Setter")

        try:
            self.__number_of_players = int(number_of_players)
        except (ValueError, TypeError):
            print(f"Error: Invalid number of players '{number_of_players}', defaulting to 2")
            self.__number_of_players = 2

        print(f"Creating player configuration for {self.__number_of_players} players")

        self.__player_prompt = tk.Label(root, text="Enter Settings For Players:")
        self.__player_prompt.pack()

        self.__frame = tk.Frame(root)
        self.__frame.pack(pady=10)
        
        self.__names = []
        self.__strats = []
        self.__customs = []
        self.__values = {}

        for i in range(self.__number_of_players):
            label = tk.Label(self.__frame, text=f"Player {i+1} Name:")
            label.grid(row=i, column=0, padx=5, pady=5)

            entry = tk.Entry(self.__frame)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, f"Player{i+1}")
            self.__names.append(entry)

            options = strategies + ["Custom"]
            selected_option = tk.StringVar(value=options[0])
            dropdown = tk.OptionMenu(self.__frame, selected_option, *options)
            dropdown.grid(row=i, column=2, padx=5, pady=5)
            self.__strats.append(selected_option)

            value_label = tk.Label(self.__frame, text="50")
            value_label.grid(row=i, column=4, padx=5)
            value_label.grid_remove()

            slider_var = tk.DoubleVar(value=50)
            self.__customs.append(slider_var)
            slider = ttk.Scale(
                self.__frame, from_=1, to=100, orient='horizontal',
                variable=slider_var,
                command=lambda val, lbl=value_label, var=slider_var: lbl.config(text=str(int(float(var.get()))))
            )
            slider.grid(row=i, column=3, padx=5, pady=5)
            slider.grid_remove()

            def update_slider_visibility(var=selected_option, s=slider, l=value_label):
                if var.get() == "Custom":
                    s.grid()
                    l.grid()
                else:
                    s.grid_remove()
                    l.grid_remove()

            selected_option.trace_add("write", lambda *args, v=selected_option, s=slider, l=value_label: update_slider_visibility(v, s, l))

        self.__submit_button = tk.Button(root, text="Submit", command=self.onclick)
        self.__submit_button.pack()
            
    def onclick(self):
        print(f"Processing {len(self.__names)} player configurations")
        for index, name_entry in enumerate(self.__names):
            name = name_entry.get().strip()
            if not name:  
                name = f"Player{index+1}"
            
            selected_strat = self.__strats[index].get()
            custom_value = int(float(self.__customs[index].get()))

            if selected_strat == "Custom":
                self.__values[name] = ["custom", custom_value]
            else:
                self.__values[name] = selected_strat

        print(f"Final player values: {self.__values}")
        self.close()

    def get_values(self):
        return self.__values

    def close(self):
        self.__root.destroy()