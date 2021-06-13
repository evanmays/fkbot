import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pfrl

MAX_PLANETS = 512
PLANET_DIMENSION = 6
FLOAT_PRECISION = np.float32

def obsToList(planet, x_center, y_center):
    arr = [
        int(planet["isOwnedByBot"]),
        (planet["position"]["x"] - x_center) / 1000.0,
        (planet["position"]["y"] - y_center) / 1000.0,
        planet["level"] / 7.0,
        min(planet["defense"] / 1000.0, 1.5),
        min(planet["energy"] / 1000.0, 1.5)
    ]
    return arr

def observationToInputTensor(observation):
    x_center = observation[0]["position"]["x"] #basically normalizing location coordinates by home planet
    y_center = observation[0]["position"]["y"]
    arr = [obsToList(planet, x_center, y_center) for planet in observation]
    t = torch.tensor(arr)
    #t = torch.unsqueeze(t, 1) # we want t to be (S, N, E) where S is the source sequence length, N is the batch size, E is the embedding dimension.
    assert t.shape[0] <= MAX_PLANETS
    assert t.shape[0] == len(observation)
    #assert t.shape[1] == 1
    assert t.shape[1] == PLANET_DIMENSION#assert t.shape[2] == PLANET_DIMENSION
    return t

def my_planets_mask(observation):
    source_planet_mask = torch.tensor([[not planet[0][0].item()] * len(observation) for planet in observation]) # source_planet_mask = torch.tensor([[not planet["isOwnedByBot"]] * len(observation) for planet in observation])
    assert source_planet_mask[0][0] == False # first tensor (should be owned by bot), all rows should be false so we can attend
    assert source_planet_mask[0][1] == False # first tensor (should be owned by bot), all rows should be false so we can attend
    assert source_planet_mask[-1][1] == True # last tensor (should be enemy/unclaimed planet), all rows should be true so we don't attend
    return source_planet_mask

def mask_selected_planet(observation, mask_index):
    arr = [[mask_index == i] * observation.shape[0] for i in range(observation.shape[0])] # arr = [[mask_index == i] * len(observation) for i, planet in enumerate(observation)]
    dest_planet_mask = torch.tensor(arr)
    return dest_planet_mask

def joint_prob_distribution(dist_a, dist_b):
    assert len(dist_a.shape) == 1, f"dist_a shape is {dist_a.shape}"
    assert len(dist_b.shape) == 1, f"dist_b shape is {dist_b.shape}"
    assert dist_a.shape == dist_b.shape, f"dist_a shape is {dist_a.shape} and dist_b shape is {dist_b.shape}"
    dist_a = torch.unsqueeze(dist_a, dim=1)
    dist_b = torch.unsqueeze(dist_b, dim=0)
    joint_dist = dist_a * dist_b
    assert joint_dist.shape == (dist_a.shape[0], dist_a.shape[0]), f"joint_dist shape is {joint_dist.shape}"
    padding_required = 512 - joint_dist.shape[0]
    joint_dist = F.pad(joint_dist, (0,padding_required, 0, padding_required))
    assert joint_dist.shape == (512, 512), f"joint_dist shape is {joint_dist.shape}"
    joint_dist_sum = torch.sum(joint_dist).item()
    assert joint_dist_sum > 0.99, f"Bad, the joint dist sums to {joint_dist_sum}"
    joint_dist = joint_dist.flatten()
    return joint_dist

