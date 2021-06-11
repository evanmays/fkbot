import gym
from gym import error, spaces, utils
from gym.utils import seeding
from .utils.gamedriver import GameDriver
from .utils.gameprivatekeys import tenAccounts
from .utils.faucet import createNewUser
from PIL import Image
from io import StringIO
import np

GAME_COORDINATE_SYSTEM_SIZE = 255 #width and height
MAX_PLANET_COUNT = 512

class DFGym(gym.Env):
    metadata = {'render.modes': ['human']}
    def __init__(self):
        self.address, self.privatekey = createNewUser()
        self.gameDriver = GameDriver(self.address, self.privatekey) # tenAccounts[8]
        planetIndexType = spaces.Discrete(MAX_PLANET_COUNT)
        self.action_space = spaces.Dict({
            'source_planet': planetIndexType,
            'destination_planet': planetIndexType,
            'percent_of_energy': spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float16)
        })
        planetType = spaces.Dict({
            'position': spaces.Box(low=0, high=GAME_COORDINATE_SYSTEM_SIZE, shape=(2,)),
            'energy': spaces.Box(low=0, high=10e3, shape=(1,)),
            'defense': spaces.Box(low=0, high=10e3, shape=(1,)),
            'level': spaces.Discrete(10)
        })
        self.observation_space = spaces.Dict({
            "planets": spaces.Tuple((planetType,) * MAX_PLANET_COUNT), #observation needs a way to mask the planets you own
            "my_planets_mask": spaces.Tuple((spaces.Discrete(2),) * MAX_PLANET_COUNT) # 1 for is my planet, 0 for not my planet
        })
        self.block_number = 0
        self.current_cumulative_reward = self.gameDriver.getPlanetCount()
        self.planetIndexToLocationId = {}
        self.planets = self.gameDriver.getAllReachablePlanets()[:MAX_PLANET_COUNT]

    def _getPlanetLocationId(self, index):
        assert index < MAX_PLANET_COUNT
        assert 0 <= index
        assert index < len(self.planets)
        return self.planets[index]

    def step(self, action):
        # do some action validation with self.my_planets_mask
        self.gameDriver.sendEnergy(
            self._getPlanetLocationId(action['source_planet']),
            self._getPlanetLocationId(action['destination_planet']),
            action['percent_of_energy']
        )
        new_cumulative_reward = self.gameDriver.getPlanetCount()

        all_reachable_planets = self.gameDriver.getAllReachablePlanets()[:MAX_PLANET_COUNT]
        self.planets = all_reachable_planets
        observation = {
            "planets": tuple(all_reachable_planets), #TODO, filter out just position, energy, defense, and level
        }
        reward = new_cumulative_reward - self.current_cumulative_reward
        self.current_cumulative_reward = new_cumulative_reward

        self.block_number = self.block_number + 1
        done = self.block_number == 100

        info = {'energy_score': self.gameDriver.getEnergyScore()} #diagnostics
        return observation, reward, done, info

    def reset(self):
        self.gameDriver.close()
        self.address, self.privatekey = createNewUser()
        self.gameDriver = GameDriver(self.address, self.privatekey) # tenAccounts[privatekey_index]
        pass

    def render(self, mode='human'):
        if mode == 'human':
            im = Image.open(BytesIO(self.gameDriver.screenshot()))
            im.show()
        else:
            super(DFGym, self).render(mode=mode) # just raise an exception

    def close(self):
        self.gameDriver.close()
        pass

    def _executejavascript(self, msg):
        """ Only use internally for debugging """
        return self.gameDriver._callJsFunc(msg)
