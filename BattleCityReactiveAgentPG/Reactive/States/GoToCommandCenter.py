from StateMachine.State import State
from States.AgentConsts import AgentConsts
import random


class GoToCommandCenter(State):

    def __init__(self, id):
        super().__init__(id)
        self.Reset()

    def Update(self, perception, map, agent):

        # 1. Analizar percepción básica
        agente_x = perception[AgentConsts.AGENT_X]
        agente_y = perception[AgentConsts.AGENT_Y]
        shoot = False

        # 2. Selección de objetivo dinámico (CC -> Player -> Exit/Star)
        target_x, target_y = self._select_target(perception)

        # 3. Lógica de movimiento base hacia el objetivo
        self._move_towards(agente_x, agente_y, target_x, target_y, perception)

        # 4. Ajustes por obstáculos y disparo proactivo
        shoot = self._avoid_obstacles(perception, shoot)

        # 5. Prioridades reactivas (Combate y Supervivencia)
        shoot = self._check_combat(perception, shoot)
        shoot = self._check_survival(perception, shoot)

        return self.action, shoot

    def _select_target(self, perception):
        """Selecciona el objetivo actual. Si el CC o el Player caen, vamos al Exit."""
        cc_x = perception[AgentConsts.COMMAND_CENTER_X]
        cc_y = perception[AgentConsts.COMMAND_CENTER_Y]
        pl_x = perception[AgentConsts.PLAYER_X]
        pl_y = perception[AgentConsts.PLAYER_Y]

        #si matamos al player o al CC, buscamos el exit (estrella)
        if cc_x <= 0 or cc_y <= 0 or pl_x <= 0 or pl_y <= 0:
            tx = perception[AgentConsts.EXIT_X]
            ty = perception[AgentConsts.EXIT_Y]
        else:
            # si ambos están vivos, el objetivo principal es el Centro de Mando
            tx = cc_x
            ty = cc_y
            
        return tx, ty

    def _move_towards(self, ax, ay, tx, ty, perception):
        """Define el movimiento base para acercarse a las coordenadas objetivo."""
        #si el target sigue vivo
        if tx > 0 and ty > 0:
            dist_min = 0.5
            # 1. Intentar alineación Vertical
            #si el agente esta por encima del target
            if ay > ty:
                # Solo elegimos DOWN si no hay un muro irrompible bloqueando
                if not (perception[AgentConsts.NEIGHBORHOOD_DIST_DOWN] < dist_min and perception[AgentConsts.NEIGHBORHOOD_DOWN] == AgentConsts.UNBREAKABLE):
                    self.action = AgentConsts.MOVE_DOWN
                else: # Si está bloqueado, intentamos movernos lateralmente
                    if ax < tx: #si el agente esta a la izquierda del target
                        self.action = AgentConsts.MOVE_RIGHT
                    else: #si el agente esta a la derecha del target
                        self.action = AgentConsts.MOVE_LEFT            
           #si el agente esta por debajo del target
            elif ay < ty:
                if not (perception[AgentConsts.NEIGHBORHOOD_DIST_UP] < dist_min and perception[AgentConsts.NEIGHBORHOOD_UP] == AgentConsts.UNBREAKABLE):
                    self.action = AgentConsts.MOVE_UP
                else: # Si está bloqueado, intentamos movernos lateralmente
                    if ax < tx: #si el agente esta a la izquierda del target
                        self.action = AgentConsts.MOVE_RIGHT
                    else: #si el agente esta a la derecha del target
                        self.action = AgentConsts.MOVE_LEFT        
            # 2. Si ya estamos cerca verticalmente, priorizamos horizontal
            if abs(ay - ty) < 0.5: 
                if ax < tx: #si el agente esta a la izquierda del target
                    if not (perception[AgentConsts.NEIGHBORHOOD_DIST_RIGHT] < dist_min and perception[AgentConsts.NEIGHBORHOOD_RIGHT] == AgentConsts.UNBREAKABLE):
                        self.action = AgentConsts.MOVE_RIGHT
                elif ax > tx: #si el agente esta a la derecha del target
                    if not (perception[AgentConsts.NEIGHBORHOOD_DIST_LEFT] < dist_min and perception[AgentConsts.NEIGHBORHOOD_LEFT] == AgentConsts.UNBREAKABLE):
                        self.action = AgentConsts.MOVE_LEFT

    def _avoid_obstacles(self, perception, shoot):
        """Detecta obstáculos delante y decide si disparar o esquivar."""
        dist_frontal = 0.4 # Aumentado para mayor seguridad
        
        # Mapa de sentidos: (Sentido actual): (Sensor, Distancia, Giro_Primario, Giro_Secundario)
        # El giro secundario ayuda si el primario también está bloqueado (esquinas)
       
        #diccionario que relaciona el sentido actual con el sensor, la distancia, el giro primario y el giro secundario
        # clave: sentido actual, valor: (sensor, distancia, giro primario, giro secundario) 
        # valor = tupla de 4 elementos que representan el sensor, la distancia, el giro primario y el giro secundario (inmutables)
        # sensor: sensor que detecta el obstáculo
        # distancia: distancia al obstáculo
        # giro primario: giro primario
        # giro secundario: giro secundario
        #ejemplo:
        # si el sentido actual es MOVE_DOWN, el sensor que detecta el obstáculo es NEIGHBORHOOD_DOWN
        # la distancia al obstáculo es NEIGHBORHOOD_DIST_DOWN
        # el giro primario es MOVE_RIGHT
        # el giro secundario es MOVE_LEFT
        obstacle_map = {
            AgentConsts.MOVE_DOWN: (AgentConsts.NEIGHBORHOOD_DOWN, AgentConsts.NEIGHBORHOOD_DIST_DOWN, AgentConsts.MOVE_RIGHT, AgentConsts.MOVE_LEFT),
            AgentConsts.MOVE_UP: (AgentConsts.NEIGHBORHOOD_UP, AgentConsts.NEIGHBORHOOD_DIST_UP, AgentConsts.MOVE_LEFT, AgentConsts.MOVE_RIGHT),
            AgentConsts.MOVE_RIGHT: (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.NEIGHBORHOOD_DIST_RIGHT, AgentConsts.MOVE_UP, AgentConsts.MOVE_DOWN),
            AgentConsts.MOVE_LEFT: (AgentConsts.NEIGHBORHOOD_LEFT, AgentConsts.NEIGHBORHOOD_DIST_LEFT, AgentConsts.MOVE_DOWN, AgentConsts.MOVE_UP)
        }

        #diccionario que relaciona el sentido actual con la distancia al obstáculo
        # clave: sentido actual, valor: distancia al obstáculo
        dist_sensores = {
            AgentConsts.MOVE_UP : AgentConsts.NEIGHBORHOOD_DIST_UP,
            AgentConsts.MOVE_DOWN : AgentConsts.NEIGHBORHOOD_DIST_DOWN,
            AgentConsts.MOVE_RIGHT : AgentConsts.NEIGHBORHOOD_DIST_RIGHT,
            AgentConsts.MOVE_LEFT : AgentConsts.NEIGHBORHOOD_DIST_LEFT
        }

        #si el sentido actual esta en el diccionario (agentconsts.move_down, agentconsts.move_up, agentconsts.move_right, agentconsts.move_left)
        if self.action in obstacle_map:
            #desempaquetamos la tupla
            sensor, dist_sensor, turn1, turn2 = obstacle_map[self.action]
            
            # Si hay algo demasiado cerca
            if perception[dist_sensor] < dist_frontal:
                #que tipo de obstaculo es en la direccion del sensor
                tipo = perception[sensor]
                
                # Caso A: Muro rompible -> Disparamos
                if tipo in [AgentConsts.BRICK, AgentConsts.SEMI_BREKABLE]:
                    shoot = True
                
                # Caso B: Obstáculo irrompible (u otro agente/jugador si no podemos disparar)
                elif tipo != AgentConsts.NOTHING:
                    # Intentamos Girar al Primario
                    self.action = turn1
                    #distancia al obstaculo en la direccion del giro primario
                    dist_sensor = dist_sensores[self.action]
                    #si hay algo demasiado cerca en la direccion del giro primario
                    if perception[dist_sensor] < dist_frontal:
                        #intentamos girar al secundario
                        self.action = turn2
        
        return shoot

    def _check_combat(self, perception, shoot):
        """Verifica si hay objetivos ofensivos en línea de fuego."""
        objetivos = [AgentConsts.PLAYER, AgentConsts.COMMAND_CENTER]
        direcciones = [
            (AgentConsts.NEIGHBORHOOD_DOWN, AgentConsts.MOVE_DOWN),
            (AgentConsts.NEIGHBORHOOD_UP, AgentConsts.MOVE_UP),
            (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.MOVE_RIGHT),
            (AgentConsts.NEIGHBORHOOD_LEFT, AgentConsts.MOVE_LEFT)
        ]

        for sensor, move in direcciones:
            if perception[sensor] in objetivos and perception[AgentConsts.CAN_FIRE]:
                self.action = move
                shoot = True
                break
        return shoot

    def _check_survival(self, perception, shoot):
        """Verifica amenazas inmediatas (balas) para interceptarlas."""
        direcciones = [
            (AgentConsts.NEIGHBORHOOD_DOWN, AgentConsts.MOVE_DOWN),
            (AgentConsts.NEIGHBORHOOD_UP, AgentConsts.MOVE_UP),
            (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.MOVE_RIGHT),
            (AgentConsts.NEIGHBORHOOD_LEFT, AgentConsts.MOVE_LEFT)
        ]

        for sensor, move in direcciones:
            if perception[sensor] == AgentConsts.SHELL and perception[AgentConsts.CAN_FIRE]:
                self.action = move
                shoot = True
                break
        return shoot
    
    def Transit(self,perception, map):
        return self.id
    
    def Reset(self):
        self.action = random.randint(1,4)
        self.updateTime = 0