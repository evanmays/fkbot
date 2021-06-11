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
env.planets
```

You should see a few planets in a list along with info on each planet.

## AI Design Idea
Bot takes in a list of (at most 512) planets that are reachable from it's owned planets then the bot outputs two numbers. The index of the planet sending energy from and the index of the planet sending energy to. Also outputs the percent of source planets energy we are sending. This gets passed back to the environment class which will execute the command in the game.

The most basic kind of AI we can do here is a transformer with 1 head for the index of the source planet and 1 head for the index of the destination planet. Then a perceptron that takes the metadata of both planets in and outputs the percent energy to send.

