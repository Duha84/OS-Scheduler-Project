import re
from asyncio import wait_for
from collections import defaultdict
from itertools import cycle
from xml.etree.ElementTree import QName
import networkx as nx
from copy import deepcopy

file_path = "TestCases.txt"  # Replace with the actual path to your file
resources = {
    "R[0]": None,  # None means the resource is free
    "R[1]": None,
    "R[2]": None,
    "R[3]": None,
    "R[4]": None,
}

class Process:
    def __init__(self, pid, arr_time, priority, bursts):
        self.pid = pid
        self.arr_time = arr_time
        self.priority = priority
        self.bursts = bursts  # List of Burst objects


class Burst:
    def __init__(self, burst_type, operations):
        self.burst_type = burst_type
        self.operations = operations  # List of Operation objects


class Operation:
    def __init__(self, action, value):
        self.action = action
        self.value = value

# for the reading file

# Queues for different process states
cpu_ready = []  # Ready queue for CPU-bound processes
cpu_waiting = []  # Waiting queue for resource requests
io_running = []  # I/O-bound processes
terminated = []  # Completed processes
cpu_running = None  # Currently running process on CPU
gantt_chart = []  # For visualizing the scheduling
quantum = 10   # Time quantum for round-robin scheduling
wait_for_graph = defaultdict(list)
deadlock_time=[]
def get_operation(word):
    """Determine the action and value based on the word."""
    word = word.strip()
    if not word:  # Skip empty strings
        raise ValueError("Empty operation encountered")

    if re.match(r"^\d+$", word):  # Pure number (execution)
        return Operation("exe", int(word))

    elif re.match(r"^R\[(\d+)\]$", word):  # Request format
        return Operation("req", int(re.findall(r"\d+", word)[0]))

    elif re.match(r"^F\[(\d+)\]$", word):  # Release format
        return Operation("release", int(re.findall(r"\d+", word)[0]))

    else:
        raise ValueError(f"Invalid operation: '{word}'")


