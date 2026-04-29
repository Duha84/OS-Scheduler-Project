# CPU Scheduling and Deadlock Simulator

**Developed by:**  
Duha Imad  
Duha Shehadeh  

---

## Overview

This project simulates how an operating system handles process scheduling, resource allocation, and deadlocks. It includes CPU and I/O bursts, shared resources, and different process states.

The scheduler uses a combination of **priority scheduling** and **Round Robin (time quantum = 10)**. It also detects deadlocks using a wait-for graph and resolves them during execution.

---

## Features

- Priority-based scheduling  
- Round Robin execution  
- CPU and I/O burst handling  
- Resource request and release (R[x], F[x])  
- Waiting queue for blocked processes  
- Deadlock detection and recovery  
- Gantt chart output  
- Waiting time and turnaround time calculation  

---

## Project Structure
os-scheduler-project/
│
├── main.py
├── TestCases.txt
└── README.md

---

## How to Run

1. Install the required dependency:


pip install networkx


2. Run the program:


python main.py


---

## Input Format (TestCases.txt)

Each line represents a process:


PID ArrivalTime Priority CPU{...} IO{...}


### Operations:
- number → execution time  
- R[x] → request resource  
- F[x] → release resource  

---

### Example

1 0 1 CPU{3,R[0],2} IO{2} CPU{2,F[0],3}
2 1 1 CPU{2,R[0],3,F[0],2}
3 2 2 CPU{5}

---

## Notes

- The output depends on the content of `TestCases.txt`  
- You can modify the test cases to try different scenarios  
- The program prints execution steps, Gantt chart, and performance metrics  
- Must keep `TestCases.txt` in the same folder as `main.py`  

---
This project demonstrates key Operating Systems concepts like scheduling, resource management, and deadlock handling in a simple simulation.
