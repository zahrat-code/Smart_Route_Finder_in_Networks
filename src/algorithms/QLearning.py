import numpy as np
import random
import networkx as nx
from ..generation import generate_graf 
from ..core import Metrics       


EPISODES = 100 # Reduced for faster demo performance

ALPHA = 0.1            
GAMMA = 0.9            
EPSILON = 0.1          


W_DELAY = 0.33
W_RELIABILITY = 0.33
W_RESOURCE = 0.34

class QLearningAgent:
    def __init__(self, start_node, goal_node, G=None):
        
        if G is None:
            print("Graf yükleniyor...")
            self.G = generate_graf.graf_uret()
        else:
            self.G = G
            
        self.nodes = list(self.G.nodes())

        self.num_nodes = len(self.nodes)
        
        self.start_node = start_node
        self.goal_node = goal_node
        
        
        self.q_table = np.zeros((self.num_nodes, self.num_nodes))

    def get_valid_actions(self, current_node):
        """Bir düğümden gidilebilecek komşuları döndürür"""
        return list(self.G.neighbors(current_node))

    def calculate_reward(self, path):
        """
        PDF'teki Formül (Sayfa 6):
        Reward = 1000 / TotalCost(P)
        
        TotalCost(P) = (W_delay * Delay) + (W_rel * RelCost) + (W_res * ResCost)
        """
        
        if not path or path[-1] != self.goal_node:
            return 0.1 
        
        
        total_delay = Metrics.Total_Delay(self.G, path)
        rel_cost = Metrics.Total_Reliability(self.G, path)
        res_cost = Metrics.Total_Bandwidth(self.G, path)
        
        
        total_cost = (W_DELAY * total_delay) + \
                     (W_RELIABILITY * rel_cost) + \
                     (W_RESOURCE * res_cost)
        
        
        if total_cost == 0: total_cost = 0.001
        
        
        return 1000.0 / total_cost

    def train(self):
        print(f"Q-Learning Eğitimi Başlıyor ({EPISODES} epizot)...")
        
        for episode in range(EPISODES):
            current_node = self.start_node
            path = [current_node]
            
            
            for _ in range(self.num_nodes * 2):
                if current_node == self.goal_node:
                    break
                
                actions = self.get_valid_actions(current_node)
                if not actions:
                    break 
                
                
                if random.uniform(0, 1) < EPSILON:
                    next_node = random.choice(actions) 
                else:
                    
                    q_values = [self.q_table[current_node, n] for n in actions]
                    max_q = max(q_values)
                    
                    best_candidates = [actions[i] for i in range(len(actions)) if q_values[i] == max_q]
                    next_node = random.choice(best_candidates)
                
                
                
                
                next_actions = self.get_valid_actions(next_node)
                if next_actions:
                    max_future_q = np.max([self.q_table[next_node, n] for n in next_actions])
                else:
                    max_future_q = 0
                
                
                reward = 0
                if next_node == self.goal_node:
                    temp_path = path + [next_node]
                    reward = self.calculate_reward(temp_path)
                
                current_q = self.q_table[current_node, next_node]
                
                
                new_q = (1 - ALPHA) * current_q + ALPHA * (reward + GAMMA * max_future_q)
                self.q_table[current_node, next_node] = new_q
                
                current_node = next_node
                path.append(current_node)
                
            if (episode + 1) % 1000 == 0:
                print(f"Epizot {episode + 1}/{EPISODES} tamamlandı...")

        print("Eğitim Bitti!")

    def get_best_path(self):
        """Eğitilmiş Q-Tablosunu kullanarak en iyi yolu çıkarır"""
        path = [self.start_node]
        current_node = self.start_node
        visited = set([self.start_node])
        
        print(f"\nEn iyi yol aranıyor ({self.start_node} -> {self.goal_node})...")
        
        while current_node != self.goal_node:
            actions = self.get_valid_actions(current_node)
            
            valid_actions = [n for n in actions if n not in visited]
            
            if not valid_actions:
                print("Hata: Yol tıkandı!")
                return None
            
            
            q_values = [self.q_table[current_node, n] for n in valid_actions]
            best_next_node = valid_actions[np.argmax(q_values)]
            
            path.append(best_next_node)
            visited.add(best_next_node)
            current_node = best_next_node
            
            if len(path) > self.num_nodes: 
                print("Hata: Sonsuz döngü tespit edildi.")
                return None
                
        return path


if __name__ == "__main__":
    
    start = 0
    target = 249
    
    agent = QLearningAgent(start, target)
    
    
    agent.train()
    
    
    best_path = agent.get_best_path()
    
    if best_path:
        print("\n" + "="*40)
        print("🚀 Q-LEARNING SONUÇLARI")
        print("="*40)
        print(f"Bulunan Yol: {best_path}")
        print(f"Adım Sayısı (Hop Count): {len(best_path) - 1}")
        
        
        d = Metrics.Total_Delay(agent.G, best_path)
        r_cost = Metrics.Total_Reliability(agent.G, best_path)
        bw_cost = Metrics.Total_Bandwidth(agent.G, best_path)
        
        total_cost = (W_DELAY * d) + (W_RELIABILITY * r_cost) + (W_RESOURCE * bw_cost)
        final_reward = 1000 / total_cost if total_cost > 0 else 0
        
        print("-" * 30)
        print(f"⏱️  Toplam Gecikme: {d} ms")
        print(f"🛡️  Güvenilirlik Maliyeti: {r_cost}")
        print(f"📉 Kaynak Maliyeti: {bw_cost}")
        print(f"💰 Toplam Ağırlıklı Maliyet: {total_cost:.4f}")
        print(f"🏆 Hesaplanan Reward: {final_reward:.4f}")
        print("="*40)
    else:
        print("Yol bulunamadı.")