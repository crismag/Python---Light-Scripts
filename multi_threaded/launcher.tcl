import subprocess
import threading

def run_commands(commands, post_processing):
    # Create a list to hold the process objects
    processes = []
    
    # Define the event listener
    def event_listener(process):
        # Wait for the process to complete
        process.wait()
        # Signal that the process has completed
        event.set()
    
    # Define the process monitor
    def process_monitor():
        # Wait for all processes to complete
        for process in processes:
            process.wait()
        # Perform post processing operation
        post_processing()
    
    # Create an event to signal when a process has completed
    event = threading.Event()
    
    # Start the processes
    for command in commands:
        process = subprocess.Popen(command, shell=True)
        # Add the process to the list
        processes.append(process)
        # Start the event listener for the process
        thread = threading.Thread(target=event_listener, args=(process,))
        thread.start()
    
    # Start the process monitor in a separate thread
    thread = threading.Thread(target=process_monitor)
    thread.start()
    
    # Wait for all events to be set, indicating that all processes have completed
    for process in processes:
        event.wait()
