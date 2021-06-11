const disablePopups = (address) => {
  localStorage.setItem(`wallet-enabled-${address.toLowerCase()}`, (Date.now() + 24 * 60 * 60 * 1000).toString());
}


//returns tuples of [planet,distance]
function distance(from, to) {
  let fromloc = from.location;
  let toloc = to.location;
  return Math.sqrt((fromloc.coords.x - toloc.coords.x) ** 2 + (fromloc.coords.y - toloc.coords.y) ** 2);
}

function getArrivalsForPlanet(planetId) {
  return df.getAllVoyages().filter(arrival => arrival.toPlanet === planetId).filter(p => p.arrivalTime > Date.now() / 1000);
}

const stopExplore = () => {
  df.stopExplore()
}

const mapPlanetToObservable = (planet) => ({
  position: planet.location.coords,
  energy: planet.energy ,
  defense: planet.defense,
  level: planet.planetLevel,
  isOwnedByBot: planet.owner === df.account
})
function getAllReachablePlanets() {
  const reachablePlanets = {};
  // We want our own planets to be first. This makes debugging easier. The neural net shouldn't know order of it's input anyway.
  for (let sourcePlanet of df.getMyPlanets()) {
    reachablePlanets[sourcePlanet.locationId] = mapPlanetToObservable(sourcePlanet)
  }
  for (let sourcePlanet of df.getMyPlanets()) {
    for (let reachablePlanet of df.getPlanetsInRange(sourcePlanet.locationId, 99)) {
      if (reachablePlanet.locationId in reachablePlanets) {
        continue;
      }
      reachablePlanets[reachablePlanet.locationId] = mapPlanetToObservable(reachablePlanet);
    }
  }
  return Object.values(reachablePlanets);
}

function capturePlanets(fromId, minCaptureLevel, maxDistributeEnergyPercent) {
  const planet = df.getPlanetWithId(fromId);
  const from = df.getPlanetWithId(fromId);

  // Rejected if has pending outbound moves
  const unconfirmed = df.getUnconfirmedMoves().filter(move => move.from === fromId)
  if (unconfirmed.length !== 0) {
    return;
  }

  const candidates_ = df.getPlanetsInRange(fromId, maxDistributeEnergyPercent)
    .filter(p => (
      p.owner !== df.account &&
      p.owner === "0x0000000000000000000000000000000000000000" &&
      p.planetLevel >= minCaptureLevel
    ))
    .map(to => {
      return [to, distance(from, to)]
    })
    .sort((a, b) => a[1] - b[1]);

  let i = 0;
  const energyBudget = Math.floor((maxDistributeEnergyPercent / 100) * planet.energy);

  let energySpent = 0;
  let moves = 0;
  while (energyBudget - energySpent > 0 && i < candidates_.length) {

    const energyLeft = energyBudget - energySpent;

    // Remember its a tuple of candidates and their distance
    const candidate = candidates_[i++][0];

    // Rejected if has unconfirmed pending arrivals
    const unconfirmed = df.getUnconfirmedMoves().filter(move => move.to === candidate.locationId)
    if (unconfirmed.length !== 0) {
      continue;
    }

    // Rejected if has pending arrivals
    const arrivals = getArrivalsForPlanet(candidate.locationId);
    if (arrivals.length !== 0) {
      continue;
    }

    const energyArriving = (candidate.energyCap * 0.15) + (candidate.energy * (candidate.defense / 100));
    // needs to be a whole number for the contract
    const energyNeeded = Math.ceil(df.getEnergyNeededForMove(fromId, candidate.locationId, energyArriving));
    if (energyLeft - energyNeeded < 0) {
      continue;
    }

    move(fromId, candidate.locationId, energyNeeded, 0);
    energySpent += energyNeeded;
    moves += 1;
  }

  return moves;
}


queuedmove = await import("https://plugins.zkga.me/utils/queued-move.js")
move = queuedmove.move

const randomove = () => {
  /*import {
    move
  } from 'https://plugins.zkga.me/utils/queued-move.js'; */
  console.log(df)
  console.log("it works")
  for (let planet of df.getMyPlanets()) {
    setTimeout(() => {
      capturePlanets(
        planet.locationId,
        0,
        99,
      );
    }, 0);
  }
  //move(fromId, candidate.locationId, energyNeeded, 0);
}

const sendEnergy = (fromPlanetId, toPlanetId, percentAmount) => {
  const energy = Math.round(df.getPlanetWithId(fromPlanetId).energy * percentAmount)
  move(fromPlanetId, toPlanetId, energy, 0);
}
