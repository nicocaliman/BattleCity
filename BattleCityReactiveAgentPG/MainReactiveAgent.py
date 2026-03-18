import os
import sys

# Get the directory where this script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Add the subdirectories to sys.path using absolute paths
sys.path.insert(0, os.path.join(base_dir, "LGym"))
sys.path.insert(0, os.path.join(base_dir, "Agent"))
sys.path.insert(0, os.path.join(base_dir, "Reactive"))

from LGym.LGymClient import agentLoop
from Agent.BaseAgent import BaseAgent
from Reactive.ReactiveAgent import ReactiveAgent

agent = ReactiveAgent("1","Kain")
agentLoop(agent,True)