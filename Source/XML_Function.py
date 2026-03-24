
import json
import xml.etree.ElementTree as ET
import xlsxwriter
from bs4 import BeautifulSoup
from docx.shared import Cm
from docx.shared import RGBColor
import re



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
            
            if value["ProDataTypeId"] == "5" and value["ProControlTypeId"] == "6":
                print(value)
                rep = "📅 YYYY"
            elif value["ProDataTypeId"] == "5":
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
    

def get_check_type(number):
    if   number =="1":return "Valid"
    elif number =="2":return "Required"
    elif number =="3":return "Enabled"
    elif number =="5":return "Required Enabled"
    elif number =="6":return "Hidden"
    elif number =="7":return "Read only"
    elif number =="8":return "Caption change"
    elif number =="9":return "DVC"
    elif number =="10":return "DVA"
    elif number =="11":return "Email"
    elif number =="12":return "Create Form"
    elif number =="14":return "Post save warning"
    elif number =="17":return "Unique value required"
    elif number =="21":return "Disabled Hidden"
    elif number =="22":return "Dynamic codelist setup"
    elif number =="23":return "Dynamic codelist filter"
    return number

def check_data_type(number):
    if   number =="1":return "Text Box"
    elif number =="2":return "Text Area"
    elif number =="3":return "Radio Button"
    elif number =="4":return "Check Box"
    elif number =="5":return "Combo Box"
    elif number =="6":return "Year"
    elif number =="7":return "YearMonth"
    elif number =="8":return "Date"
    elif number =="10":return "Time"
    elif number =="13":return "Label"
    elif number =="16":return "Textbox with MedDRA"
    elif number =="18":return "Timer"
    elif number =="18":return "ComboBox Dynamic"
    return number


def get_message(data,ProItemGuid,ProGroupGuid,ProFormGuid):
    """genere le message pour les editcheck"""
    Message=""
    i=0
    ProEdit=filtrer_par_cle( data,"ProItemGuid",ProItemGuid)
    for  key,Edit in ProEdit.items():
        if (Edit["ProItemGuid"] == ProItemGuid) and (Edit["TargetProFormGuid"]==ProFormGuid or Edit["TargetProFormGuid"] is None) and (Edit["TargetProGroupGuid"]==ProGroupGuid or Edit["TargetProGroupGuid"] is None)  :
            i+=1
            EditACtion= Edit["ProEditActionId"]
            EditACtion = get_check_type(EditACtion)
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


def create_graph(data):
    dictionnary = dict()
    nodes = ["Trial", "Site", "Patient", "Visit", "Form", "Group", "Item", "CodeList", "CodeListItem"]
    for nodetype in nodes:
        name = "Pro" + nodetype
        for elem in data.iter(name):
            try:
                guid = elem.find("ProObjectGuid").text
                dictionnary[guid] = dict()
                dictionnary[guid]['child'] = list()
                dictionnary[guid]['parent'] = list()
                dictionnary[guid]['Caption'] = elem.find('Caption').text
                dictionnary[guid]['tag'] = elem.tag
            except AttributeError:
                pass
            try:
                dictionnary[guid]['SasName'] = elem.find('SasName').text
            except:
                pass
            try:
                dictionnary[guid]['type'] = elem.find('ProControlTypeId').text
            except:
                pass
            try:
                if name != "ProCodeListItem":
                    dictionnary[guid]['child'].append((elem.find('ProCodeListGuid').text, 1))
            except:
                pass
            try:
                dictionnary[elem.find('ProCodeListGuid').text]['parent'].append(guid)
            except:
                pass
            try:
                dictionnary[guid]['Description'] = elem.find('Description').text
            except:
                pass
            try:
                dictionnary[guid]['Hidden'] = elem.find('Hidden').text
            except:
                pass
    # Links
    for i in range(6):
        link = "Pro" + nodes[i] + nodes[i+1]
        for elem in data.iter(link):
            parent = elem.find("Pro" + nodes[i]  + "Guid").text
            child =  elem.find("Pro" + nodes[i+1]+ "Guid").text
            order = int(elem.find("OrderNo").text)
            dictionnary[parent]['child'].append((child, order))
            dictionnary[child]['parent'].append(parent)
            try:
                dictionnary[child]['MaxOccurance'] = elem.find('MaxOccurance').text
            except:
                pass
    for elem in data.iter("ProCodeListItem"):
        parent = elem.find("ProCodeListGuid").text
        child = elem.find("ProObjectGuid").text
        order = int(elem.find("OrderNo").text)
        dictionnary[parent]['child'].append((child, order))
        dictionnary[child]['parent'].append(parent)
        dictionnary[guid]['Caption'] = elem.find('Caption').text
        dictionnary[guid]['Value'] = elem.find('Value').text
    return dictionnary

