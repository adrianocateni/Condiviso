import csv
import os
import xml.etree.ElementTree as ET
import urllib.request

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
                # Aggiungi uno spazio alla fine del titolo se è stato rimosso un valore
                if elem.text.strip():
                    title_text += ' '
        # Rimuovi eventuali spazi iniziali o finali dal titolo
        title_text = title_text.strip()
        # Aggiorna il testo dell'elemento di titolo con il testo modificato
        title.text = title_text

# Nuovi input feed_file_path e include_or_exclude
xml_base_file_url = input("Inserisci l'URL del file XML di base: ")
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
include_or_exclude_availability = input("Vuoi filtrare per disponibilità? (S/N): ")
if include_or_exclude_availability.upper() == 'S':
    availability_include = input("Vuoi i prodotti in Stock o Out of Stock? (S/O): ")
    if availability_include.upper() == 'S':
        availability = 'in Stock'
        # filtrare i prodotti in Stock
    elif availability_include.upper() == 'O':
        availability = 'Out of Stock'
        # filtrare i prodotti Out of Stock

    

# Scarica il file XML di base
urllib.request.urlretrieve(xml_base_file_url, "prodotti.xml")
xml_base_file = "prodotti.xml"

# Leggi il file CSV e genera i feed
with open("track.csv", newline="") as csvfile:
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

        # Filtra gli elementi in base alla scelta dell'utente per ID
        if include_or_exclude_id.upper() == 'S':
            with open(id_file_path, "r") as f:
                ids = f.read().splitlines()
            if id_include.upper() == 'I':
                filtered_items = [item for item in filtered_items if item.find("g:id", ns).text in ids]
            else:
                filtered_items = [item for item in filtered_items if item.find("g:id", ns).text not in ids]

        # Filtra gli elementi in base alla scelta dell'utente per titolo
        if include_or_exclude_title.upper() == 'S':
            if title_include.upper() == 'I':
                filtered_items = [item for item in filtered_items if title_filter.lower() in item.find(".//title", ns).text.lower()]
            else:
                filtered_items = [item for item in filtered_items if title_filter.lower() not in item.find(".//title", ns).text.lower()]

        # Rimuovi i contenuti dei vari attributi dal titolo
        for item in filtered_items:
            remove_elements_from_title(item)
            
        # Filtra gli elementi in base alla scelta dell'utente per disponibilità
        if include_or_exclude_availability.upper() == 'S':
            if availability_include.upper() == 'S':
                # Filtra gli elementi in stock
                filtered_items = [item for item in filtered_items if item.find("g:availability", ns).text.strip().lower() == 'in stock']
            else:
                # Filtra gli elementi out of stock
                filtered_items = [item for item in filtered_items if item.find("g:availability", ns).text.strip().lower() == 'out of stock']
    
        
        # Crea il nuovo file XML
        xml_root = ET.Element("rss", attrib={"version": "2.0"})
        channel = ET.SubElement(xml_root, "channel")

        # Aggiungi gli elementi filtrati al nuovo file XML
        for item in filtered_items:
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
    raise SystemExit
