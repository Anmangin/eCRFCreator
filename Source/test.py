import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

class JSONEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Editor")
        self.json_data = {}
        self.file_path = ""
        
        self.load_button = tk.Button(root, text="Charger JSON", command=self.load_json)
        self.load_button.pack(pady=5)
        
        self.add_button = tk.Button(root, text="Ajouter une entrée", command=self.add_entry)
        self.add_button.pack(pady=5)
        
        self.edit_button = tk.Button(root, text="Modifier une entrée", command=self.edit_entry)
        self.edit_button.pack(pady=5)
        
        self.delete_button = tk.Button(root, text="Supprimer une entrée", command=self.delete_entry)
        self.delete_button.pack(pady=5)
        
        self.save_button = tk.Button(root, text="Sauvegarder JSON", command=self.save_json)
        self.save_button.pack(pady=5)
        
        self.text_area = tk.Text(root, height=20, width=50)
        self.text_area.pack(pady=5)
    
    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.json_data = json.load(file)
            self.file_path = file_path
            self.display_json()
    
    def display_json(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, json.dumps(self.json_data, indent=4))
    
    def add_entry(self):
        key = simpledialog.askstring("Ajouter une entrée", "Clé de l'entrée :")
        if key:
            value = simpledialog.askstring("Ajouter une entrée", f"Valeur pour {key}:")
            self.json_data[key] = value
            self.display_json()
    
    def edit_entry(self):
        key = simpledialog.askstring("Modifier une entrée", "Clé de l'entrée à modifier :")
        if key in self.json_data:
            value = simpledialog.askstring("Modifier une entrée", f"Nouvelle valeur pour {key}:")
            self.json_data[key] = value
            self.display_json()
        else:
            messagebox.showerror("Erreur", "Clé non trouvée dans le JSON")
    
    def delete_entry(self):
        key = simpledialog.askstring("Supprimer une entrée", "Clé de l'entrée à supprimer :")
        if key in self.json_data:
            del self.json_data[key]
            self.display_json()
        else:
            messagebox.showerror("Erreur", "Clé non trouvée dans le JSON")
    
    def save_json(self):
        if self.file_path:
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(self.json_data, file, indent=4)
            messagebox.showinfo("Succès", "JSON sauvegardé avec succès !")
        else:
            messagebox.showerror("Erreur", "Aucun fichier chargé.")

if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditor(root)
    root.mainloop()