def create_edit_check_dictionnary(data):
    dictionnary = dict()
    keys = ["OID", "ProEditActionId", "TargetPath", "ActionExpression", "DataExpression"]
    for proedit in data.iter("ProEdit"):
        guids = list()
        try:
            guids.append(proedit.find("ProItemGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProGroupGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProFormGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProVisitGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProPatientGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProSiteGuid").text)
        except AttributeError:
             pass
        try:
            guids.append(proedit.find("ProTrialGuid").text)
        except:
             pass
        OID = proedit.find('OID').text
        dictionnary[OID] = dict()
        if len(guids) == 0: print(OID)
        for k in keys:
            sub = proedit.find(k).text
            dictionnary[OID][k] = sub
        dictionnary[OID]["lower"] = guids[0]
    return dictionnary

# Useless, does not function with return
def recursive_move(graph, elem):
    try:
        print (graph[elem]['Caption'], graph[elem]['SasName'], check_data_type(graph[elem]['type']))
    except:
        loc = graph[elem]['child']
        for e in loc:
            recursive_move(graph, e)

def print_xls_from_edit_check(xmlFile, xlsName):
    data = ET.parse(xmlFile)
    editChecks = create_edit_check_dictionnary(data)
    graph = create_graph(data)
    # Create an new Excel file and add a worksheet
    workbook = xlsxwriter.Workbook(xlsName)
    worksheet = workbook.add_worksheet("Checks")
    cell_format = workbook.add_format()
    cell_format.set_text_wrap()
    ROWS = ['Item Name', "Item Type", "Test Type", "Action", "Data"]
    # TITLE ROW
    for i in range(len(ROWS)):
         worksheet.write(0, i, ROWS[i])
    l = 1
    checked = list()
    for k, v in editChecks.items():
        action = v['ActionExpression']
        # Remove the empty lines
        try:
            action = "\n".join([ll.rstrip() for ll in action.splitlines() if ll.strip()])
        except AttributeError:
             action = ""
        data = v['DataExpression']
        # Remove the empty lines
        try:
            data = "\n".join([ll.rstrip() for ll in data.splitlines() if ll.strip()])
        except AttributeError:
            data = ""           
        item = graph[editChecks[k]['lower']]
        checked.append(editChecks[k]['lower'])
        worksheet.write(l, 0, item['Caption'])
        worksheet.write(l, 1,item['tag'])
        worksheet.write(l, 2, get_check_type(v['ProEditActionId']))
        worksheet.write(l, 3, action, cell_format)
        worksheet.write(l, 4, data, cell_format)
        l += 1
    worksheet.autofit()
    worksheet.autofilter(0, 0, l - 1, len(ROWS)-1)
    worksheet2 = workbook.add_worksheet('Items Without Checks')
    l = 1
    worksheet2.write(0, 0, 'Caption', cell_format)
    worksheet2.write(0, 1, 'SasName', cell_format)
    worksheet2.write(0, 2, 'type', cell_format)
    for id, node in graph.items():
        if node['tag'] == "ProItem":
            if id not in checked:
                worksheet2.write(l, 0, node['Caption'], cell_format)
                worksheet2.write(l, 1, node['SasName'], cell_format)
                worksheet2.write(l, 2, check_data_type(node['type']), cell_format)
                l += 1
    worksheet2.autofilter(0, 0, l - 1, 2)
    worksheet2.autofit()
    workbook.close()


