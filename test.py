import csv
import os
import xml.etree.ElementTree as ET
import urllib.request
import requests
import itertools

# Namespace
ns = {"g": "http://base.google.com/ns/1.0"}

def remove_elements_from_title(item):
    title = item.find(".//title", ns)
    if title is not None:
        # Replace caratteri ; con spazio vuoto
        title_text = title.text.replace(";", "")
        # Replace parola "Ermenegildo" con spazio vuoto
        title_text = title_text.replace("Ermenegildo", "")
        for attr in ['g:brand', 'g:color', 'g:gender', 'g:size']:
            elem = item.find(attr, ns)
            if elem is not None and elem.text is not None:
                title_text = title_text.replace(elem.text, '')
        # Rimuovi eventuali spazi iniziali o finali dal titolo
        title_text = title_text.strip()
        # Aggiorna il testo dell'elemento di titolo con il testo modificato
        title.text = title_text
        
urls = {
    'US': 'https://www.zegna.com/feeds/google-us-en2.xml',
    'IT': 'https://www.zegna.com/feeds/google-it-it2.xml',
    'GB': 'https://www.zegna.com/feeds/google-uk-en2.xml',
    'FR': 'https://www.zegna.com/feeds/google-fr-fr2.xml',
    'DE': 'https://www.zegna.com/feeds/google-de-de2.xml',
    'ES': 'https://www.zegna.com/feeds/google-es-es2.xml',
    'MX': 'https://www.zegna.com/feeds/google-mx-es2.xml',
    'JP': 'https://www.zegna.com/feeds/google-jp-ja2.xml',
    'AU': 'https://www.zegna.com/feeds/google-au-en2.xml',
    'CA': 'https://www.zegna.com/feeds/google-ca-en2.xml',
    'NL': 'https://www.zegna.com/feeds/google-nl-en2.xml',
    'CH': 'https://www.zegna.com/feeds/google-ch-de2.xml',
    'BE': 'https://www.zegna.com/feeds/google-be-fr2.xml',
    'AT': 'https://www.zegna.com/feeds/google-at-de2.xml',
    'PT': 'https://www.zegna.com/feeds/google-pt-pt2.xml'
}


# Nuovi input feed_file_path e include_or_exclude
country_code = input("Inserisci il codice paese (US, IT, GB, FR, DE, ES, MX, JP, AU, CA, NL, CH, BE, AT, PT): ")
xml_base_file_url = urls.get(country_code.upper())
include_or_exclude_item_group = input("Vuoi filtrare gli item group id? (S/N): ")
if include_or_exclude_item_group.upper() == 'S':
    item_group_id_file_path = input("Inserisci il percorso del file txt per filtrare per Item group ID: ")
    item_group_include = input("Vuoi includere o escludere gli item group ID specificati? (I/E): ")
include_or_exclude_id = input("Vuoi filtrare per ID? (S/N): ")
if include_or_exclude_id.upper() == 'S':
    id_file_path = input("Inserisci il percorso del file txt per filtrare per ID: ")
    id_include = input("Vuoi includere o escludere gli ID specificati? (I/E): ")
include_or_exclude_title = input("Vuoi filtrare per titolo? (S/N): ")
if include_or_exclude_title.upper() == 'S':
    title_filter = input("Inserisci il testo da cercare nel titolo: ")
    title_include = input("Vuoi includere o escludere gli elementi che contengono il testo specificato nel titolo? (I/E): ")

    
# Aggiungere un header "User-Agent" per evitare il codice di errore 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Aprire la URL in background per impostare eventuali cookie e sessioni
session = requests.Session()
session.get(xml_base_file_url, headers=headers)

# Scarica il file XML di base
response = session.get(xml_base_file_url, headers=headers)
with open("prodotti.xml", "wb") as f:
    f.write(response.content)
xml_base_file = "prodotti.xml"


