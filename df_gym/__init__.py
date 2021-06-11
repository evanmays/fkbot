from gym.envs.registration import register

register(
    id='df-v0',
    entry_point='df_gym.envs:DFGym',
)
