import os
import json
import subprocess


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


def generate_data(date):
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
