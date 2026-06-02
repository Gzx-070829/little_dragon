import json
import os
import random
import time
from ast import literal_eval


class QLearningAgent:
    """轻量表格 Q-learning 智能体，用离散游戏状态选择跳跃/下蹲动作。"""

    ACTIONS = (0, 1, 2)  # 0=不操作, 1=跳跃, 2=下蹲

    def __init__(
        self,
        learning_rate=0.12,
        discount_factor=0.92,
        epsilon=0.35,
        min_epsilon=0.05,
        epsilon_decay=0.995,
    ):
        self.q_table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.min_epsilon = min_epsilon
        self.epsilon_decay = epsilon_decay
        self.training_episodes = 0
        self.best_avoided = 0
        self.best_score = 0
        self.last_train_time = None
        self.last_session = {}

    @staticmethod
    def state_to_key(state):
        return ','.join(str(int(value)) for value in state)

    @staticmethod
    def key_to_state(key):
        if isinstance(key, str) and ',' in key:
            return tuple(int(part) for part in key.split(','))
        return tuple(literal_eval(key))

    def _ensure_state(self, state):
        key = self.state_to_key(state)
        if key not in self.q_table:
            self.q_table[key] = [0.0, 0.0, 0.0]
        return key

    def get_q_values(self, state):
        key = self._ensure_state(state)
        return self.q_table[key]

    def choose_action(self, state, training=True, epsilon_override=None):
        epsilon = self.epsilon if epsilon_override is None else epsilon_override
        if training and random.random() < epsilon:
            return random.choice(self.ACTIONS)

        q_values = self.get_q_values(state)
        max_q = max(q_values)
        best_actions = [index for index, value in enumerate(q_values) if value == max_q]
        return random.choice(best_actions)

    def update_q_value(self, state, action, reward, next_state, done=False):
        q_values = self.get_q_values(state)
        current_q = q_values[action]
        next_best = 0.0 if done else max(self.get_q_values(next_state))
        target = reward + self.discount_factor * next_best
        q_values[action] = current_q + self.learning_rate * (target - current_q)

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def _metadata(self, session_metadata=None):
        metadata = {
            'training_episodes': int(self.training_episodes),
            'best_avoided': int(self.best_avoided),
            'best_score': int(self.best_score),
            'epsilon': float(self.epsilon),
            'alpha': float(self.learning_rate),
            'gamma': float(self.discount_factor),
            'min_epsilon': float(self.min_epsilon),
            'epsilon_decay': float(self.epsilon_decay),
            'last_train_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if session_metadata:
            metadata.update(session_metadata)
            self.last_session = dict(session_metadata)
        self.last_train_time = metadata['last_train_time']
        return metadata

    def save(self, path, session_metadata=None):
        metadata = self._metadata(session_metadata)
        data = {
            'q_table': self.q_table,
            'metadata': metadata,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path):
        if not os.path.exists(path):
            self.q_table = {}
            print('未找到历史训练数据，已初始化新Q表')
            return False

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        raw_table = data.get('q_table', data)
        self.q_table = {
            self.state_to_key(self.key_to_state(key)): [float(v) for v in values]
            for key, values in raw_table.items()
        }

        metadata = data.get('metadata', {})
        self.learning_rate = float(metadata.get('alpha', data.get('learning_rate', self.learning_rate)))
        self.discount_factor = float(metadata.get('gamma', data.get('discount_factor', self.discount_factor)))
        self.epsilon = float(metadata.get('epsilon', data.get('epsilon', self.epsilon)))
        self.min_epsilon = float(metadata.get('min_epsilon', data.get('min_epsilon', self.min_epsilon)))
        self.epsilon_decay = float(metadata.get('epsilon_decay', data.get('epsilon_decay', self.epsilon_decay)))
        self.training_episodes = int(metadata.get('training_episodes', data.get('training_episodes', 0)))
        self.best_avoided = int(metadata.get('best_avoided', data.get('best_avoided', 0)))
        self.best_score = int(metadata.get('best_score', data.get('best_score', 0)))
        self.last_train_time = metadata.get('last_train_time')
        self.last_session = {
            key: metadata[key]
            for key in ('session_episodes', 'session_best_avoided', 'session_best_score', 'session_average_score', 'session_average_avoided')
            if key in metadata
        }
        print('已加载历史训练数据')
        return True
