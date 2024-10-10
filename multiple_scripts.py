import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PythonFileHandler(FileSystemEventHandler):
    def __init__(self, files):
        self.files = files

    def on_modified(self, event):
        # Check if the modified event is for a Python file we're interested in
        if event.src_path in self.files:
            print(f'Detected change in: {event.src_path}. Running the script...')
            self.run_file(event.src_path)

    def run_file(self, file):
        # Ensure it's a valid Python file before running
        if os.path.isfile(file) and file.endswith('.py'):
            try:
                # Running the specified Python file
                result = subprocess.run(['python', file], check=True, capture_output=True, text=True)
                print(f'Output of {file}:\n{result.stdout}')  # Print standard output
            except subprocess.CalledProcessError as e:
                print(f'Error while running {file}:\n{e.stderr}')  # Print error output
        else:
            print(f'File {file} does not exist or is not a Python file.')

def main():
    # Define the full path to the Python files you want to monitor
    base_path = '.'  # Ensure this is the correct path

    # List of Python files to monitor
    file_list = [
        os.path.join(base_path, 'sticker_bot.py'),  # Full path to the file
        os.path.join(base_path, 'inline.py'),
        # Add more files as needed
    ]

    # Create an event handler
    event_handler = PythonFileHandler(file_list)
    observer = Observer()

    # Monitor the directory where the files are located
    directory_to_monitor = base_path
    observer.schedule(event_handler, directory_to_monitor, recursive=False)

    # Start monitoring
    observer.start()
    print("Monitoring for changes in:", directory_to_monitor)

    # Start all specified files immediately
    for file in file_list:
        print(f'Starting {file}...')
        event_handler.run_file(file)  # Run each file at startup

    try:
        while True:
            time.sleep(0.1)  # Keep the script running with a shorter sleep interval
    except KeyboardInterrupt:
        observer.stop()
        print("Stopping the monitoring.")
    observer.join()

if __name__ == "__main__":
    main()
