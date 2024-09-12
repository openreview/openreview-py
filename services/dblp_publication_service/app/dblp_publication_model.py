import os
import json
import subprocess

def generate_data(date):
    try:
        # call the java code
        # java code creates the file

        # Step 1: Compile the Java program
        javac_command = ['javac', '-cp', 'libs/*', 'DblpExampleParser.java']
        subprocess.run(javac_command, check=True)

        # Step 2: Run the Java program with the necessary arguments
        java_command = [
            'java', '-Xmx8G', '-cp', '.:libs/*', 
            'DblpExampleParser', 'data/dblp.xml', 'data/dblp.dtd', date
        ]
        subprocess.run(java_command, check=True)

        # Step 3: Open the recentlyModified.json file
        json_file_path = os.path.join('data', 'recentlyModified.json')

        with open("data/recentlyModified.json", "r") as f:
            json_data = json.load(f)
            return json_data
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running Java commands: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")