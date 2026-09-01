import numpy as np
import random
import os
import matplotlib.pyplot as plt

from environment import RingRoadEnv


class QLearningAgent:

    def __init__(
        self,
        state_size,
        action_size,
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.05,
    ):

        self.q_table = np.zeros(
            (state_size, action_size)
        )

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        self.action_size = action_size

    def choose_action(self, state):

        #Exploration
        if random.random() < self.epsilon:

            return random.randrange(
                self.action_size
            )

        # Exploitation
        return int(
            np.argmax(
                self.q_table[state]
            )
        )

    def update(
        self,
        state,
        action,
        reward,
        next_state,
        done,
    ):

        current_q = self.q_table[
            state,
            action
        ]

        if done:

            target = reward

        else:

            next_q = np.max(
                self.q_table[next_state]
            )

            target = (
                reward
                + self.discount_factor
                * next_q
            )

        self.q_table[
            state,
            action
        ] += (
            self.learning_rate
            * (target - current_q)
        )

    def decay_epsilon(self):

        self.epsilon = max(
            self.epsilon_min,
            self.epsilon * self.epsilon_decay
        )


# STATE DISCRETIZATION

# Number of discrete levels per feature
WAITING_LEVELS = 6
OCCUPANCY_LEVELS = 4
DEMAND_LEVELS = 4
BUS_LEVELS = 4
AVAILABLE_LEVELS = 3
HOUR_LEVELS = 3

ACTION_SIZE = 4

STATE_SIZE = (
    HOUR_LEVELS
    * WAITING_LEVELS
    * OCCUPANCY_LEVELS
    * DEMAND_LEVELS
    * BUS_LEVELS
    * AVAILABLE_LEVELS
)

def discretize_state(observation):
    """
    Convert the continuous environment observation
    into a small discrete state.

    We mainly care about:

        - total waiting passengers
        - active buses
        - average occupancy
        - high-demand zones
        - time of day (to react to demand peaks)
    """

    # Extract zone information

    waiting = []

    unmet_demand = []

    for i in range(8):

        index = i * 4

        waiting.append(
            observation[index]
        )

        unmet_demand.append(
            observation[index + 3]
        )


    # Global information

    available_buses = observation[-4]

    active_buses = observation[-3]

    occupancy = observation[-2]

    hour = observation[-1]

    # Total waiting passengers
    total_waiting = sum(waiting)

    if total_waiting < 30:

        waiting_level = 0

    elif total_waiting < 70:

        waiting_level = 1

    elif total_waiting < 120:

        waiting_level = 2

    elif total_waiting < 200:

        waiting_level = 3

    elif total_waiting < 350:

        waiting_level = 4

    else:

        waiting_level = 5

  
    # Occupancy level
    if occupancy < 0.40:

        occupancy_level = 0

    elif occupancy < 0.60:

        occupancy_level = 1

    elif occupancy < 0.80:

        occupancy_level = 2

    else:

        occupancy_level = 3

    # Demand level
    high_demand_zones = sum(
        1
        for value in unmet_demand
        if value > 30
    )

    if high_demand_zones == 0:

        demand_level = 0

    elif high_demand_zones <= 2:

        demand_level = 1

    elif high_demand_zones <= 4:

        demand_level = 2

    else:

        demand_level = 3

  
    # Active bus level
    if active_buses <= 2:

        bus_level = 0

    elif active_buses <= 5:

        bus_level = 1

    elif active_buses <= 7:

        bus_level = 2

    else:

        bus_level = 3


    # Available bus level
    if available_buses <= 2:

        available_level = 0

    elif available_buses <= 5:

        available_level = 1

    else:

        available_level = 2

    # -----------------------------------------------
    # Time-of-day level (mirrors the demand multiplier)
    # -----------------------------------------------

    if 7 <= hour < 9 or 16 <= hour < 19:

        hour_level = 2

    elif 10 <= hour < 15:

        hour_level = 1

    else:

        hour_level = 0

    # Encode into one integer (mixed radix)
    state = (
        (
            (
                (
                    (hour_level * WAITING_LEVELS + waiting_level)
                    * OCCUPANCY_LEVELS + occupancy_level
                )
                * DEMAND_LEVELS + demand_level
            )
            * BUS_LEVELS + bus_level
        )
        * AVAILABLE_LEVELS + available_level
    )

    return int(state)


# TRAINING

def train():

    env = RingRoadEnv()

   
    state_size = (
        HOUR_LEVELS
        * WAITING_LEVELS
        * OCCUPANCY_LEVELS
        * DEMAND_LEVELS
        * BUS_LEVELS
        * AVAILABLE_LEVELS
    )

    action_size = (
        env.action_space.n
    )

    agent = QLearningAgent(
        state_size=state_size,
        action_size=action_size,
        epsilon_decay=0.998,
        epsilon_min=0.02,
    )

    episodes = 5000

    rewards = []

    print()
    print("=" * 60)
    print("TRANSITOPTIMIZER - Q-LEARNING")
    print("=" * 60)
    print()

    for episode in range(episodes):

        observation, info = env.reset()

        state = discretize_state(
            observation
        )

        total_reward = 0

        terminated = False
        truncated = False

        while not (terminated or truncated):

          
            # Select action
         

            action = agent.choose_action(
                state
            )

            # ---------------------------------------
            # Environment
            # ---------------------------------------

            (
                next_observation,
                reward,
                terminated,
                truncated,
                info
            ) = env.step(action)

      
            # Convert observation to state
            next_state = discretize_state(
                next_observation
            )

        
            # Learn
      
            agent.update(
                state,
                action,
                reward,
                next_state,
                terminated or truncated,
            )

            state = next_state

            total_reward += reward

     
        # Reduce exploration
    
        agent.decay_epsilon()

        rewards.append(
            total_reward
        )

        # -------------------------------------------
        # Print progress
        # -------------------------------------------

        if (episode + 1) % 100 == 0:

            average_reward = np.mean(
                rewards[-100:]
            )

            print(
                f"Episode: {episode + 1:4d} | "
                f"Reward: {total_reward:8.2f} | "
                f"Average: {average_reward:8.2f} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )

    # -----------------------------------------------
    # Save model
    # -----------------------------------------------

    np.save(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "q_table.npy",
        ),
        agent.q_table,
    )

    print()
    print("=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print()
    print("Q-table saved to:")
    print("q_table.npy")

    # -----------------------------------------------
    # Graph Output
    # -----------------------------------------------

    window = 100
    moving_avg = np.convolve(
        rewards,
        np.ones(window) / window,
        mode="valid",
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        rewards,
        alpha=0.3,
        label="Episode Reward",
    )
    plt.plot(
        range(window - 1, len(rewards)),
        moving_avg,
        label=f"{window}-Episode Moving Avg",
    )
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.title("TransitOptimizer - Q-Learning Training Progress")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    graph_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "training_progress.png",
    )
    plt.savefig(graph_path, dpi=150)
    plt.show()

    print()
    print("Graph saved to:")
    print("training_progress.png")


if __name__ == "__main__":

    train()