def read_from_file(file_path):
    """Parse the file and return a list of Process objects."""
    processes = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # print(f"Reading line: {line.strip()}")  # Debugging
                parts = line.strip().split()

                # Parse basic process information
                pid = int(parts[0])
                arr_time = int(parts[1])
                priority = int(parts[2])

                # Parse bursts
                bursts = []

                for i in range(3, len(parts)):
                    if '{' in parts[i]:
                        match = parts[i].split('{')
                        burst_type = match[0].strip()
                        seq = match[1].strip('}')
                        op = seq.split(',')

                        # Parse operations
                        operations = []
                        for operation in op:
                            operation = operation.strip()
                            if operation:  # Skip empty operations
                                operations.append(get_operation(operation))

                        bursts.append(Burst(burst_type, operations))


                # Create and append the Process object
                processes.append(Process(pid, arr_time, priority, bursts))
    except FileNotFoundError:

        print(f"Error: File not found at {file_path}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return processes



def add_to_Q(process, queue, arrival_time):

        process.arr_time = arrival_time
        # print(f"Before adding: {[p.pid for p in queue]}")  # Debugging
        queue.append(process)
        queue.sort(key=lambda p: p.priority)
        # print(f"After adding: {[p.pid for p in queue]}")  # Debugging
        # print(f"Process {process.pid} added to queue at time {arrival_time}.")




def cpu_scheduling(processes):
    actual_time = 0  # Current time in the simulation
    global cpu_running , quantum

    # Main loop to simulate CPU scheduling
    while processes or cpu_ready or cpu_waiting or io_running or cpu_running:

        '''
        print(f"\nTime {actual_time}: Starting simulation step")
        print(f"Processes: {[p.pid for p in processes]}")
        print(f"CPU Ready Queue: {[p.pid for p in cpu_ready]}")
        print(f"CPU Running: {cpu_running.pid if cpu_running else None}")
        print(f"IO Running: {[p.pid for p in io_running]}")
        print(f"Terminated: {[p.pid for p in terminated]}")
        '''

        # Handle arriving processes
        for process in list(processes):
            if process.arr_time == actual_time:
                print(f"Process {process.pid} arrived at time {actual_time}.")

                add_to_Q(process, cpu_ready, actual_time)
                processes.remove(process)

        # Select process for CPU execution
        if not cpu_running and cpu_ready:
          cpu_running = cpu_ready.pop(0)  # Simply pick the first process in the ready queue

          print(f"CPU starts running process {cpu_running.pid}")


        # Execute the current process
        if cpu_running:

            # no bursts remaining terminate
            if not cpu_running.bursts:
                print(f"Process {cpu_running.pid} has no more bursts. Terminating.")
                terminated.append(cpu_running)
                cpu_running = None
                continue
            # no operation left to do move to the next burst
            if not cpu_running.bursts[0].operations:
                print(f"Process {cpu_running.pid} burst completed. Moving to next burst.")
                cpu_running.bursts.pop(0)

                if not cpu_running.bursts:
                    print(f"Process {cpu_running.pid} has no more bursts. Terminating.")
                    terminated.append(cpu_running)
                    cpu_running = None
                    #cpu_ready[:] = [p for p in cpu_ready if p.pid != terminated[-1].pid]

                    continue

            # Safe to access first operation now
            first_operation = cpu_running.bursts[0].operations[0]

            # Check if priority of the running process matches any process in the ready queue
            same_priority_exists = any(p.priority == cpu_running.priority for p in cpu_ready)

            if first_operation.action == "exe":  # Execute burst
                first_operation.value -= 1
                gantt_chart.append(cpu_running.pid)  # Log current process in the Gantt Chart
                # print(f"Executing process {cpu_running.pid}, remaining burst: {first_operation.value}")

                if same_priority_exists:
                    # print("Same priority exists")
                    quantum -= 1


                if first_operation.value == 0:  # Burst complete
                    print(f"Process {cpu_running.pid} burst complete.")
                    cpu_running.bursts[0].operations.pop(0)

                    if not cpu_running.bursts[0].operations:
                        cpu_running.bursts.pop(0)

                    if cpu_running.bursts and cpu_running.bursts[0].burst_type == "IO":
                        print(f"Process {cpu_running.pid} moving to IO burst.")
                        io_running.append(cpu_running)
                        cpu_running = None


                    elif not cpu_running.bursts:
                        print(f"Process {cpu_running.pid} has no more bursts. Terminating.")
                        terminated.append(cpu_running)
                        cpu_running = None


                if same_priority_exists and quantum == 0 and cpu_running:  # Quantum expired
                    #print(f"Quantum expired for process {cpu_running.pid}. Preempting.")

                    add_to_Q(cpu_running, cpu_ready, actual_time)
                    cpu_running = None
                    quantum = 10

            else:  # Handle resource operations
                # print("Before resource handling:")
                # for r, status in resources.items():
                    # print(f"Resource {r}: {'Available' if status is None else 'Unavailable'}")

                is_done = handling_Resource(first_operation, cpu_running, cpu_waiting,
                                            actual_time, processes)

                if is_done:
                    cpu_running = None

                    if cpu_ready:
                      cpu_running=cpu_ready.pop(0)

                else:

                    cpu_running.bursts[0].operations.pop(0)
                #
                # print("After resource handling:")
                # for r, status in resources.items():
                #     print(f"Resource {r}: {'Available' if status is None else 'Unavailable'}")

        # Handle IO bursts
        handle_io_bursts(actual_time)

        # Log idle time in the Gantt Chart
        if not cpu_running and not cpu_ready:
            gantt_chart.append("idle")

        # Increment time
        actual_time += 1

        # Break if all processes are done
        if not processes and not cpu_ready and not io_running and not cpu_running:
            print("All processes complete. Exiting simulation.")
            #return gantt_chart
           # break

    # # Print Gantt Chart
    # print("\nGantt Chart:")
    # for time, pid in enumerate(gantt_chart):
    #     print(f"Time {time}: Process {pid}")
    return gantt_chart




def handling_Resource(operation, process, waiting, actual_time,processes):

    global cpu_running  # Declare cpu_running as global to modify it directly

    index = f"R[{operation.value}]"  # The specific resource (e.g., "R[1]")

    # Handle resource request
    if operation.action == "req":
        if resources[index] is None or resources[index] == process.pid:  # Resource is free
            resources[index] = process.pid  # Allocate resource to the process
            print(f"Process {process.pid} has acquired {index}.")


        else:  # Resource is held by another process

            holder = resources[index]
            print(f"Process {process.pid} is waiting for {index}, held by Process {holder}.")
            waiting.append(process)  # Add process to waiting queue

            if cpu_running:
                cpu_running = None

            print(f"WAITING Q: {[p.pid for p in waiting]}")
            wait_for_graph[process.pid].append(holder)  # Add edge in the wait-for graph

            #debugging
            print("\nCurrent Wait-for Graph:")
            for process, dependencies in wait_for_graph.items():
                print(f"Process {process} is waiting for: {dependencies}")


            loop=detect_cycle(wait_for_graph)
            print(loop)

            if loop:
                 handle_deadlock(waiting, processes, actual_time)
                 return True
            else:
                return True #cpu should be freed from this process

    # Handle resource release
    elif operation.action == "release":
        if resources[index] == process.pid:  # If the process holds the resource
            resources[index] = None  # Free the resource
            print(f"Process {process.pid} has released {index}.")
            # Remove edges related to the resource
            for pid in wait_for_graph:
                if process.pid in wait_for_graph[pid]:
                    wait_for_graph[pid].remove(process.pid)
                    print(f"Removed edge: Process {pid} → Process {process.pid}")


        # Check waiting processes for this resource
        for waiting_process in list(waiting):
            print("علاوي ")
            if waiting_process.bursts[0].operations[0].value == operation.value:
                waiting.remove(waiting_process)  # Remove from waiting queue
                resources[index] = waiting_process.pid  # Allocate resource
                add_to_Q(waiting_process, cpu_ready, actual_time)
                print(f"Process {waiting_process.pid} has acquired {index}.")
                break

    # Check if the process has no more operations or bursts
    if not process.bursts or not process.bursts[0].operations:
        print(f"Process {process.pid} has completed all bursts. Terminating.")
        return True  # Process is done

    return False  # Process is not done




def handle_io_bursts(actual_time):
    """Simulate IO bursts for processes."""
    for process in list(io_running):
        burst = process.bursts[0]
        if burst.operations[0].value == 0:
            print(f"Process {process.pid} finished IO burst.")
            burst.operations.pop(0)
            process.bursts.pop(0)
            io_running.remove(process)
            if process.bursts:  # Only re-add to ready if more bursts remain

                add_to_Q(process, cpu_ready,actual_time)
            else:
                print(f"Process {process.pid} has completed all bursts. Terminating.")
        else:
            burst.operations[0].value -= 1  # Decrement IO burst time

def print_processes(processes):
    """Print the processes in the desired format."""
    for process in processes:
        print(f"Process ID: {process.pid}")
        print(f"Arrival Time: {process.arr_time}")
        print(f"Priority: {process.priority}")

        for idx, burst in enumerate(process.bursts, start=1):
            print(f"  Burst {idx} ({burst.burst_type}):")
            for operation in burst.operations:
                print(f"    - {operation.action}: {operation.value}")
        print()  # Blank line between processes


########################################################################################################################################################

#def handle_deadlock:
def handle_deadlock( waiting, processes, actual_time):
    """
    Handles deadlocks by terminating the process with the minimum PID in the cycle.
    """
    global cpu_running
    global deadlock_time

     # Store the time of the deadlock
    while True:
        cycle = detect_cycle(wait_for_graph)

        if not cycle:
            print("No deadlock detected.")
            break
        deadlock_time.append(actual_time - 3)
        print(f"Deadlock detected! Cycle: {cycle}")

        # Find the process with the maximum PID in the cycle (as per the original logic)
        lowest_pid_process = max(cycle)
        print(f"Terminating process {lowest_pid_process} to resolve deadlock.")

        # Release resources held by the process
        for resource, holder in list(resources.items()):
            if holder == lowest_pid_process:
                resources[resource] = None
                print(f"Released {resource} from Process {lowest_pid_process}.")

                # Check if any process is waiting for this resource
                for waiting_process in list(waiting):
                    if waiting_process.bursts[0].operations[0].value == int(resource[2]):  # Match resource number
                        waiting.remove(waiting_process)  # Remove from waiting queue
                        resources[resource] = waiting_process.pid  # Allocate resource
                        add_to_Q(waiting_process, cpu_ready, actual_time)  # Move to ready queue
                        print(f"Process {waiting_process.pid} has acquired {resource} and moved to ready queue.")

        # Remove the process from the wait-for graph
        wait_for_graph.pop(lowest_pid_process, None)
        for pid, neighbors in wait_for_graph.items():
            if lowest_pid_process in neighbors:
                neighbors.remove(lowest_pid_process)
                print(f"Removed edge: Process {pid} → Process {lowest_pid_process}")

        # Remove from CPU ready queue
        cpu_ready[:] = [p for p in cpu_ready if p.pid != lowest_pid_process]

        # Remove from waiting queue
        waiting[:] = [p for p in waiting if p.pid != lowest_pid_process]

        # Remove from CPU if it's running
        if cpu_running and cpu_running.pid == lowest_pid_process:
            cpu_running = None

        # Remove from processes list and re-add with new arrival time
        cpy = read_from_file(file_path)
        for process in cpy:
            if process.pid == lowest_pid_process:
                process.arr_time = actual_time + 1
                process.priority = 6
                processes.append(process)
                # print(f"Process {lowest_pid_process} has been re-added with new arrival time {process.arr_time}.")
                # print_processes(processes)
                break

    return cpu_running

def detect_cycle(wait_for_graph):

    G = nx.DiGraph()  # Create a directed graph

    # Add edges from the wait-for graph
    for process, dependencies in wait_for_graph.items():
        for dependent in dependencies:
            G.add_edge(process, dependent)

    try:
        # Use networkx's built-in function to find a cycle
        cycle = nx.find_cycle(G, orientation='original')
        return [edge[0] for edge in cycle]  # Return just the nodes in the cycle
    except nx.NetworkXNoCycle:
        return None  # No cycle found


def calculate_metrics(processes):

    process_metrics = {}
    total_waiting_time = 0
    total_turnaround_time = 0
    num_processes = len(processes)

    for process in processes:
        pid = process.pid

        # Find termination time from Gantt chart
        termination_time = len(gantt_chart) - 1 - gantt_chart[::-1].index(pid)

        # Calculate total burst time (sum of all 'exe' operations)
        total_burst_time = sum(op.value for burst in process.bursts for op in burst.operations if op.action == "exe")

        # Calculate turnaround time
        turnaround_time = termination_time - process.arr_time + 1

        # Calculate waiting time
        waiting_time = turnaround_time - total_burst_time

        # Store metrics
        process_metrics[pid] = {
            "Turnaround Time": turnaround_time,
            "Waiting Time": waiting_time,
        }

        # Update totals
        total_waiting_time += waiting_time
        total_turnaround_time += turnaround_time

    # Print results
    print("\nFinal Metrics:")
    for pid, metrics in process_metrics.items():
        print(f"Process {pid}:")
        print(f"  Turnaround Time: {metrics['Turnaround Time']}")
        print(f"  Waiting Time: {metrics['Waiting Time']}")

    # Calculate averages
    average_waiting_time = total_waiting_time / num_processes
    average_turnaround_time = total_turnaround_time / num_processes

    # Print averages
    print("\nAverage Metrics:")
    print(f"  Average Waiting Time: {average_waiting_time:.2f}")
    print(f"  Average Turnaround Time: {average_turnaround_time:.2f}")

def print_formatted_gantt_chart(gantt_chart):
    print("\nGantt Chart:")
    print("=" * 50)

    # Initialize variables to track the process and its execution times
    current_process = gantt_chart[0]
    start_time = 0

    for time in range(1, len(gantt_chart)):
        # Check if the process changes
        if gantt_chart[time] != current_process:
            # Print the process execution details
            print(f"Process {current_process} executed from time {start_time} to {time}")

            if start_time in deadlock_time:
                print(f"Deadlock detected at time {start_time}!")

            # Update to the next process
            current_process = gantt_chart[time]
            start_time = time

    # Print the last process execution
    print(f"Process {current_process} executed from time {start_time} to {len(gantt_chart)}")

    # Print any remaining deadlock times after the last process
    for dt in deadlock_time:
        if dt >= len(gantt_chart):
            print(f"Deadlock detected at time {dt}!")
    print("=" * 50)


def main():

    global gantt_chart
    # global deadlock_time
    # File path to the input file

    # Read and process the file
    processes = read_from_file(file_path)
    print_processes(processes)
    gantt_chart=cpu_scheduling(processes)
    # print("Gantt Chart:", gantt_chart)

    print_formatted_gantt_chart(gantt_chart)
    cpy=read_from_file(file_path)
    calculate_metrics(cpy)
    print(deadlock_time)


if __name__ == "__main__":

    main()