# Richiedi il percorso del file CSV all'utente
csv_file_path = input("Inserisci il percorso del file dei tracciamenti: ")
with open(csv_file_path, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Nome del file XML da creare
        xml_file_name = row["Nome catalogo"] + ".xml"

        # Stringhe da concatenare a <link> nell'XML di base
        clicktracker = row["Clicktracker"]
        utm = row["Utm"]

        # Copia il file XML di base per creare il nuovo file XML
        xml_tree = ET.parse(xml_base_file)
        root = xml_tree.getroot()

        # Filtra gli elementi in base alla scelta dell'utente per item group id
        filtered_items = []
        if include_or_exclude_item_group.upper() == 'S':
            with open(item_group_id_file_path, "r") as f:
                item_group_ids = f.read().splitlines()
            for item in root.findall(".//item", ns):
                item_group_id = item.find("g:item_group_id", ns).text
                if item_group_include.upper() == 'I':
                    if item_group_id in item_group_ids:
                        filtered_items.append(item)
                else:
                    if item_group_id not in item_group_ids:
                        filtered_items.append(item)
        else:
            filtered_items = root.findall(".//item", ns)
        
        # Filtra gli elementi in stock
        filtered_items= [item for item in filtered_items if item.find("g:availability", ns).text.strip().lower() == 'in stock']
        
        # Raggruppa gli item per g:item_group_id
        grouped_items = itertools.groupby(filtered_items, lambda x: x.find("g:item_group_id", ns).text)

        # Seleziona solo un item per ogni gruppo
        selected_items = [next(group) for _, group in grouped_items]

        # Filtra gli elementi in base alla scelta dell'utente per ID
        selected_items = selected_items  # inizializza la lista di elementi selezionati
        if include_or_exclude_id.upper() == 'S':
            with open(id_file_path, "r") as f:
                ids = f.read().splitlines()
            if id_include.upper() == 'I':
                selected_items = [item for item in selected_items if item.find("g:id", ns).text in ids]
            else:
                selected_items = [item for item in selected_items if item.find("g:id", ns).text not in ids]


        # Filtra gli elementi in base alla scelta dell'utente per titolo
        if include_or_exclude_title.upper() == 'S':
            if title_include.upper() == 'I':
                selected_items = [item for item in selected_items if title_filter in item.find("title", ns).text]
            else:
                selected_items = [item for item in selected_items if title_filter not in item.find("title", ns).text]

        # Rimuovi i contenuti dei vari attributi dal titolo
        for item in selected_items:
            remove_elements_from_title(item)
            
        
        # Crea il nuovo file XML
        xml_root = ET.Element("rss", attrib={"version": "2.0"})
        channel = ET.SubElement(xml_root, "channel")

        # Aggiungi gli elementi filtrati al nuovo file XML
        for item in selected_items:
            channel.append(item)

        # Aggiungi le stringhe di clicktracker e utm a <link> in ogni elemento
        for item in channel.findall(".//item", ns):
            link = item.find(".//link", ns).text
            new_link = clicktracker + link.split('?utm')[0] + utm
            item.find(".//link", ns).text = new_link
            
        # Elimina UTM da <g:display_ads_link> in ogni elemento
        for item in channel.findall(".//item", ns):
            display_ads_link = item.find("g:display_ads_link", ns).text
            new_display_ads_link = display_ads_link.split('?utm')[0]
            item.find("g:display_ads_link", ns).text = new_display_ads_link
            
        # Scrivi il nuovo file XML troncando prima eventuali spazi vuoti
        xml_tree = ET.ElementTree(xml_root)
        xml_tree.write(xml_file_name, encoding="UTF-8", xml_declaration=True, method="xml", short_empty_elements=False)
        with open(xml_file_name, "r+", encoding="UTF-8") as f:
            file_content = f.read().replace("ns0", "g")
            f.seek(0)
            f.write(file_content)
            f.truncate()

    print("Generazione dei feed completata.")
    os.remove("prodotti.xml")
    raise SystemExit
    raise SystemExit
