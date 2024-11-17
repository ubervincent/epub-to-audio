import os 
import zipfile

def extract_zip(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

if __name__ == "__main__":
    extract_zip("test.epub", "data")