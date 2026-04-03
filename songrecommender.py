import pandas as pd 
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror

def import_data():
    train_data = pd.read_csv('spotify_data.csv')
    return train_data

class Track(object):
    def __init__(self, track, track_name, danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo):
        self.track = track
        self.track_name = track_name
        self.danceability = danceability
        self.energy = energy
        self.loudness = loudness
        self.speechiness = speechiness
        self.acousticness = acousticness
        self.instrumentalness = instrumentalness
        self.liveness = liveness
        self.valence = valence
        self.tempo = tempo

class PointSpace(object):
    def __init__(self, data, track_name):
        self.points = []
        self.data = data
        self.used_songs = set()  # Track recommended songs to avoid duplicates
        
        # Gets first song, which is at centre of user's taste in songs, adds it to points
        if track_name in self.data['track_name'].values:
            row = self.data[self.data["track_name"] == track_name].iloc[0]
            self.centroid = Track(row['track_id'], row['track_name'], row['danceability'], 
                                row['energy'], row['loudness'], row['speechiness'], 
                                row['acousticness'], row['instrumentalness'], row['liveness'], 
                                row['valence'], row['tempo'])
            self.points.append(self.centroid)
            self.used_songs.add(track_name)
        else:
            # Default to first song if track_name not found
            row = self.data.iloc[0]
            self.centroid = Track(row['track_id'], row['track_name'], row['danceability'], 
                                row['energy'], row['loudness'], row['speechiness'], 
                                row['acousticness'], row['instrumentalness'], row['liveness'], 
                                row['valence'], row['tempo'])
            self.points.append(self.centroid)
            self.used_songs.add(row['track_name'])

    def find_similar(self):
        '''
        Similar songs are songs with: d±0.25, e±0.25, l±2, s±0.01, a±0.2, i±5e-6, li±0.04, v±0.05, t±10
        Compares track directly to centroid, if in 'acceptable' range, it is deemed similar.
        Returns first song it finds that hasn't been used yet
        '''
        for _, row in self.data.iterrows():
            # Skip if song already used
            if row['track_name'] in self.used_songs:
                continue
                
            # Check if song is within acceptable range
            if (abs(row['danceability'] - self.centroid.danceability) <= 0.25 and
                abs(row['energy'] - self.centroid.energy) <= 0.25 and
                abs(row['loudness'] - self.centroid.loudness) <= 2 and
                abs(row['speechiness'] - self.centroid.speechiness) <= 0.01 and
                abs(row['acousticness'] - self.centroid.acousticness) <= 0.2 and
                abs(row['instrumentalness'] - self.centroid.instrumentalness) <= 5e-6 and
                abs(row['liveness'] - self.centroid.liveness) <= 0.04 and
                abs(row['valence'] - self.centroid.valence) <= 0.05 and
                abs(row['tempo'] - self.centroid.tempo) <= 10):
                
                self.used_songs.add(row['track_name'])
                return row['track_name']
        
        return None  # No similar songs found

    def update_centroid(self):
        if not self.points:
            return
            
        d_total = sum(point.danceability for point in self.points)
        e_total = sum(point.energy for point in self.points)
        l_total = sum(point.loudness for point in self.points)
        s_total = sum(point.speechiness for point in self.points)
        a_total = sum(point.acousticness for point in self.points)
        i_total = sum(point.instrumentalness for point in self.points)
        li_total = sum(point.liveness for point in self.points)
        v_total = sum(point.valence for point in self.points)
        t_total = sum(point.tempo for point in self.points)

        n = len(self.points)
        self.centroid = Track("centre", "centre", d_total / n, e_total / n, l_total / n, 
                            s_total / n, a_total / n, i_total / n, li_total / n, 
                            v_total / n, t_total / n)

class ConverterFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        
        # Initialize data first
        try:
            self.data = import_data()
        except FileNotFoundError:
            showerror("Error", "spotify_data.csv file not found!")
            return
            
        self.area = None
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = ttk.Label(self, text="Song Recommender", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Song input
        ttk.Label(self, text="Enter song name:").pack(pady=(0, 5))
        self.song_name = tk.StringVar()
        self.song_entry = ttk.Entry(self, textvariable=self.song_name, width=40, font=("Arial", 11))
        self.song_entry.pack(pady=(0, 15))
        self.song_entry.bind('<Return>', lambda e: self.smart_add_song())
        
        # Main buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=(0, 15))
        
        self.add_centre = ttk.Button(button_frame, text='Set Starting Song', command=self.set_first)
        self.add_centre.pack(side='left', padx=(0, 10))

        self.add_button = ttk.Button(button_frame, text='Add Song', command=self.add_song)
        self.add_button.pack(side='left', padx=(0, 10))
        
        self.get_rec_button = ttk.Button(button_frame, text='Get Recommendation', command=self.get_recommendation)
        self.get_rec_button.pack(side='left')
        
        # Status
        self.status_label = ttk.Label(self, text="Enter a starting song to begin", font=("Arial", 9))
        self.status_label.pack(pady=(0, 10))
        
        # Recommendation display
        self.recommend_label = ttk.Label(self, text="", wraplength=400, font=("Arial", 11, "bold"))
        self.recommend_label.pack(pady=(0, 15))
        
        # Songs list
        ttk.Label(self, text="Your Songs:").pack(anchor='w', padx=20)
        
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=20, pady=(5, 10))
        
        self.songs_listbox = tk.Listbox(list_frame, width=50, height=8, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.songs_listbox.yview)
        self.songs_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.songs_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Clear button
        ttk.Button(self, text='Clear All', command=self.clear_preferences).pack(pady=(0, 10))

    def smart_add_song(self):
        """Smart add - if no starting song, set as starting, otherwise add to preferences"""
        if self.area is None:
            self.set_first()
        else:
            self.add_song()

    def set_first(self):
        song_title = self.song_name.get().strip()
        if not song_title:
            showerror("Error", "Please enter a song name!")
            return
            
        if song_title in self.data['track_name'].values:
            self.area = PointSpace(self.data, song_title)
            self.status_label.config(text=f"Starting song: {song_title}")
            self.songs_listbox.delete(0, tk.END)
            self.songs_listbox.insert(tk.END, f"{song_title} (starting)")
            self.song_name.set("")
            self.recommend_label.config(text="Ready for recommendations!")
        else:
            available_songs = self.data['track_name'].head(3).tolist()
            hint = f"Song not found. Try: {', '.join(available_songs)}"
            showerror("Song Not Found", hint)

    def add_song(self):
        if self.area is None:
            showerror("Error", "Please set a starting song first!")
            return
            
        song_title = self.song_name.get().strip()
        if not song_title:
            showerror("Error", "Please enter a song name!")
            return
            
        if song_title in self.data['track_name'].values:
            if song_title in self.area.used_songs:
                showerror("Already Added", f"'{song_title}' is already added!")
                return
                
            row = self.data[self.data["track_name"] == song_title].iloc[0]
            new_track = Track(row['track_id'], row['track_name'], row['danceability'], 
                            row['energy'], row['loudness'], row['speechiness'], 
                            row['acousticness'], row['instrumentalness'], row['liveness'], 
                            row['valence'], row['tempo'])
            
            self.area.points.append(new_track)
            self.area.used_songs.add(song_title)
            self.area.update_centroid()
            
            self.songs_listbox.insert(tk.END, song_title)
            self.status_label.config(text=f"Added: {song_title}")
            self.song_name.set("")
        else:
            available_songs = self.data['track_name'].head(3).tolist()
            hint = f"Song not found. Try: {', '.join(available_songs)}"
            showerror("Song Not Found", hint)

    def get_recommendation(self):
        if self.area is None:
            showerror("Error", "Please set a starting song first!")
            return
            
        recommended = self.area.find_similar()
        if recommended:
            song_info = self.data[self.data['track_name'] == recommended].iloc[0]
            artist = song_info.get('artists', 'Unknown Artist')
            self.recommend_label.config(text=f"Recommended: {recommended}\nBy: {artist}")
            self.status_label.config(text="New recommendation generated!")
        else:
            self.recommend_label.config(text="No more similar songs found.\nTry adding more songs!")
            self.status_label.config(text="No recommendations available")
    
    def clear_preferences(self):
        self.area = None
        self.songs_listbox.delete(0, tk.END)
        self.recommend_label.config(text="")
        self.status_label.config(text="Enter a starting song to begin")
        self.song_name.set("")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Song Recommender")
        self.geometry("480x600")
        self.resizable(True, True)
        self.minsize(400, 500)
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    app = App()
    frame = ConverterFrame(app)
    frame.pack(fill='both', expand=True, padx=20, pady=20)
    app.mainloop()