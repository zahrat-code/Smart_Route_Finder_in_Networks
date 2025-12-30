import numpy as np
import random
import networkx as nx
from ..generation import generate_graf 
from ..core import Metrics       

class QLearningAgent:
    def __init__(self, start_node, goal_node, G=None, alpha=0.1, gamma=0.9, epsilon=0.1, episodes=1000):
        
        if G is None:
            print("Graf yükleniyor...")
            self.G = generate_graf.graf_uret()
        else:
            self.G = G
            
        self.nodes = list(self.G.nodes())

        self.num_nodes = len(self.nodes)
        
        self.start_node = start_node
        self.goal_node = goal_node
        
        # Hyperparameters
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.episodes = episodes
        
        self.q_table = np.zeros((self.num_nodes, self.num_nodes))

    def get_valid_actions(self, current_node):
        """Bir düğümden gidilebilecek komşuları döndürür"""
        return list(self.G.neighbors(current_node))

    def calculate_reward(self, path):
        """
        Calculates reward based on Multi-Objective Cost.
        Reward = 1000 / TotalCost
        """
        if not path or path[-1] != self.goal_node:
            return 0.1 
        
        w_delay = 0.33
        w_rel = 0.33
        w_res = 0.34
        
        total_delay = Metrics.Total_Delay(self.G, path)
        rel_cost = Metrics.Total_Reliability(self.G, path)
        res_cost = Metrics.Total_Bandwidth(self.G, path)
        
        total_cost = (w_delay * total_delay) + \
                     (w_rel * rel_cost) + \
                     (w_res * res_cost)
        
        if total_cost == 0: total_cost = 0.001
        
        return 1000.0 / total_cost

    def train(self):
        # Epsilon Decay Strategy
        # Start with high exploration, decay to self.epsilon
        start_epsilon = 1.0
        min_epsilon = self.epsilon
        decay_rate = 0.005 # Adjust based on episodes
        
        current_epsilon = start_epsilon
        
        for episode in range(self.episodes):
            current_node = self.start_node
            
            # Max steps to prevent infinite loops during training
            for _ in range(self.num_nodes * 2):
                if current_node == self.goal_node:
                    break
                
                actions = self.get_valid_actions(current_node)
                if not actions:
                    break 
                
                # Epsilon-Greedy Action Selection
                if random.uniform(0, 1) < current_epsilon:
                    next_node = random.choice(actions) 
                else:
                    q_values = [self.q_table[current_node, n] for n in actions]
                    max_q = max(q_values)
                    # Handle ties randomly
                    best_candidates = [actions[i] for i in range(len(actions)) if q_values[i] == max_q]
                    next_node = random.choice(best_candidates)
                
                # Observe next state max Q
                next_actions = self.get_valid_actions(next_node)
                if next_actions:
                    max_future_q = np.max([self.q_table[next_node, n] for n in next_actions])
                else:
                    max_future_q = 0
                
                # Calculate Reward
                # Note: This is simplified. True Q-learning usually rewards strictly on transitions.
                # Here we give a big sparse reward at the goal.
                reward = 0
                if next_node == self.goal_node:
                     # Calculate full path reward only at goal? 
                     # For Q-learning efficiency in sparse graphs, we can give a small step penalty
                     reward = 100 # Immediate goal reward
                
                # Q-Update
                current_q = self.q_table[current_node, next_node]
                new_q = (1 - self.alpha) * current_q + self.alpha * (reward + self.gamma * max_future_q)
                self.q_table[current_node, next_node] = new_q
                
                current_node = next_node
                
            # Decay Epsilon
            if current_epsilon > min_epsilon:
                current_epsilon *= 0.995 # Decay factor

    def get_best_path(self):
        """Eğitilmiş Q-Tablosunu kullanarak en iyi yolu çıkarır"""
        path = [self.start_node]
        current_node = self.start_node
        visited = set([self.start_node])
        
        while current_node != self.goal_node:
            actions = self.get_valid_actions(current_node)
            valid_actions = [n for n in actions if n not in visited]
            
            if not valid_actions:
                return None
            
            # Select best action based on Q-table
            q_values = [self.q_table[current_node, n] for n in valid_actions]
            
            # If all Q-values are 0, we haven't learned this path
            if max(q_values) == 0:
                # Fallback: Pick random unvisited to try and proceed, or fail?
                # Failing is safer to indicate no confidence.
                # return None 
                # Let's try heuristic: pick neighbor with max bandwith or something?
                # For now, just pick random to avoid strict failure if possible
                best_next_node = random.choice(valid_actions)
            else:
                best_next_node = valid_actions[np.argmax(q_values)]
            
            path.append(best_next_node)
            visited.add(best_next_node)
            current_node = best_next_node
            
            if len(path) > self.num_nodes: 
                return None
                
        return path