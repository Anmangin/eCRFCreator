
import json
import xml.etree.ElementTree as ET



def remove_details_tags(text):
    # Utilisation de l'expression régulière pour supprimer les balises <details>...</details>
    cleaned_text = re.sub(r'<(th|td)\s+class=["\']check["\'][^>]*>.*?<!--\$htmlbalise-->.', '', text, flags=re.DOTALL)
    # cleaned_text = re.sub(r'<(th|td)\s+class=["\']check["\'][^>]*>.*?<!--\$htmlbalise-->.*?</\1>', '', text, flags=re.DOTALL)


    return cleaned_text

    
def Get_objt(root, racine, keyname, fields):
        ProForm = {}
        for FWAW in root.iter(racine):
            key = FWAW.findtext(keyname)
            if key:  # Vérifie que la clé existe
                ProForm[key] = {field: FWAW.findtext(field) for field in fields}
        return ProForm

def filtrer_par_cle(dictionnaire, champ, valeur):
    return {key: val for key, val in dictionnaire.items() if val.get(champ) == valeur}





def lire_et_trier_donnees(pathfileXML, config_path=r'Python\config.json'):


    # with open("print.txt", "w") as log_file:
    #         log_file.write(config_path)

    # Charger la configuration
    with open(config_path, 'r') as f:

        config = json.load(f)

    # Charger et analyser l'XML
    tree = ET.parse(pathfileXML)
    root = tree.getroot()
    version = root.attrib.get('ver')
    data = {"version": version}

    # Extraire et transformer les données à partir du fichier XML selon la config
    for key, params in config.items():
        racine = params["racine"]
        keyname = params["keyname"]
        fields = params["fields"]
        data[key] = Get_objt(root, racine, keyname, fields)

    # Trier les clés spécifiques


    trier_cles = ["ProPatientVisit", "ProVisitForm", "ProFormGroup", "ProGroupItem", "ProCodeListItem"]
    for key in trier_cles:
        if key in data:
            data[key] = dict(sorted(data[key].items(), key=lambda item: int(item[1].get("OrderNo", 0))))
    # Ajouter le champ "Display" pour ProCodeList
    data["ProCodeList"] = ajouter_display_pro_codelist(data)

    # Ajouter le champ "Display" pour ProItem
    data["ProItem"] = ajouter_display_pro_item(data)




    return data




def ajouter_display_pro_codelist(data):
    """Ajoute un champ 'Display' pour les ProCodeList."""




    for key, value in data["ProCodeList"].items():
        # Filtrer les items associés à la ProCodeList actuelle
        filtered_items = {k: v for k, v in data["ProCodeListItem"].items() if v["ProCodeListGuid"] == key}

        # Construire la chaîne de caractères pour le champ Display
        if len(filtered_items) < 15:
            rep = "<br>".join(f"🔘 {item['Value']} - <b>{item['Caption']}</b>" for item in filtered_items.values())
        else:
            rep = "🔘 Radio bouton trop long"

        # Ajouter le champ Display
        data["ProCodeList"][key]["Display"] = rep

    return data["ProCodeList"]


def ajouter_display_pro_item(data):
    """Ajoute un champ 'Display' pour les ProItem."""
    for key, value in data["ProItem"].items():
            if value["ProDataTypeId"] == "5":
                rep = "📅 DD/MM/YYYY"
            else:
                rep = f"{value['SasType']} - {value['MaxLength']}"

            # Ajouter le champ Display
            if rep :data["ProItem"][key]["Display"] = rep





            # Partie du la nature de la var
            if value["Hidden"]=="True": Hidden="👻"
            else: Hidden=""
            if value["ReadOnly"]=="True": ReadOnly="🔒"
            else: ReadOnly=""
            value["Status"]= Hidden + ReadOnly


    return data["ProItem"]

# Appel de la fonction


