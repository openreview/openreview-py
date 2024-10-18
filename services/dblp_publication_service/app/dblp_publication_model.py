import os
import json
import subprocess
import requests
import gzip


def json_generator(data):
    first_key = True
    yield "{"  # Start of the JSON object
    for key, articles in data.items():  # Iterate over each key in the dictionary
        if not first_key:
            yield ", "  # Add a comma between keys if not the first key
        else:
            first_key = False
        yield f'"{key}": ['  # Yield the key with quotes
        for i, article in enumerate(articles):
            if i > 0:
                yield ", "  # Add comma between articles
            yield json.dumps(article)  # Stream each article as a JSON string
        yield "]"
    yield "}"  # End of the JSON object


def decompress_and_save_gz(gz_file_path, output_file_path):
    print(f"Decompressing {gz_file_path}")
    with gzip.open(gz_file_path, 'rb') as gz_file:
        with open(output_file_path, 'wb') as output_file:
            output_file.write(gz_file.read())
    print(f"Saved decompressed file as {output_file_path}")

def get_dblp_file(url, filename):
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    print(f"Downloading {filename}")
    res = requests.get(url)
    if res.status_code == 200:
        with open(filename, "wb") as file:
            file.write(res.content)
        print(f"{filename} downloaded successfully.")
    else:
        print(f"Failed to download {filename}. Status code: {res.status_code}")


def generate_data(date):
    get_dblp_file("https://dblp.org/xml/dblp.dtd", "app/data/dblp.dtd")
    get_dblp_file("https://dblp.org/xml/dblp.xml.gz", "app/data/dblp.xml.gz")
    decompress_and_save_gz("app/data/dblp.xml.gz", "app/data/dblp.xml")
    try:
        # call the java code
        # java code creates the file

        # Step 1: Compile the Java program
        javac_command = ["javac", "-cp", "app/libs/*", "app/DblpParser.java"]
        subprocess.run(javac_command, check=True)

        # Step 2: Run the Java program with the necessary arguments
        java_command = [
            "java",
            "-Xmx8G",
            "-cp",
            ".:app/libs/*",
            "app.DblpParser",
            "app/data/dblp.xml",
            "app/data/dblp.dtd",
            date,
        ]
        subprocess.run(java_command, check=True)

        # Step 3: Open the recentlyModified.json file
        json_file_path = os.path.join("app/data", "recentlyModified.json")

        with open("app/data/recentlyModified.json", "r") as f:
            json_data = json.load(f)
            return json_generator(json_data)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running Java commands: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
