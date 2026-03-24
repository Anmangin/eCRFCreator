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

# --- tes imports métiers
from XML_Function import lire_et_trier_donnees, exporter_donnees_markdown_eCRF, print_xls_from_edit_check, print_doc_xml


# ===================== Utils PyInstaller / chemins =====================

def resource_base() -> Path:
    """
    Dossier de base des ressources :
    - en .exe (PyInstaller): sys._MEIPASS
    - en script: dossier du fichier courant (__file__)
    """
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def resource_path(relative_path):
    # Mode EXE → fichiers extraits dans sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        # Mode script → dossier courant du script Python
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def tcl_path_str(p: Path) -> str:
    """Chemin normalisé pour Tk/Tcl (slashes)."""
    return str(p).replace("\\", "/")

def read_text(rel_path: str, encoding="utf-8") -> str:
    """Lecture texte sûre depuis une ressource packagée."""
    p = resource_path(rel_path)
    print(rel_path)
    return open(p, encoding=encoding).read()


# ===================== I/O JSON =====================

def save_json(obj, output_dir: str, file_name="export.json"):
    """Sauvegarde un objet Python en JSON (pas de double dump)."""
    try:
        output_dir = str(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        json_file_path = os.path.join(output_dir, file_name)
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        print(f"Fichier JSON sauvegardé : {json_file_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du JSON : {e}")


# ===================== Parsing / validation =====================

def Get_objt(root, racine, keyname, fields):
    ProForm = {}
    for FWAW in root.iter(racine):
        key = FWAW.findtext(keyname)
        if key:
            ProForm[key] = {field: FWAW.findtext(field) for field in fields}
    return ProForm

def validate_xml_file(filepath):
    """
    Valide le fichier XML. Retourne (True/False, message).
    Moins fragile : accepte XML avec ou sans BOM, casse différente, etc.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip().lstrip('\ufeff')
            if first_line.lower()[0:5] !="<?xml" or not ("encoding='utf-8'" in first_line.lower() or 'encoding="utf-8"' in first_line.lower()):
                return False, "En-tête XML inattendu (attendu: XML UTF-8)."

        tree = ET.parse(filepath)
        root = tree.getroot()

        required = [
            (".//ProPatient", "Pas d'objet patient présent, le programme nécessite un XML fini."),
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


# ===================== GUI actions =====================

def update_validation_icon():
    filepath = input_path_var.get()
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
    # Entrées
    Pathin = input_path_var.get()
    if not Pathin.lower().endswith(".xml"):
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier XML.")
        return

    output_path = output_path_var.get()
    if not Pathin or not output_path:
        messagebox.showerror("Erreur", "Veuillez fournir les deux chemins avant de lancer le programme.")
        return

    is_valid, message = validate_xml_file(Pathin)
    if not is_valid:
        messagebox.showerror("Validation échouée", message)
        return

    file_name = os.path.basename(Pathin).replace('.xml', '')

    try:
        # --- lecture + transformation
        config_path = resource_path("Python/config.json")
        data = lire_et_trier_donnees(Pathin, str(config_path))
        JSON_EXPORT = exporter_donnees_markdown_eCRF(data, False)  # False forcé, comme tu voulais

        # --- export JSON (corrigé: pas de double json.dumps)
        save_json(JSON_EXPORT, output_path, file_name="resultat_export.json")

        # --- génération HTML
        css = read_text("Python/style.css")
        printpage = read_text("Python/print.html")
        template_html = read_text("Python/Template_CRF.html")

        # injecte les données
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
        print_xls_from_edit_check(Pathin, out_html.replace('html', 'xlsx'))
        print_doc_xml(Pathin, out_html.replace('html', 'docx'))

        print(f"Le fichier {out_html} a été généré avec succès.")
        messagebox.showinfo("Succès", "Le programme a été exécuté avec succès !")

    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")


# ===================== GUI =====================

root = tk.Tk()
root.title("Convertisseur XML vers HTML")
root.geometry("500x420")
root.configure(bg="#f7f5f2")

# Icône: ICO -> fallback PNG
try:
    ico = resource_path("Python/images.ico")
    if os.path.exists(ico):
        root.iconbitmap(tcl_path_str(ico))
    else:
        raise FileNotFoundError("ICO manquant")
except Exception as e:
    try:
        png = resource_path("Python/images.png")
        if png.exists():
            img = tk.PhotoImage(file=tcl_path_str(png))
            root.iconphoto(True, img)
    except Exception:
        print(f"[WARN] Icon load failed: {e}")

# Variables
input_path_var = tk.StringVar()
output_path_var = tk.StringVar()
input_path_var.trace_add("write", lambda *args: update_validation_icon())

# Styles
label_font = ("Arial", 12, "bold")
entry_font = ("Arial", 10)
button_font = ("Arial", 10, "bold")

# Widgets
input_label = tk.Label(root, text="Fichier XML d'entrée :", font=label_font, bg="#f7f5f2", fg="#333333")
input_label.pack(pady=10)

input_frame = tk.Frame(root, bg="#f7f5f2")
input_frame.pack(pady=5)

input_entry = tk.Entry(input_frame, textvariable=input_path_var, width=40, font=entry_font)
input_entry.pack(side="left", padx=5)

canvas = tk.Canvas(root, width=20, height=20, bg="#f7f5f2", highlightthickness=0)
circle = canvas.create_oval(2, 2, 18, 18, fill="red", outline="")
canvas.pack(pady=0)

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

status_label = tk.Label(root, text="Aucun fichier sélectionné.", fg="red", bg="#f7f5f2", font=("Arial", 9, "italic"))
status_label.pack(pady=0)

footer_label = tk.Label(root, text="Créateur : by Anthony MANGIN", font=("Arial", 8), fg="#777777", bg="#f7f5f2")
footer_label.pack(side="bottom", pady=5)

root.mainloop()
