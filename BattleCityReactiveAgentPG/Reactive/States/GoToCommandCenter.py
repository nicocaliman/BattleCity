from StateMachine.State import State
from States.AgentConsts import AgentConsts
import random


class GoToCommandCenter(State):

    def __init__(self, id):
        super().__init__(id)
        self.Reset()

    def Update(self, perception, map, agent):

        #el agente no dispara inicialmente
        shoot = False

        #coordenadas agente
        agente_x = perception[AgentConsts.AGENT_X]
        agente_y = perception[AgentConsts.AGENT_Y]

        #coordenadas centro de mando
        command_center_x = perception[AgentConsts.COMMAND_CENTER_X]
        command_center_y = perception[AgentConsts.COMMAND_CENTER_Y]

        #coordenadas jugador
        player_x = perception[AgentConsts.PLAYER_X]
        player_y = perception[AgentConsts.PLAYER_Y]

        #si el agente esta por encima de la command center y la command center no ha sido destruida (coordenadas en negativo)
        if agente_y > command_center_y and (command_center_x > 0 and command_center_y > 0):
            self.action = AgentConsts.MOVE_DOWN
        if agente_y+0.5 == command_center_y and agente_x < command_center_x:
            self.action = AgentConsts.MOVE_RIGHT
        if agente_y+0.5 == command_center_y and agente_x > command_center_x:
            self.action = AgentConsts.MOVE_LEFT

        #si el agente se mueve hacia abajo y tiene debajo un muro rompible o irrompible a menos de 2 de distancia
        if self.action == AgentConsts.MOVE_DOWN and perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN] < 0.5 and perception[AgentConsts.NEIGHBORHOOD_DOWN] in [AgentConsts.BRICK, AgentConsts.UNBREAKABLE]:
            self.action = AgentConsts.MOVE_RIGHT

        #si el agente se mueve hacia la derecha y tiene a la derecha un muro rompible o irrompible a menos de 2 de distancia
        if self.action == AgentConsts.MOVE_RIGHT and perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT] < 0.5 and perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.BRICK:
            self.action = AgentConsts.MOVE_RIGHT
            shoot = True 
        #si el agente se mueve hacia la derecha y esta en la esquina derecha inferior
        if self.action == AgentConsts.MOVE_RIGHT and perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT] < 0.5 and (perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.UNBREAKABLE and perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.UNBREAKABLE):
            self.action = AgentConsts.MOVE_UP

        #si el agente se mueve hacia arriba y encima hay un muro rompible o irrompible y a la derecha hay un muro irrompible
        if self.action == AgentConsts.MOVE_UP and perception[AgentConsts.NEIGHBORHOOD_DIST_UP] < 0.5 and (perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.UNBREAKABLE or perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.BRICK) and perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.UNBREAKABLE:
            self.action = AgentConsts.MOVE_LEFT

        # --- PRIORIDADES Y REACCIONES ---
        
        # 1. OBJETIVOS OFENSIVOS (Atacar si están alineados)
        objetivos_ataque = [AgentConsts.PLAYER, AgentConsts.COMMAND_CENTER]
        
        if perception[AgentConsts.NEIGHBORHOOD_DOWN] in objetivos_ataque and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_DOWN
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_RIGHT] in objetivos_ataque and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_RIGHT
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_UP] in objetivos_ataque and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_UP
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_LEFT] in objetivos_ataque and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_LEFT
            shoot = True

        # 2. SUPERVIVENCIA (Máxima prioridad: interceptar balas)
        if perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.SHELL and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_DOWN
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.SHELL and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_RIGHT
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.SHELL and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_UP
            shoot = True
        elif perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.SHELL and perception[AgentConsts.CAN_FIRE]:
            self.action = AgentConsts.MOVE_LEFT
            shoot = True

        return self.action,shoot
    
    def Transit(self,perception, map):
        return self.id
    
    def Reset(self):
        self.action = random.randint(1,4)
        self.updateTime = 0