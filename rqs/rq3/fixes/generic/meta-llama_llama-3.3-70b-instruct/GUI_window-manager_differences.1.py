import gymnasium as gym
import platform

# Create the environment
env = gym.make("CliffWalking-v0", render_mode="human" if platform.system() != 'Linux' else None)

# Reset the environment
obs, info = env.reset()

done = False

while not done:
    if env.render_mode != 'none':
        env.render()  # Render the environment

    # Select an action (you can replace this with your own policy)
    action = int(input("Enter action (0=Left, 1=Down, 2=Right, 3=Up): "))

    # Take a step
    obs, reward, terminated, truncated, info = env.step(action)

    # Check if the episode is over
    done = terminated or truncated

env.close()