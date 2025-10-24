import os
import gymnasium as gym

env = gym.make("CliffWalking-v0", render_mode="human")

obs, info = env.reset()

done = False

while not done:
    # Use a fixed input for actions instead of user input
    action = 0  # Always take the left action for testing

    env.render()

    obs, reward, terminated, truncated, info = env.step(action)

    done = terminated or truncated

env.close()