def find_arbo(TBNode):
            if TBNode["ParentTBNodeId"]=="6":source="Fiche"
            elif TBNode["ParentTBNodeId"]=="7":source="groupe"
            elif TBNode["ParentTBNodeId"]=="8":source="item"
            elif TBNode["ParentTBNodeId"]=="9":source="codelist"
            elif int(TBNode["ParentTBNodeId"]) < 10 : source="unknown"
            else : source="unknown"
            return source
    




def get_message(data,ProItemGuid,ProGroupGuid,ProFormGuid):
    """genere le message pour les editcheck"""
    Message=""
    i=0
    ProEdit=filtrer_par_cle( data,"ProItemGuid",ProItemGuid)
    for  key,Edit in ProEdit.items():
        if (Edit["ProItemGuid"] == ProItemGuid) and (Edit["TargetProFormGuid"]==ProFormGuid or Edit["TargetProFormGuid"] is None) and (Edit["TargetProGroupGuid"]==ProGroupGuid or Edit["TargetProGroupGuid"] is None)  :
            i+=1
            EditACtion= Edit["ProEditActionId"]
            if   EditACtion =="1"           :EditACtion="Valid"
            elif EditACtion =="3"           :EditACtion="Enabled"
            elif EditACtion =="6"           :EditACtion="Hidden"
            elif EditACtion =="10"          :EditACtion="DVA"
            elif EditACtion =="11"          :EditACtion="Email"
            elif EditACtion =="9"           :EditACtion="DVC"
            elif EditACtion =="23"          :EditACtion="Dynamic codelist filter"
            msg=Edit["Message"]
            chk=Edit["ActionExpression"]
            DTE=Edit['DataExpression']
            path=Edit["TargetPath"]

            Message+=f"<tr><td> {EditACtion}:{path}</td> </tr>"
            Message+=f"<tr> <td> <pre><code class='javascript'>#Action Expression \n{chk} \n#data Expression \n{DTE} \n</code></pre> </td>"
            Message+=f"<td> {msg}</td> </tr>"


    Message+="</table></details>"
    if i==0:Message=""
    else: Message= f"<details> <summary>{i} EditCheck </summary><table>" + Message


    return Message




def exporter_donnees_markdown_eCRF(data,unic_form):

        order=0
        JSON_EXPORT = {}
        for key, value in data["ProPatient"].items():
            print(value)
            ProFormGuid=value["ProFormGuid"]
            Caption=value["Caption"]
            order,JSON_EXPORT = ADD_FORM(data,"Patient Template",ProFormGuid,order,JSON_EXPORT)
       


        for  PVkey,PatientVisit in data["ProPatientVisit"].items():



            # Ecriture des variables nécéssaire pour l'affichage
            ProVisitGuid        =PatientVisit["ProVisitGuid"]
            V_description       =data["ProVisit"][ProVisitGuid]["Description"]
            V_Caption           =data["ProVisit"][ProVisitGuid]["Caption"]
            V_OrderNo           =PatientVisit["OrderNo"]



            ProVisitForm=filtrer_par_cle( data["ProVisitForm"],"ProVisitGuid",ProVisitGuid)
           
            for  VFkey,VisitForm in ProVisitForm.items():
                ProFormGuid=VisitForm.get("ProFormGuid")
                written=data["ProForm"][ProFormGuid].get("written", False)
                if written and unic_form: continue    

                # Ecriture des variables nécéssaire pour l'affichage
                F_OrderNo           =VisitForm["OrderNo"]

                data["ProForm"][ProFormGuid]["written"]=True
                order,JSON_EXPORT = ADD_FORM(data,V_description,ProFormGuid,order,JSON_EXPORT)

        return JSON_EXPORT
        

