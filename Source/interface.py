import xml.etree.ElementTree as ET
import os
import sys
import json
import traceback
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

# --- tes imports métiers
from XML_Function import lire_et_trier_donnees, exporter_donnees_markdown_eCRF, print_xls_from_edit_check, print_doc_xml

# ===================== Utils PyInstaller / chemins =====================

def resource_base() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def tcl_path_str(p: Path) -> str:
    return str(p).replace("\\", "/")

def read_text(rel_path: str, encoding="utf-8") -> str:
    p = resource_path(rel_path)
    return open(p, encoding=encoding).read()

# ===================== JSON =====================

def save_json(obj, output_dir: str, file_name="export.json"):
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        json_file_path = os.path.join(output_dir, file_name)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        print(f"Fichier JSON sauvegardé : {json_file_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde JSON : {e}")

# ===================== Validation XML =====================

def validate_xml_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip().lstrip('\ufeff')
            if not first_line.lower().startswith('<?xml ') or 'encoding="utf-8"' not in first_line.lower():
                return False, "En-tête XML inattendu (attendu: XML UTF-8)."
        tree = ET.parse(filepath)
        root = tree.getroot()
        required = [
            (".//ProPatient", "Pas d'objet patient présent."),
            (".//ProPatientVisit", "Pas d'objet visite (ProPatientVisit)."),
            (".//ProVisitForm", "Pas d'objet form (ProVisitForm)."),
            (".//ProFormGroup", "Pas d'objet group (ProFormGroup)."),
            (".//ProGroupItem", "Pas d'objet item (ProGroupItem)."),
        ]
        for xpath, msg in required:
            if root.find(xpath) is None:
                return False, msg
        return True, "XML valide."
    except ET.ParseError:
        return False, "Erreur de parsing XML."
    except Exception as e:
        return False, f"Erreur inattendue : {e}"

# ===================== GUI =====================

root = tk.Tk()
root.title("Convertisseur XML vers HTML")
root.geometry("500x500")
root.configure(bg="#f7f5f2")

# Variables
input_path_var = tk.StringVar()
output_path_var = tk.StringVar()
generate_excel_var = tk.BooleanVar(value=True)
generate_word_var = tk.BooleanVar(value=True)
generate_html_var = tk.BooleanVar(value=True)

# ===================== Fonctions GUI =====================

def update_validation_icon(*args):
    filepath = input_path_var.get()
    if not filepath:
        status_label.config(text="Aucun fichier sélectionné.", fg="red")
        canvas.itemconfig(circle, fill="red")
        return
    is_valid, message = validate_xml_file(filepath)
    status_label.config(text=message, fg="green" if is_valid else "red")
    canvas.itemconfig(circle, fill="green" if is_valid else "red")

def select_input_file():
    filepath = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if filepath:
        input_path_var.set(filepath)

def select_output_folder():
    folderpath = filedialog.askdirectory()
    if folderpath:
        output_path_var.set(folderpath)

def run_program():
    Pathin = input_path_var.get()
    output_path = output_path_var.get()
    if not Pathin.lower().endswith(".xml") or not Pathin or not output_path:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier XML et un dossier de sortie.")
        return
    is_valid, message = validate_xml_file(Pathin)
    if not is_valid:
        messagebox.showerror("Validation échouée", message)
        return
    file_name = os.path.basename(Pathin).replace('.xml', '')

    try:
        config_path = resource_path("Python/config.json")
        data = lire_et_trier_donnees(Pathin, str(config_path))
        JSON_EXPORT = exporter_donnees_markdown_eCRF(data, False)
        save_json(JSON_EXPORT, output_path, file_name="resultat_export.json")

        # ===================== HTML =====================
        if generate_html_var.get():
            css = read_text("Python/style.css")
            template_html = read_text("Python/Template_CRF.html")
            printpage = read_text("Python/print.html")
            JSON_Data = f"const jsonData = {json.dumps(JSON_EXPORT, ensure_ascii=False)};"
            final_export = (
                template_html
                .replace("// <JSONDATA>", JSON_Data)
                .replace("/* <css></css> */", css)
                .replace("<!--<print></print> -->", printpage)
                .replace(r"\r\n", "<br>")
                .replace(r"\n", "<br>")
                .replace(r"\r", "<br>")
            )
            out_html = os.path.join(output_path, f"{file_name}.html")
            with open(out_html, 'w', encoding='utf-8') as f:
                f.write(final_export)
            print(f"HTML généré : {out_html}")

        # ===================== Excel =====================
        if generate_excel_var.get():
            print_xls_from_edit_check(Pathin, os.path.join(output_path, f"{file_name}.xlsx"))

        # ===================== Word =====================
        if generate_word_var.get():
            print_doc_xml(Pathin, os.path.join(output_path, f"{file_name}.docx"))

        messagebox.showinfo("Succès", "Programme exécuté avec succès !")

    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

# ===================== Widgets =====================

# Entrée XML
tk.Label(root, text="Fichier XML d'entrée :", font=("Arial", 12, "bold"), bg="#f7f5f2").pack(pady=5)
tk.Entry(root, textvariable=input_path_var, width=40, font=("Arial", 10)).pack()
tk.Button(root, text="Choisir un fichier", command=select_input_file, font=("Arial", 10, "bold"), bg="#e6e6e6").pack(pady=5)

# Validation
canvas = tk.Canvas(root, width=20, height=20, bg="#f7f5f2", highlightthickness=0)
circle = canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
canvas.pack()
status_label = tk.Label(root, text="Aucun fichier sélectionné.", fg="red", bg="#f7f5f2", font=("Arial", 9, "italic"))
status_label.pack(pady=0)
input_path_var.trace_add("write", update_validation_icon)

# Dossier sortie
tk.Label(root, text="Dossier de sortie :", font=("Arial", 12, "bold"), bg="#f7f5f2").pack(pady=5)
tk.Entry(root, textvariable=output_path_var, width=40, font=("Arial", 10)).pack()
tk.Button(root, text="Choisir un dossier", command=select_output_folder, font=("Arial", 10, "bold"), bg="#e6e6e6").pack(pady=5)

# Cases à cocher
checkbox_frame = tk.Frame(root, bg="#f7f5f2")
checkbox_frame.pack(pady=10)
tk.Checkbutton(checkbox_frame, text="Générer Excel", variable=generate_excel_var, bg="#f7f5f2", font=("Arial", 10)).pack(anchor="w")
tk.Checkbutton(checkbox_frame, text="Générer Word", variable=generate_word_var, bg="#f7f5f2", font=("Arial", 10)).pack(anchor="w")
tk.Checkbutton(checkbox_frame, text="Générer HTML", variable=generate_html_var, bg="#f7f5f2", font=("Arial", 10)).pack(anchor="w")

# Bouton lancer
tk.Button(root, text="Lancer le programme", command=run_program, font=("Arial", 10, "bold"), bg="#4caf50", fg="white").pack(pady=20)

# Footer
tk.Label(root, text="Créateur : by Anthony MANGIN, Thibaut PAYEN", font=("Arial", 8), fg="#777777", bg="#f7f5f2").pack(side="bottom", pady=5)

root.mainloop()