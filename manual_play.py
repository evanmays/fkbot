from df_gym.envs.utils.gamedriver import GameDriver
from df_gym.envs.utils.faucet import createNewUser
address, pk = createNewUser()
g = GameDriver(address, pk)