def print_graph(graph, head, lvl=0, fileName=None):
    lns = graph[head]['child']
    tag = graph[head]['tag']
    try:
        desc = graph[head]['Description'].strip()
        try:
            typ = check_data_type(graph[head]['type'])
        except:
            typ = ''
        try:
            sasNam = graph[head]['SasName']
        except:
            sasNam = ''
        if len(desc) > 0:
            print(desc, typ, sep="\t", file=fileName)
    except:
        print("\t", graph[head]['Caption'], file=fileName)
    for e in sorted(lns, key = lambda e:e[1]):
        lvl = lvl + 1
        print_graph(graph, e[0], lvl, fileName)


def print_doc_xml(xmlFile, docFile, head=None):
    data = ET.parse(xmlFile)
    graph = create_graph(data)
    # Find the head
    if head == None:
        for k, v in graph.items():
            if v['tag'] == 'ProPatient':
                head = k
                break
    from docx import Document
    document = Document()
    document.add_heading("SUMMARY", level=1)
    internal_func_doc(graph, document, head=head, lvl=2, unique=False, summary=True)
    document.add_page_break()
    document.add_heading("CRF", level=1)
    internal_func_doc(graph, document, head=head, lvl=2, buffer=list())
    document.save(docFile)


def internal_func_doc(graph, documentName, head=None, lvl=0, buffer=list(), maxi=False, unique=True,uniqueList=list(), summary=False):
    lns = graph[head]['child']
    tag = graph[head]['tag']
    if tag == 'ProVisit' and not summary:
        documentName.add_page_break()
    if summary and tag not in ["ProTrial", "ProSite", "ProPatient", "ProVisit", "ProForm"]:
        return
    try:
        desc = graph[head]['Description'].strip()
        soup = BeautifulSoup(desc, "html.parser")
        desc = soup.get_text()
        if unique and tag in ["ProTrial", "ProSite", "ProPatient", "ProVisit", "ProForm"]:
            if head in uniqueList: return
            uniqueList.append(head)
        try:
            typ = check_data_type(graph[head]['type'])
        except:
            typ = ''
        try:
            hidden = graph[head]['Hidden']
        except:
            hidden = False
        try:
            sasNam = graph[head]['SasName']
        except:
            sasNam = ''
        try:
            repeat = graph[head]['MaxOccurance']
            if int(repeat) > 1:
                desc += " ⟳"
        except:
            repeat = ""
        if len(desc) > 0:
            if len(typ) == 0:
                try:
                    documentName.add_heading(desc, level=lvl)
                except ValueError:
                    documentName.add_heading(desc, level=9)
            else:
                buffer = (desc, typ, list(), hidden)
    except KeyError:
        buffer[2].append(graph[head]['Caption'])
    if len(buffer) > 0 and len(lns) == 0 and (maxi or tag != 'ProCodeListItem'):
        table = documentName.add_table(rows=1, cols=2)
        if buffer[3] and buffer[3] == "True":
            table.style = 'Medium Shading 1'
        else:
            table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].width = Cm(14)
        hdr_cells[0].text = buffer[0].replace("\\r\\n", "\n")
        codeList = "\n".join(buffer[2])
        hdr_cells[1].width = Cm(6)
        if len(buffer[2]) > 10:
            codeList = "\n".join(buffer[2][0:4] + ['...'] + buffer[2][-4:-1])
        if len(codeList)>0:
            para = hdr_cells[1].paragraphs[0].add_run(codeList)
            para.font.color.rgb = RGBColor(255, 0, 0)
        else:
            hdr_cells[1].text = buffer[1]
        buffer = list()
    ls = sorted(lns, key = lambda e:e[1])
    lvl = lvl + 1
    for i in range(len(ls)):
        e = ls[i]
        if i == len(ls) - 1:
            maxi = True
        else:
            maxi = False
        internal_func_doc(graph, documentName, e[0], lvl, buffer, maxi, unique, uniqueList, summary=summary)



def find_parentals(graph, id):
    for e in graph[id]['parents']:
        print(e)
        find_parentals(graph, e)
