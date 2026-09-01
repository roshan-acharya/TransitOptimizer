from environment import RingRoadEnv


env = RingRoadEnv()

observation, info = env.reset(seed=42)

print("Observation shape:")
print(observation.shape)

print("\nAction space:")
print(env.action_space)

print("\nObservation space:")
print(env.observation_space)


for step in range(20):

  
    action = env.action_space.sample()

    (
        observation,
        reward,
        terminated,
        truncated,
        info,
    ) = env.step(action)

    print(
        f"Step {step:02d} | "
        f"Action={action} | "
        f"Waiting={info['total_waiting']:4d} | "
        f"Buses={info['active_buses']:2d} | "
        f"Occupancy={info['occupancy'] * 100:5.1f}% | "
        f"Profit=Rs.{info['profit']:8.0f} | "
        f"Reward={reward:8.2f}"
    )

    if terminated or truncated:
        break


env.close()