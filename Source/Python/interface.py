import xml.etree.ElementTree as ET
import re
import sys
import os
import json
import traceback
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import messagebox
from pathlib import Path
from XML_Function import lire_et_trier_donnees, exporter_donnees_markdown_eCRF
 
def Get_objt(root, racine, keyname, fields):
        ProForm = {}
        for FWAW in root.iter(racine):
            key = FWAW.findtext(keyname)
            if key:  # Vérifie que la clé existe
                ProForm[key] = {field: FWAW.findtext(field) for field in fields}
        return ProForm

def validate_xml_file(filepath):
    """Valide le fichier XML. Retourne True si valide, sinon False."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            print(f"First line read: {repr(first_line)}")
            if first_line != '\ufeff<?xml version="1.0" encoding="utf-8"?>':
                return False, "La première ligne n'est pas conforme."
        tree = ET.parse(filepath)
        root = tree.getroot()

        if root.find(".//ProPatient") is None:
            return False, "Pas d'objet patient présent, le programme nécéssite un XML finis"

        if root.find(".//ProPatientVisit") is None:
            return False, "Pas d'objet  visite dans le template patient, le programme nécéssite un XML finis"

        if root.find(".//ProVisitForm") is None:
            return False, "Pas d'objet  form dans une visite, le programme nécéssite un XML finis"

        if root.find(".//ProFormGroup") is None:
            return False, "Pas d'objet  group dans une fiche, le programme nécéssite un XML finis."

        if root.find(".//ProGroupItem") is None:
            return False, "Pas d'objet  item  dans un groupe, le programme nécéssite un XML finis."

        return True, "XML valide."

    except ET.ParseError:
        return False, "Erreur de parsing XML."
    except Exception as e:
        return False, f"Erreur inattendue : {e}"

def update_validation_icon():
    """Valide le fichier XML et met à jour le cercle."""

    filepath = input_path_var.get()
    
    # Ne pas valider si la variable est vide au démarrage.
    if not filepath:
        status_label.config(text="Aucun fichier sélectionné.", fg="red")
        canvas.itemconfig(circle, fill="red")
        return

    is_valid, message = validate_xml_file(filepath)
    status_label.config(text=message, fg="green" if is_valid else "red")
    canvas.itemconfig(circle, fill="green" if is_valid else "red")

def select_input_file():
    filepath = askopenfilename(filetypes=[("XML files", "*.xml")])
    if filepath:
        input_path_var.set(filepath)


def select_output_folder():
    folderpath = askdirectory()
    if folderpath:
        output_path_var.set(folderpath)

def run_program():
    # Vérification de l'extension du fichier d'entrée
    Pathin = input_path_var.get()
    if not Pathin.lower().endswith(".xml"):
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier XML.")
        return

    # Vérification des chemins
    output_path = output_path_var.get()
    if not Pathin or not output_path:
        messagebox.showerror("Erreur", "Veuillez fournir les deux chemins avant de lancer le programme.")
        return

    is_valid, message = validate_xml_file(Pathin)
    if not is_valid:
        messagebox.showerror("Validation échouée", message)
        return

    # Détecte si exécuté depuis un exécutable ou un script
    execution_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.getcwd()
    file_name = os.path.basename(Pathin).replace('.xml', '')

    # Lecture des données et génération des fichiers
    try:
        config_path = os.path.join(execution_path, "Python/config.json")
        data = lire_et_trier_donnees(Pathin, config_path)
        JSON_EXPORT = exporter_donnees_markdown_eCRF(data, False)  # Toujours False

        # Génération du fichier HTML
        css = Path(f"{execution_path}/Python/style.css").read_text(encoding='utf-8')
        JSON_Data = f"const jsonData = {json.dumps(JSON_EXPORT)};"
        chemin_html = f"{execution_path}/Python/Template_CRF.html"
        contenu_html = Path(chemin_html).read_text(encoding='utf-8')

        final_export = (
            contenu_html
            .replace("// <JSONDATA>", JSON_Data)
            .replace("/* <css></css> */", css)
            .replace(r"\r\n", "<br>")
            .replace(r"\n", "<br>")
            .replace(r"\r", "<br>")
        )

        with open(f"{output_path}/{file_name}.html", 'w', encoding='utf-8') as f:
            f.write(final_export)

        print(f"Le fichier {output_path}/{file_name}.html a été imprimé avec succès.")
        messagebox.showinfo("Succès", "Le programme a été exécuté avec succès !")
    
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

# Initialisation de la fenêtre principale
root = tk.Tk()
root.title("Convertisseur XML vers HTML")
root.geometry("500x400")
root.configure(bg="#f7f5f2")  # Couleur de fond chaleureuse
# Définir l'icône de la fenêtre
execution_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.getcwd()

root.iconbitmap(f"{execution_path}/Python/images.ico")  # Remplacez par le chemin de votre icône .ico

# Variables pour stocker les chemins
input_path_var = tk.StringVar()
output_path_var = tk.StringVar()
input_path_var.trace_add("write", lambda *args: update_validation_icon())

# Styles personnalisés
label_font = ("Arial", 12, "bold")
entry_font = ("Arial", 10)
button_font = ("Arial", 10, "bold")

# Widgets de l'interface
input_label = tk.Label(root, text="Fichier XML d'entrée :", font=label_font, bg="#f7f5f2", fg="#333333")
input_label.pack(pady=10)

input_frame = tk.Frame(root, bg="#f7f5f2")
input_frame.pack(pady=5)

input_entry = tk.Entry(input_frame, textvariable=input_path_var, width=40, font=entry_font)
input_entry.pack(side="left", padx=5)

canvas = tk.Canvas(root, width=20, height=20)
circle = canvas.create_oval(2, 2, 18, 18, fill="red")
canvas.pack(side="right", padx=10)

input_button = tk.Button(root, text="Choisir un fichier", command=select_input_file, font=button_font, bg="#e6e6e6", fg="#333333")
input_button.pack(pady=5)

output_label = tk.Label(root, text="Dossier de sortie :", font=label_font, bg="#f7f5f2", fg="#333333")
output_label.pack(pady=10)
output_entry = tk.Entry(root, textvariable=output_path_var, width=50, font=entry_font)
output_entry.pack(pady=5)
output_button = tk.Button(root, text="Choisir un dossier", command=select_output_folder, font=button_font, bg="#e6e6e6", fg="#333333")
output_button.pack(pady=5)

run_button = tk.Button(root, text="Lancer le programme", command=run_program, font=button_font, bg="#4caf50", fg="white")
run_button.pack(pady=20)
status_label = tk.Label(root, text="Aucun fichier sélectionné.", fg="red")
status_label.pack(pady=5)

# Création du pied de page
footer_label = tk.Label(root, text="Créateur : by Anthony MANGIN", font=("Arial", 8), fg="#777777", bg="#f7f5f2")
footer_label.pack(side="bottom", pady=5)

# Lancement de l'interface
root.mainloop()