class Net(nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        #self.encoder = torch.nn.MultiheadAttention(
        #    embed_dim=PLANET_DIMENSION,
        #    num_heads=1
        #)

        self.source_planet_attention_layer = torch.nn.MultiheadAttention(
            embed_dim=PLANET_DIMENSION,
            num_heads=2
        )

        self.dest_planet_attention_layer = torch.nn.MultiheadAttention(
            embed_dim=PLANET_DIMENSION,
            num_heads=2
        )

        self.source_planet_conv_layer = torch.nn.Conv1d(
            in_channels=PLANET_DIMENSION,
            out_channels=1,
            kernel_size=1
        )

        self.dest_planet_conv_layer = torch.nn.Conv1d(
            in_channels=PLANET_DIMENSION,
            out_channels=1,
            kernel_size=1
        )

        self.vantage_function = torch.nn.Linear(
            in_features=PLANET_DIMENSION * 2,
            out_features=1
        )

        self.distribution = torch.distributions.Categorical

    def forward(self, X):
        #assert len(X) > 0
        #assert len(X) <= 512
        assert X.shape[0] == 1, f"it's x.shape is {X.shape}"
        assert X.shape[1] > 0, f"it's x.shape is {X.shape}"
        assert X.shape[1] <= 512, f"it's x.shape is {X.shape}"
        assert X.shape[2] == PLANET_DIMENSION, f"it's x.shape is {X.shape}"
        X = X.permute(1, 0, 2)
        planets = X#planets = observationToInputTensor(X)

        # encode planets
        #planets = self.encoder(
        #    query=planets,
        #    key=planets,
        #    value=planets
        #)

        # Predict source planet
        source_planet_attn_mask = my_planets_mask(X)
        assert source_planet_attn_mask.shape == (len(planets), len(planets))
        attn_output, attn_output_weights = self.source_planet_attention_layer(
            query=planets,
            key=planets,
            value=planets,
            attn_mask=source_planet_attn_mask
        )
        assert attn_output.shape == (len(X), 1, PLANET_DIMENSION)
        attn_output = attn_output.permute(1, 2, 0)
        assert attn_output.shape == (1, PLANET_DIMENSION, len(X))
        score = self.source_planet_conv_layer(attn_output)
        assert score.shape == (1, 1, len(X))
        score = torch.squeeze(score)
        assert score.shape == (len(X),)
        score = torch.nan_to_num(score, nan=np.nextafter(-np.inf, 0, dtype=FLOAT_PRECISION))
        score = F.softmax(score)
        s1 = score
        source_planet_index = torch.multinomial(score, num_samples=1)
        print("src planet", source_planet_index)

        # Predict destination planet
        dest_planet_attn_mask = mask_selected_planet(X, source_planet_index)
        modulation = planets[source_planet_index]
        assert modulation.shape == (1, 1, PLANET_DIMENSION)
        assert planets.shape == (len(X), 1, PLANET_DIMENSION)
        query = planets + modulation
        attn_output, attn_output_weights = self.dest_planet_attention_layer(
            query=query,
            key=planets,
            value=planets,
            attn_mask=dest_planet_attn_mask
        )
        assert attn_output.shape == (len(X), 1, PLANET_DIMENSION)
        attn_output = attn_output.permute(1, 2, 0)
        score = self.dest_planet_conv_layer(attn_output)
        score = torch.squeeze(score)
        score = torch.nan_to_num(score, nan=np.nextafter(-np.inf, 0, dtype=FLOAT_PRECISION))
        score = F.softmax(score)
        s2 = score
        destination_planet_index = torch.multinomial(score, num_samples=1)
        print("dest planet", destination_planet_index)

        # Predict V
        selectedPlanets = torch.unsqueeze(torch.cat((planets[source_planet_index].flatten(), planets[destination_planet_index].flatten())), dim=0)
        assert selectedPlanets.shape == (1, 2 * PLANET_DIMENSION)
        v_out = F.sigmoid(self.vantage_function(selectedPlanets))

        # Predict P
        p_out = joint_prob_distribution(s1, s2)
        assert p_out.shape == (512*512,), f"actual p_out.shape is {p_out.shape}"
        p_out = torch.unsqueeze(p_out, dim=0)
        assert p_out.shape == (1, 512*512), f"actual p_out.shape is {p_out.shape}"
        return p_out, v_out

    def choose_action(self, s):
        self.eval()
        probs, _ = self.forward(s)
        probs = probs.data
        m = self.distribution(probs)
        return m.sample().numpy()[0]

    def loss_func(self, s, a, v_t):
        self.train()
        probs, values = self.forward(s)
        td = v_t - values
        c_loss = td.pow(2)

        m = self.distribution(probs)
        exp_v = m.log_prob(a) * td.detach().squeeze()
        a_loss = -exp_v
        total_loss = (c_loss + a_loss).mean()
        return total_loss
