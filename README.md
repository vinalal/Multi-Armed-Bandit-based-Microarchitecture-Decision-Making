# Micro-Armed Bandit for Microarchitecture Optimization  

## Overview  
This project explores the use of lightweight reinforcement learning—specifically **Multi-Armed Bandit (MAB) algorithms**—for optimizing key microarchitectural policies.  
The primary focus is on **data prefetching** (using ChampSim) and **SMT instruction fetch policies** (using Gem5).  

Building on the referenced research paper, the project will first implement the **Discounted Upper Confidence Bound (DUCB)** algorithm for prefetching, then extend the study by benchmarking other bandit algorithms such as **Thompson Sampling, ε-Greedy, and UCB**.  
The aim is to compare their **performance, adaptability, and hardware efficiency**, and to provide practical guidelines for using reinforcement learning agents in processor design.  

## Goals  
- Implement and evaluate the Micro-Armed Bandit framework for microarchitectural decision-making.  
- Explore and benchmark multiple bandit algorithms in terms of performance (IPC), adaptability, and storage overhead.  
- Demonstrate applicability across two distinct use cases:  
  - **Data Prefetching** (ChampSim simulation).  
  - **SMT Instruction Fetch Policies** (Gem5 simulation).  

## Project Plan  

### Checkpoint 1: Setup & Initial Implementation  
- Study the paper and background material.  
- Set up the **ChampSim** environment (with Pythia if available).  
- Verify/implement baseline L2 prefetchers: Next-Line, Stream, Stride.  
- Implement the basic **Bandit agent structure (DUCB)** with defined action space, tracking tables, and step/reward logic.  

### Checkpoint 2: Prefetching Implementation & SMT Exploration  
- Finalize DUCB agent logic (warmup, normalization, latency model).  
- Tune DUCB parameters and compare against other bandit algorithms (Thompson Sampling, ε-Greedy, UCB).  
- Run performance evaluation in ChampSim and analyze prefetch quality and storage overhead.  
- Begin **SMT use case** in Gem5: set up with SMT support, integrate Hill Climbing, define fetch policy actions, and test Bandit control.  
- Summarize IPC gains and overall contributions in a report.  
