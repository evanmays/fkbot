# FK Bot

This repo will let you programtically control dark forest from python. This is useful for making Full Knowledge Bot. A bot that can play the game.
## See if this repo works
pip install all the libraries in requirements.txt

Get my dark forest forks and run the local blockchain and local webserver so we don't spend real money. More instructions in these repos
[dark forest eth repo fork](https://github.com/evanmays/eth)
[dark forest client repo fork](https://github.com/evanmays/client)


In your python interpreter you can try the following

```
import gym, df_gym
env = gym.make('df_gym:df-v0')
env.reset() # randomly generates a new account, and funds it with ETH
env.planets
```

You should see a few planets in a list along with info on each planet.

Another thing you can try is manually playing the game
```
python -i manual_play.py
>>> g.getAllReachablePlanets()[:2] # this will give you info about 2 nearby planets, the first should be one you own, the second one you don't own. Grab the location id of the first and second planets for the next line.
>>> g.sendEnergy(<get a location id of first planet>, <get location id of second planet>, 0.8)
```

This should caputre the second planet

## AI Design Idea
Bot takes in a list of (at most 512) planets that are reachable from it's owned planets then the bot outputs two numbers. The index of the planet sending energy from and the index of the planet sending energy to. This gets passed back to the gym environment class which will send some constant amount of energy between the planets.

The most basic kind of AI we can do here is a transformer with 1 head for the index of the source planet and 1 head for the index of the destination planet.
