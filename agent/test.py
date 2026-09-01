from gymnasium.utils.env_checker import check_env
from environment import RingRoadEnv
env = RingRoadEnv()

check_env(env)

print("Environment passed Gymnasium checks!")