def ADD_FORM(data,V_description,ProFormGuid,order,JSON_EXPORT):

                F_description       =data["ProForm"][ProFormGuid]["Description"]
                F_SasName           =data["ProForm"][ProFormGuid]["SasName"]
                F_Caption           =data["ProForm"][ProFormGuid]["Caption"]
    
                ProFormGroup=filtrer_par_cle( data["ProFormGroup"],"ProFormGuid",ProFormGuid)
                for  key,FormGroup in ProFormGroup.items():
                    # Ecriture des variables nécéssaire pour l'affichage
                    ProGroupGuid        =FormGroup["ProGroupGuid"]
                    G_description       =data["ProGroup"][ProGroupGuid]["Caption"]
                    G_Caption           =data["ProGroup"][ProGroupGuid]["Caption"]

                    ProGroupItem=filtrer_par_cle( data["ProGroupItem"],"ProGroupGuid",ProGroupGuid)

                    for  GI_key,GroupItem in ProGroupItem.items():
                        # Ecriture des variables nécéssaire pour l'affichage
                        I_OrderNo           =GroupItem["OrderNo"]
                        ProItemGuid         =GroupItem.get("ProItemGuid")
                        I_description       =data["ProItem"][ProItemGuid]["Description"]
                        i_SasName           =data["ProItem"][ProItemGuid]["SasName"]
                        I_Caption           =data["ProItem"][ProItemGuid]["Caption"]
                        ProCodeListGuid     =data["ProItem"][ProItemGuid]["ProCodeListGuid"]
                        Hidden              =data["ProItem"][ProItemGuid]["Hidden"]
                        Disabled            =data["ProItem"][ProItemGuid]["Disabled"]
                        ReadOnly            =data["ProItem"][ProItemGuid]["ReadOnly"]
                        i_Display           =data["ProItem"][ProItemGuid]["Display"]
                        I_Status            =data["ProItem"][ProItemGuid]["Status"]
                        ProItemCategoryGuid            =data["ProItem"][ProItemGuid]["ProItemCategoryGuid"]
                        if ProItemCategoryGuid: Cat_Description            =data["ProItemCategory"][ProItemCategoryGuid]["Description"]
                        else :Cat_Description=""
                        rep=""
                        if ProCodeListGuid :rep=data["ProCodeList"][ProCodeListGuid]["Display"]
                      
                        
                        Message = get_message(data["ProEdit"],ProItemGuid,ProGroupGuid,ProFormGuid)    
                        order+=1
                        if Cat_Description != "":Message= "Catérogie:" + Cat_Description + "<br>" +  Message
                        JSON_EXPORT = get_JSONLIGNE(JSON_EXPORT,V_description,F_description,G_description,GI_key,order,I_description,I_Caption,Message,rep,i_Display,I_Status,i_SasName)            
                return  order,JSON_EXPORT






def get_JSONLIGNE(JSON_EXPORT, V_description, F_description, G_description, GI_key,
                  order,I_description,I_caption, Message, rep,display, I_Status, i_SasName):
    # Assure-toi que la clé 'Patient' existe dans JSON_EXPORT
    if 'visites' not in JSON_EXPORT:
        JSON_EXPORT['visites'] = []

    # Cherche si le patient existe déjà dans la liste des patients, sinon crée-le
    visites = next((p for p in JSON_EXPORT['visites'] if p['V_description'] == V_description), None)
    
    if not visites:
        # Crée un nouveau patient avec V_description comme nom
        visites = {"V_description": V_description, "fiches": []}
        JSON_EXPORT['visites'].append(visites)

    # Cherche la fiche dans le patient, sinon crée-la
    fiche = next((f for f in visites['fiches'] if f['F_description'] == F_description), None)
    
    if not fiche:
        fiche = {"F_description": F_description, "groupes": []}
        visites['fiches'].append(fiche)

    # Cherche le groupe dans la fiche, sinon crée-le
    groupe = next((g for g in fiche['groupes'] if g['G_description'] == G_description), None)
    
    if not groupe:
        groupe = {"G_description": G_description, "questions": []}
        fiche['groupes'].append(groupe)


    # Ajout de la question dans le groupe
    question = {
         "GI_key": GI_key,
         "Item_Order":order,
        "I_description": I_description,
        "I_caption":I_caption,
        "Message": Message if Message else None,
        "rep": rep if rep else display,
        "I_Status": I_Status,
        "i_SasName": i_SasName
    }
    groupe['questions'].append(question)
    
    return JSON_EXPORT
