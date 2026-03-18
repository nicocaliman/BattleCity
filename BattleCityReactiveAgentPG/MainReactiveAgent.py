from LGym.LGymClient import agentLoop
from Agent.BaseAgent import BaseAgent
from Reactive.ReactiveAgent import ReactiveAgent


agent = ReactiveAgent("1","Kain") #creo al agente reactivo con id 1 y nombre Kain
agentLoop(agent,True) #inicio el bucle del agente

 
