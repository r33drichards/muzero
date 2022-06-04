from absl import app
from absl import flags
from absl import logging
import os
import gym
import torch

from muzero.network import MuZeroMLPNet
from muzero.gym_env import create_classic_environment
from muzero.pipeline import load_checkpoint
from muzero.mcts import uct_search
from muzero.core import make_classic_config

FLAGS = flags.FLAGS
flags.DEFINE_string("environment_name", 'CartPole-v1', "Classic problem like 'CartPole-v1', 'LunarLander-v2'")
flags.DEFINE_integer("stack_history", 0, "Stack previous states.")

flags.DEFINE_integer('seed', 1, 'Seed the runtime.')

flags.DEFINE_string(
    'load_checkpoint_file',
    'checkpoints/classic/CartPole-v1_train_steps_61000',
    'Load the checkpoint from file.',
)
flags.DEFINE_string('record_video_dir', 'recordings/classic', 'Record play video.')


def main(argv):
    """Evaluates MuZero agent on classic control problem."""
    del argv

    device = 'cpu'
    if torch.cuda.is_available():
        device = 'cuda'
    runtime_device = torch.device(device)

    eval_env = create_classic_environment(FLAGS.environment_name, FLAGS.seed, FLAGS.stack_history)
    input_shape = eval_env.observation_space.shape
    num_actions = eval_env.action_space.n

    config = make_classic_config()

    network = MuZeroMLPNet(
        input_shape, num_actions, config.num_planes, config.value_support_size, config.reward_support_size, config.hidden_size
    )

    # Load states from checkpoint to resume training.
    if FLAGS.load_checkpoint_file is not None and os.path.isfile(FLAGS.load_checkpoint_file):
        loaded_state = load_checkpoint(FLAGS.load_checkpoint_file, 'cpu')
        network.load_state_dict(loaded_state['network'])
        logging.info(f'Loaded state from checkpoint {FLAGS.load_checkpoint_file}')

    network.eval()

    if FLAGS.record_video_dir is not None and os.path.isdir(FLAGS.record_video_dir):
        eval_env = gym.wrappers.RecordVideo(eval_env, FLAGS.record_video_dir)

    steps = 0
    returns = 0.0

    obs = eval_env.reset()
    while True:
        action, *_ = uct_search(
            state=obs,
            network=network,
            device=runtime_device,
            config=config,
            temperature=0.0,
            actions_mask=eval_env.actions_mask,
            current_player=eval_env.current_player,
            opponent_player=eval_env.opponent_player,
            best_action=True,
        )

        obs, reward, done, _ = eval_env.step(action)
        steps += 1
        returns += reward

        if done:
            break

    eval_env.close()
    logging.info(f'Episode returns: {returns}, steps: {steps}')


if __name__ == '__main__':
    app.run(main)