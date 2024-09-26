import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class LayerFrame(tk.Frame):
    def __init__(self, parent, generator, layer_data=None):
        super().__init__(parent, bd=0, highlightthickness=0, bg='#ffffff', padx=15, pady=15)
        self.generator = generator

        # Glassy background with rounded corners and shadow
        self.config(highlightbackground='#bbbbbb', highlightthickness=1, relief=tk.RIDGE)

        # Layer Path
        self.path_var = tk.StringVar()
        self.offset_x_var = tk.StringVar()
        self.offset_y_var = tk.StringVar()
        self.blend_mode_var = tk.StringVar(value="normal")

        # Styling widgets
        tk.Label(self, text="Layer Path", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        path_entry = ttk.Entry(self, textvariable=self.path_var, width=30)
        path_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Label(self, text="Offset X", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.offset_x_var, width=5).pack(side=tk.LEFT)

        tk.Label(self, text="Offset Y", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.offset_y_var, width=5).pack(side=tk.LEFT)

        tk.Label(self, text="Blend Mode", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Combobox(self, textvariable=self.blend_mode_var, values=["normal", "multiply", "overlay"]).pack(side=tk.LEFT)

        # Remove button with hover effect
        remove_button = ttk.Button(self, text="Remove Layer", command=self.remove_layer)
        remove_button.pack(side=tk.LEFT, padx=10)
        remove_button.bind("<Enter>", lambda e: remove_button.config(style="Accent.TButton"))
        remove_button.bind("<Leave>", lambda e: remove_button.config(style="TButton"))

        if layer_data:
            self.populate_layer(layer_data)

    def populate_layer(self, data):
        self.path_var.set(data.get("path", ""))
        self.offset_x_var.set(data["offset"][0])
        self.offset_y_var.set(data["offset"][1])
        self.blend_mode_var.set(data.get("blend_mode", "normal"))
    
    def get_layer_data(self):
        return {
            "path": self.path_var.get(),
            "offset": [int(self.offset_x_var.get()), int(self.offset_y_var.get())],
            "blend_mode": self.blend_mode_var.get()
        }

    def remove_layer(self):
        self.pack_forget()
        self.generator.layers.remove(self)
        self.destroy()


class GeneratorFrame(tk.Frame):
    def __init__(self, parent, generator_data=None):
        super().__init__(parent, bg='#ffffff', padx=15, pady=15, bd=0)

        # Styling: Glassy background, rounded corners, shadow
        self.config(highlightbackground='#bbbbbb', highlightthickness=1, relief=tk.RIDGE)

        self.layers = []
        self.output_folder_var = tk.StringVar()
        self.output_suffix_var = tk.StringVar()
        self.output_prefix_var = tk.StringVar()

        # Generator fields
        tk.Label(self, text="Output Folder", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.output_folder_var, width=30).pack(side=tk.LEFT, padx=10)

        tk.Label(self, text="Output Suffix", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.output_suffix_var, width=10).pack(side=tk.LEFT, padx=10)

        tk.Label(self, text="Output Prefix", font=("Roboto", 10), bg='#ffffff').pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.output_prefix_var, width=10).pack(side=tk.LEFT, padx=10)

        # Add Layer Button with hover effect
        add_layer_button = ttk.Button(self, text="Add Layer", command=self.add_layer)
        add_layer_button.pack(side=tk.LEFT, padx=10)
        add_layer_button.bind("<Enter>", lambda e: add_layer_button.config(style="Accent.TButton"))
        add_layer_button.bind("<Leave>", lambda e: add_layer_button.config(style="TButton"))

        # Remove Generator Button with hover effect
        remove_button = ttk.Button(self, text="Remove Generator", command=self.remove_generator)
        remove_button.pack(side=tk.LEFT, padx=10)
        remove_button.bind("<Enter>", lambda e: remove_button.config(style="Accent.TButton"))
        remove_button.bind("<Leave>", lambda e: remove_button.config(style="TButton"))

        self.layer_container = tk.Frame(self, bg='#ffffff')
        self.layer_container.pack(fill=tk.X, padx=10, pady=5)

        if generator_data:
            self.populate_generator(generator_data)

    def populate_generator(self, data):
        self.output_folder_var.set(data.get("output_folder", ""))
        self.output_suffix_var.set(data.get("output_suffix", ""))
        self.output_prefix_var.set(data.get("output_prefix", ""))

        for layer_data in data.get("layers", []):
            self.add_layer(layer_data)

    def add_layer(self, layer_data=None):
        layer_frame = LayerFrame(self.layer_container, self, layer_data)
        layer_frame.pack(fill=tk.X, pady=5)
        self.layers.append(layer_frame)

    def get_generator_data(self):
        return {
            "output_folder": self.output_folder_var.get(),
            "output_suffix": self.output_suffix_var.get(),
            "output_prefix": self.output_prefix_var.get(),
            "layers": [layer.get_layer_data() for layer in self.layers]
        }

    def remove_generator(self):
        self.pack_forget()
        self.master.generators.remove(self)
        self.destroy()


class ConfigEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Material Design - Config Editor")
        self.configure(bg="#f4f4f4")

        self.generators = []
        self.config_path = tk.StringVar()

        # Styles for the app
        self.style = ttk.Style(self)
        self.style.configure("TButton", font=("Roboto", 10), padding=6)
        self.style.configure("Accent.TButton", background="#2196F3", foreground="#ffffff", font=("Roboto", 10))
        self.style.configure("TEntry", font=("Roboto", 10))
        
        # Header with Gradient
        header_frame = tk.Frame(self, bg='#2196F3', pady=15)
        header_frame.pack(fill=tk.X)
        header_label = tk.Label(header_frame, text="Configuration Editor", font=("Roboto", 18, "bold"), fg="white", bg="#2196F3")
        header_label.pack()

        # File load/save frame
        file_frame = tk.Frame(self, bg='#f4f4f4', pady=10)
        file_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(file_frame, text="Config File", font=("Roboto", 12), bg='#f4f4f4').pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.config_path, width=40).pack(side=tk.LEFT, padx=10)
        ttk.Button(file_frame, text="Load", command=self.load_config).pack(side=tk.LEFT, padx=10)
        ttk.Button(file_frame, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=10)
        ttk.Button(file_frame, text="Add Generator", command=self.add_generator).pack(side=tk.LEFT, padx=10)

        self.generator_container = tk.Frame(self, bg='#f4f4f4')
        self.generator_container.pack(fill=tk.X, padx=20, pady=10)

    def load_config(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.config_path.set(filepath)
            self.populate_fields(data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")

    def populate_fields(self, data):
        for generator_data in data.get("generators", []):
            self.add_generator(generator_data)

    def add_generator(self, generator_data=None):
        generator_frame = GeneratorFrame(self.generator_container, generator_data)
        generator_frame.pack(fill=tk.X, pady=10)
        self.generators.append(generator_frame)

    def save_config(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not filepath:
            return
        try:
            data = {
                "generators": [generator.get_generator_data() for generator in self.generators]
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON: {e}")


# Run the app
if __name__ == "__main__":
    app = ConfigEditorApp()
    app.mainloop()
