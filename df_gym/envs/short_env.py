import gym
from gym import error, spaces, utils
from gym.utils import seeding
from .utils.gamedriver import GameDriver
from .utils.gameprivatekeys import tenAccounts
from .utils.faucet import createNewUser
from PIL import Image
from io import StringIO
import np
import time

GAME_COORDINATE_SYSTEM_SIZE = 255 #width and height
MAX_PLANET_COUNT = 512

def action_space_to_planet_list_space(action_space_index):
    source_planet_index = action_space_index // MAX_PLANET_COUNT
    dest_planet_index = action_space_index % MAX_PLANET_COUNT
    return source_planet_index, dest_planet_index

def planet_list_space_to_action_space(source_planet_index, dest_planet_index):
    """
    source_planet_index is the row in the probability matrix
    dest_planet_index is the column in the probability matrix
    """
    action_space_index = source_planet_index * MAX_PLANET_COUNT + dest_planet_index
    return action_space_index

class DFGym(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self):
        self.gameDriver = None#self._init()
        planetIndexType = spaces.Discrete(MAX_PLANET_COUNT)
        self.action_space = spaces.Discrete(MAX_PLANET_COUNT * MAX_PLANET_COUNT)
        planetType = spaces.Dict({
            'position': spaces.Box(low=0, high=GAME_COORDINATE_SYSTEM_SIZE, shape=(2,)),
            'energy': spaces.Box(low=0, high=10e3, shape=(1,)),
            'defense': spaces.Box(low=0, high=10e3, shape=(1,)),
            'level': spaces.Discrete(10),
        })
        self.observation_space = spaces.Dict({
            "planets": spaces.Tuple((planetType,) * MAX_PLANET_COUNT), #observation needs a way to mask the planets you own
        })

    def _getPlanetLocationId(self, index):
        assert index < MAX_PLANET_COUNT
        assert 0 <= index
        assert index < len(self.planets)
        return self.planets[index]['locationId']

    def _init(self):
        self.address, self.privatekey = createNewUser()
        self.gameDriver = GameDriver(self.address, self.privatekey)
        self.block_number = 0
        self.current_cumulative_reward = 1
        self.planetIndexToLocationId = {}
        self.planets = self.gameDriver.getAllReachablePlanets()[:MAX_PLANET_COUNT]

    def step(self, action):
        # do some action validation with self.my_planets_mask
        #self.gameDriver.sendEnergy(
        #    self._getPlanetLocationId(action['source_planet']),
        #    self._getPlanetLocationId(action['destination_planet']),
        #    action['percent_of_energy']
        #)
        src_planet_idx, dst_planet_idx = action_space_to_planet_list_space(action)
        self.gameDriver.sendEnergy(
            self._getPlanetLocationId(src_planet_idx),
            self._getPlanetLocationId(dst_planet_idx),
            0.5
        )

        time.sleep(5)

        new_cumulative_reward = self.gameDriver.getPlanetCount()
        assert new_cumulative_reward

        all_reachable_planets = self.gameDriver.getAllReachablePlanets()[:MAX_PLANET_COUNT]
        self.planets = all_reachable_planets
        observation = {
            "planets": tuple(all_reachable_planets),
        }
        reward = new_cumulative_reward - self.current_cumulative_reward
        self.current_cumulative_reward = new_cumulative_reward

        self.block_number = self.block_number + 1
        done = self.block_number == 100

        info = {'energy_score': self.gameDriver.getEnergyScore()}
        assert observation and observation["planets"] and observation["planets"][0]
        assert reward is not None
        assert info
        return observation, reward, done, info

    def reset(self):
        if self.gameDriver:
            self.gameDriver.close()
        self._init()
        return {"planets": tuple(self.planets)}

    def render(self, mode='human'):
        if mode == 'human':
            im = Image.open(BytesIO(self.gameDriver.screenshot()))
            im.show()
        else:
            super(DFGym, self).render(mode=mode) # just raise an exception

    def close(self):
        self.gameDriver.close()

    def _executejavascript(self, msg):
        """ Only use internally for debugging """
        return self.gameDriver._callJsFunc(msg)
