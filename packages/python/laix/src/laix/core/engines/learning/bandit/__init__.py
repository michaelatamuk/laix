"""Reward mapping and the UCB bandit learner."""

from .arm import Arm
from .bandit import UCBBandit
from .rewards import reward_for_label

__all__ = ["Arm", "UCBBandit", "reward_for_label"]
