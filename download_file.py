
import os
import requests
import zipfile
import argparse
from urllib.parse import urlparse

def download_and_unzip(url, output_dir='.'):
    """
    Downloads a file from a URL, unzips it if it's a zip file, 
    and saves it to the specified directory.

    Args:
        url (str): The URL of the file to download.
        output_dir (str): The directory to save the file in.

    Returns:
        str: The path to the downloaded file or the directory where it was extracted.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Get filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "downloaded_file"
            
        file_path = os.path.join(output_dir, filename)

        print(f"Downloading {filename} to {file_path}...")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("Download complete.")

        # Check if the file is a zip file and unzip it
        if zipfile.is_zipfile(file_path):
            print(f"{filename} is a zip file. Extracting...")
            extract_dir = os.path.join(output_dir, os.path.splitext(filename)[0])
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"Extracted to {extract_dir}")
            os.remove(file_path) # remove the original zip file
            return extract_dir
        else:
            return file_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A tool to download a file from a URL and unzip it.')
    parser.add_argument('url', type=str, help='The URL of the file to download.')
    parser.add_argument('--output_dir', type=str, default='companydata', help='The directory to save the file in.')
    args = parser.parse_args()
    
    if not args.url:
        print("Please provide a URL in the 'url' argument.")
    else:
        downloaded_path = download_and_unzip(args.url, args.output_dir)
        if downloaded_path:
            print(f"\nFile processed successfully. Final path: {downloaded_path}")
