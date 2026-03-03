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
        self._move_towards(agente_x, agente_y, target_x, target_y)

        # 4. Ajustes por obstáculos y disparo proactivo
        shoot = self._avoid_obstacles(perception, shoot)

        # 5. Prioridades reactivas (Combate y Supervivencia)
        shoot = self._check_combat(perception, shoot)
        shoot = self._check_survival(perception, shoot)

        return self.action, shoot

    def _select_target(self, perception):
        """Selecciona el objetivo actual según el orden de prioridad."""
        # Prioridad 1: Centro de Mando
        tx = perception[AgentConsts.COMMAND_CENTER_X]
        ty = perception[AgentConsts.COMMAND_CENTER_Y]

        # Prioridad 2: Si el CC está destruido, buscamos al Player
        if tx <= 0 or ty <= 0:
            tx = perception[AgentConsts.PLAYER_X]
            ty = perception[AgentConsts.PLAYER_Y]

        # Prioridad 3: Si el Player también está destruido, buscamos la Estrella (Exit)
        if tx <= 0 or ty <= 0:
            tx = perception[AgentConsts.EXIT_X]
            ty = perception[AgentConsts.EXIT_Y]
            
        return tx, ty

    def _move_towards(self, ax, ay, tx, ty):
        """Define el movimiento base para acercarse a las coordenadas objetivo."""
        if tx > 0 and ty > 0:
            if ay > ty:
                self.action = AgentConsts.MOVE_DOWN
            elif ay < ty:
                self.action = AgentConsts.MOVE_UP
            
            if abs(ay - ty) < 0.5: # Alineados verticalmente
                if ax < tx:
                    self.action = AgentConsts.MOVE_RIGHT
                elif ax > tx:
                    self.action = AgentConsts.MOVE_LEFT

    def _avoid_obstacles(self, perception, shoot):
        """Detecta obstáculos delante y decide si disparar o esquivar."""
        dist_frontal = 0.5
        
        # Mapeo de sentidos y sensores
        obstacle_sensors = {
            AgentConsts.MOVE_DOWN: (AgentConsts.NEIGHBORHOOD_DOWN, AgentConsts.NEIGHBORHOOD_DIST_DOWN, AgentConsts.MOVE_RIGHT),
            AgentConsts.MOVE_UP: (AgentConsts.NEIGHBORHOOD_UP, AgentConsts.NEIGHBORHOOD_DIST_UP, AgentConsts.MOVE_LEFT),
            AgentConsts.MOVE_RIGHT: (AgentConsts.NEIGHBORHOOD_RIGHT, AgentConsts.NEIGHBORHOOD_DIST_RIGHT, AgentConsts.MOVE_UP),
            AgentConsts.MOVE_LEFT: (AgentConsts.NEIGHBORHOOD_LEFT, AgentConsts.NEIGHBORHOOD_DIST_LEFT, AgentConsts.MOVE_DOWN)
        }

        if self.action in obstacle_sensors:
            sensor, dist_sensor, turn_action = obstacle_sensors[self.action]
            if perception[dist_sensor] < dist_frontal:
                if perception[sensor] in [AgentConsts.BRICK, AgentConsts.SEMI_BREKABLE]:
                    shoot = True
                else: # Obstáculo irrompible, intentar girar
                    self.action = turn_action
        
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