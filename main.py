import os 
import zipfile
import xml.etree.ElementTree as ET
import json
import shutil
from xml.etree.ElementTree import fromstring as parse_string


namespaces = {
    'xmlns': 'http://www.w3.org/1999/xhtml',
    'epub': 'http://www.idpf.org/2007/ops',
    'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    'opf': 'http://www.idpf.org/2007/opf',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

def extract_zip(zip_path, extract_path):
    zip_ref = zipfile.ZipFile(zip_path, 'r')
    zip_ref.extractall(os.path.join(extract_path, os.path.splitext(os.path.basename(zip_path))[0]))
    zip_ref.close()

def find_ncx_file(extract_path):
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith('.ncx'):
                return os.path.join(root, file)
    return None

def find_nav_file(extract_path):
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith('.xhtml') or file.endswith('.html'):
                # Check if file contains nav element
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for both with and without epub:type
                    if '<nav epub:type="toc"' in content or \
                       ('<nav' in content and '<ol>' in content):
                        return file_path
    return None

def extract_nav(extract_path):
    nav_file = find_nav_file(extract_path)
    
    if nav_file is None:
        ncx_file = find_ncx_file(extract_path)
        if ncx_file is None:
            raise ValueError("Neither nav nor ncx file found in the extracted path.")
        return ncx_file
    return nav_file

def processing_ncx(ncx_file):
    # Parse the NCX file
    tree = ET.parse(ncx_file)
    root = tree.getroot()

    # Define the namespace
    ns = {'ncx': 'http://www.daisy.org/z3986/2005/ncx/'}

    semantic_titles = []


    # Find all navPoints and their corresponding content src and text
    nav_points = root.findall('.//ncx:navPoint', namespaces=ns)
    
    for nav_point in nav_points:
        content_src = nav_point.find('ncx:content', namespaces=ns).get('src')
        text = nav_point.find('ncx:navLabel/ncx:text', namespaces=ns).text
        html_title = {"title": text, "href": content_src}
        semantic_titles.append(html_title)
        
    return semantic_titles

def processing_nav(nav_file):
    # Register the namespaces first

    
    # Parse with namespaces preserved
    tree = ET.parse(nav_file)
    root = tree.getroot()
    
    # Find the nav element with toc type
    nav = root.find('.//xmlns:nav[@epub:type="toc"]', namespaces)
    if nav is None:
        raise ValueError("No TOC nav element found")
        
    semantic_titles = []
    for link in nav.findall('.//xmlns:a', namespaces):
        semantic_titles.append({
            "title": link.text,
            "href": link.get('href')
        })
    
    return semantic_titles


def processing_content(extract_path):
    nav_file = extract_nav(extract_path)
    
    print(nav_file)

    if nav_file.endswith('.ncx'):
        return processing_ncx(nav_file)
    else:
        return processing_nav(nav_file)
    

# def change_to_semantic_href(semantic_titles, extract_path):
#     """
#     Changes the href of each semantic title to use the title as the filename and updates the corresponding file in the filesystem.
#     """
#     for title in semantic_titles:
#         # Replace spaces with underscores and make lowercase for filename compatibility
#         filename = title["title"].replace(" ", "_").lower()
#         original_file_path = os.path.join(extract_path, title["href"])
#         original_extension = os.path.splitext(title["href"])[1]
        
#         if os.path.exists(original_file_path):
#             os.rename(original_file_path, os.path.join(extract_path, filename + original_extension))
#         else:
#             print(f"Warning: File {original_file_path} does not exist, skipping rename.")
        
#         title["href"] = os.path.join(extract_path, filename + original_extension)

#     return semantic_titles

def extract_text_from_epub(file, extract_path):
    extract_zip(file, extract_path)
    
    semantic_titles = processing_content(extract_path)
    
    file_name = os.path.splitext(os.path.basename(file))[0]

    for title in semantic_titles:
        file_path = os.path.join(extract_path, file_name, title["href"])
        
        root = ET.parse(file_path).getroot()
        for child in root:
            print(child.tag, child.text)
            
        body = root.find('.//{*}body')
        if body is not None:
            flattened_text = ET.tostring(body, method='text', encoding='unicode').strip()

        # add the text to the title
        title["text"] = flattened_text
        
    # write semantic_titles to a json file
    with open(os.path.join(extract_path, file_name + ".json"), "w") as f:
        json.dump(semantic_titles, f)

    shutil.rmtree(os.path.join(extract_path, file_name))

    return semantic_titles

if __name__ == "__main__":
    print(extract_text_from_epub("test2.epub", "data"))