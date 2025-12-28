import pandas as pd
import random
import math
import os


from ..generation import generate_graf as gg
import os

# Metrik hesaplamaları ve yol iyileştirme modüllerini ekliyoruz
from ..core import Metrics as mt
from . import path_utilities as pu


class AntColonyOptimizer:
    def __init__(self, G, S, D, demand, weights, num_ants=20, max_iter=50, alpha=1.0, beta=2.0, evaporation=0.5):
        """
        ACO Algoritması Başlatıcı (Constructor).
        Amaç: Verilen kısıtlar altında S'den D'ye en uygun maliyetli yolu bulmak.
        
        Parametreler:
        - G: Ağ topolojisi (NetworkX graf nesnesi)
        - S, D: Kaynak ve Hedef düğümler
        - demand: İstenen bant genişliği (Bunu sağlamayan yollar elenir)
        - weights: Gecikme, Güvenilirlik ve Bant Genişliği ağırlıkları
        - alpha: Feromonun (kokunun) seçim üzerindeki etkisi
        - beta: Heuristic'in (yol kalitesinin) seçim üzerindeki etkisi
        - evaporation: Buharlaşma katsayısı (Eski yolların unutulması için)
        """
        self.G = G
        self.S = S
        self.D = D
        self.demand = demand 
        self.weights = weights
        self.num_ants = num_ants
        self.max_iter = max_iter
        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        
        # --- FEROMON BAŞLATMA ---
        self.pheromones = {}
        # Başlangıçta tüm yollara eşit miktarda (1.0) feromon atıyoruz.
        # Bu sayede ilk iterasyonda karıncalar tamamen rastgele dağılır.
        for u, v in G.edges():
            self.pheromones[(u, v)] = 1.0
            self.pheromones[(v, u)] = 1.0  # Graf yönlü olmadığı için ters yönü de ekliyoruz
            
        # Heuristic değerleri önceden hesapla
        # Her karınca için tekrar hesaplamamak adına, baştan hesaplayıp hafızaya alıyoruz.
        self.heuristic_cache = {}
        self._precompute_heuristics()

    def _precompute_heuristics(self):
        """
        Her bir kenar için heuristic (çekicilik) değerini önceden hesaplar.
        Böylece döngü içinde tekrar tekrar log, bölme gibi ağır işlemler yapılmaz.
        """
        for u, v in self.G.edges():
            # Gidiş yönü için hesapla ve kaydet
            h_val = self._calculate_single_heuristic(u, v)
            self.heuristic_cache[(u, v)] = h_val
            
            # Dönüş yönü için hesapla ve kaydet
            h_val_reverse = self._calculate_single_heuristic(v, u)
            self.heuristic_cache[(v, u)] = h_val_reverse

    def _calculate_single_heuristic(self, u, v):
        """
        Tek bir kenar (u -> v) için heuristic (çekicilik) değerini hesaplar.
        Heuristic = 1 / (ağırlıklı toplam maliyet)
        Düşük maliyet → Yüksek heuristic → Daha çekici yol
        """
        edge_data = self.G.edges[u, v] #Kenar verileri (Bant genişliği, Gecikme, Güvenilirlik)
        node_data = self.G.nodes[v]    # Hedef düğüm verisi
        
        # KISIT KONTROLÜ
        # Eğer hattın kapasitesi, istenen talebi (demand) karşılamıyorsa;
        # o yolun heuristic değerini 0 yapıyoruz. Karınca orayı "duvar" gibi görür.
        if edge_data.get('bandwidth_mbps', 0) < self.demand:
            return 0.0

        # 1. Gecikme Metriği
        # Toplam Gecikme = Hat Gecikmesi + Düğümdeki İşlem Süresi
        delay_cost = edge_data.get('link_delay_ms', 10) + node_data.get('processing_delay_ms', 1)
        
        # 2. Güvenilirlik Metriği (-log transformation)
        # Güvenilirlik olasılıksal (0.99 gibi) bir değerdir ve seri bağlı sistemlerde çarpılır.
        # Ancak maliyet fonksiyonunda toplama yapabilmek için -log() dönüşümü uygulanır.
        # Sonuç: Güvenilirlik arttıkça, cost değeri sıfıra yaklaşır (küçülür).
        r_link = edge_data.get('link_reliability', 0.99)
        r_node = node_data.get('node_reliability', 0.99)

        # Log(0) hatasını önlemek için güvenli alt sınır
        if r_link <= 0: r_link = 0.0001
        if r_node <= 0: r_node = 0.0001
        rel_cost = (-1 * math.log(r_link)) + (-1 * math.log(r_node))
        
        # 3. Bant Genişliği Metriği
        # Yüksek bant genişliği tercih edilmelidir (Düşük maliyet).
        # Bu yüzden Maliyet = 1000 / Bant Genişliği formülü kullanılır.
        bw = edge_data.get('bandwidth_mbps', 100)
        bw_cost = 1000 / bw if bw > 0 else 10000

        # Ağırlıklı Toplam (Weighted Sum)
        # Üç farklı birimi, kullanıcıdan alınan ağırlıklarla normalize ederek topluyoruz.
        total_step_cost = (self.weights['delay'] * delay_cost) + \
                          (self.weights['reliability'] * rel_cost) + \
                          (self.weights['bandwidth'] * bw_cost)
        
        # Maliyet ile Heuristic ters orantılıdır 
        return 1.0 / (total_step_cost + 0.0001) # (Payda 0 olmasın diye +0.0001 ekledik)

    def _select_next_node(self, current_node, visited):
        """
        Bir karıncanın şu anki düğümden gideceği sonraki düğümü seçer.
        Rulet tekerleği (roulette wheel) seçim mekanizması kullanır.
        """
        neighbors = list(self.G.neighbors(current_node))  # Mevcut düğümün komşuları
        
        candidates = []  # Seçilebilecek komşu düğümler
        probabilities = [] # Her komşunun seçilme olasılığı
        total_prob = 0.0 # Toplam olasılık (normalizasyon için)
        
        for n in neighbors:
            # Döngüsel hareketleri engellemek için ziyaret edilenleri atla
            if n in visited: 
                continue
            
            # Önceden hesaplanmış değerden oku
            eta = self.heuristic_cache.get((current_node, n), 0)
            
            if eta == 0: continue # Eğer heuristic 0 ise (kapasite yetersizse) bu adayı ele
            
            # Feromon değerini al (başlangıçta 1.0)
            tau = self.pheromones.get((current_node, n), 1.0)
            
            # ACO FORMÜLÜ: (Feromon^alpha) * (Heuristic^beta)
            prob = (tau ** self.alpha) * (eta ** self.beta)
            
            candidates.append(n)
            probabilities.append(prob)
            total_prob += prob
            
        if not candidates:  # Hiç uygun komşu yok
            return None

        if total_prob == 0: # Eğer olasılıklar hesaplanamadıysa rastgele seç
            return random.choice(candidates)
            
        # RULET TEKERLEĞİ SEÇİMİ
        # 0 ile Toplam Olasılık arasında rastgele bir nokta seçilir.
        threshold = random.random() * total_prob
        current_sum = 0.0
        for i, p in enumerate(probabilities):
            current_sum += p
            # Kümülatif toplam eşik değerini geçtiği an o düğüm seçilir.
            if current_sum >= threshold:
                return candidates[i]
        
        return candidates[-1]

    def run(self):
        """
        ACO algoritmasını çalıştırır, en iyi yolu ve maliyetini bulur.
        
        Döndürdüğü değerler:
        - best_global_path: En iyi yol (düğüm listesi)
        - best_global_cost: En iyi yolun toplam maliyeti
        - best_metrics: En iyi yolun detaylı metrikleri
        """
        best_global_path = None
        best_global_cost = float('inf') # Sonsuz ile başlatıyoruz (Minimizasyon problemi)
        best_metrics = {'delay': 0, 'rel_cost': 0, 'bw_cost': 0}
        
        # Yakınsama Kontrolü
        # Eğer belirli bir süre boyunca yeni bir rekor gelmezse, algoritmayı erken bitiririz.
        no_improve_count = 0
        
        # Ana döngü: max_iter kadar iterasyon
        for iteration in range(self.max_iter):
            all_paths = []  # Bu iterasyondaki tüm başarılı yollar
            
            # Karıncaları çalıştır: Her biri bir yol arar
            for ant in range(self.num_ants):
                path = [self.S] # Yol kaynağıyla başlar
                visited = set([self.S]) # Ziyaret edilen düğümler kümesi
                current = self.S # Karıncanın şu anki konumu
                
                # Karınca adım adım ilerliyor (Maksimum 100 adım sınırı koyduk, sonsuz döngü olmasın)
                steps = 0
                while current != self.D and steps < 100:
                    nxt = self._select_next_node(current, visited)
                    if nxt is None: break # Gidecek yer yoksa dur
                    path.append(nxt)
                    visited.add(nxt)
                    current = nxt
                    steps += 1
                
                # Karınca Hedefe Ulaştı mı?
                if current == self.D:
                    # Bulunan yolu sadeleştir (Gereksiz döngüleri temizle) - path_utilities modülü
                    clean_path = pu.yolu_Sadelestir(path)
                    
                    # Yolun gerçek metriklerini hesapla
                    d_cost = mt.Total_Delay(self.G, clean_path)
                    r_cost = mt.Total_Reliability(self.G, clean_path)
                    b_cost = mt.Total_Bandwidth(self.G, clean_path)
                    
                    # Toplam maliyet: Ağırlıklı toplam formülü
                    total_cost = (self.weights['delay'] * d_cost) + \
                                 (self.weights['reliability'] * r_cost) + \
                                 (self.weights['bandwidth'] * b_cost)
                    
                    all_paths.append((clean_path, total_cost))
                    
                    # En iyi yolu guncelle (daha düşük maliyet bulduysak)
                    if total_cost < best_global_cost:
                        best_global_cost = total_cost
                        best_global_path = clean_path
                        best_metrics = {'delay': d_cost, 'rel_cost': r_cost, 'bw_cost': b_cost}
                        no_improve_count = 0 # İyileşme oldu, sayacı sıfırla
            
            if not all_paths: continue # Eğer bu turda hiçbir karınca yol bulamadıysa sonraki tura geç

            # Erken Durdurma: 10 iterasyon boyunca gelişme yoksa dur.
            no_improve_count += 1
            if no_improve_count > 10: break
            
            # Feromon Güncelleme

            # 1. Buharlaşma: 
            # Tüm yollardaki koku belirli oranda azaltılır. 
            # Bu işlem, eski ve kötü yolların unutulmasını sağlar.
            for key in self.pheromones:
                self.pheromones[key] *= (1.0 - self.evaporation)
            
            # 2. Yeni Feromon Bırakma:
            # Sadece bu iterasyonun EN İYİ 3 çözümüne feromon eklenir.
            # Bu strateji, çözümün daha hızlı yakınsamasını sağlar.
            all_paths.sort(key=lambda x: x[1]) # Maliyete göre sırala (Küçükten büyüğe)
            best_iteration_paths = all_paths[:3] 
            
            Q = 10.0  # Feromon sabiti
            for path, cost in best_iteration_paths:
                # Epsilon to prevent zero division
                if cost <= 0: cost = 0.0001
                deposit = Q / cost # Maliyet ne kadar azsa bırakılan koku o kadar çok olur

                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    self.pheromones[(u, v)] += deposit
                    self.pheromones[(v, u)] += deposit

        return best_global_path, best_global_cost, best_metrics

#  ANA CALISTIRMA BLOGU 
if __name__ == "__main__":
    print("\n--- ACO ALGORITMASI SONUCLARI ---\n")
    
    # Grafiği Yükle
    try:
        G = gg.graf_uret()
        print(f"Graf yuklendi. Dugum Sayisi: {len(G.nodes)}")
    except Exception as e:
        print(f"HATA: Graf olusturulamadi: {e}")
        exit()

    # Talep Dosyasını (DemandData) Oku
    DEMAND_FILE = "DemandData.xlsx"
    if not os.path.exists(DEMAND_FILE) and os.path.exists("data/DemandData.xlsx"):
        DEMAND_FILE = "data/DemandData.xlsx"
        
    try:
        df_demands = pd.read_excel(DEMAND_FILE)
    except:
        df_demands = pd.DataFrame()

    # SENARYO AGIRLIKLARI [0.4, 0.4, 0.2]
    weights = {'delay': 0.4, 'reliability': 0.4, 'bandwidth': 0.2}
    print(f"Kullanilan Agirliklar: {weights}\n")
    
    # Tablo Basliklari
    header = f"{'No':<4} {'Src':<6} {'Dst':<6} {'Talep':<8} {'Durum':<10} {'Gec(ms)':<10} {'Guv(Cost)':<10} {'BW(Cost)':<10} {'TOPLAM':<10}"
    print(header)
    print("-" * 85)

    # İstatistikleri tutmak için değişkenler
    total_scenarios = 0 # Toplam test senaryosu sayısı
    success_count = 0 # Başarılı çözüm sayısı
    total_cost_sum = 0.0 # Tüm başarılı çözümlerin maliyet toplamı
    
    min_cost_value = float('inf') # En düşük maliyet (başlangıç: sonsuz)
    min_cost_info = "" # En dusuk maliyetli senaryonun bilgisi

    # Excel'deki her bir satır için algoritmayı çalıştır
    for index, row in df_demands.iterrows():
        total_scenarios += 1
        S = int(row['src']) # Kaynak düğüm
        D = int(row['dst']) # Hedef düğüm
        B = float(row['demand_mbps']) # Minimum bant genişliği talebi
        
        # ACO Çalıştır
        aco = AntColonyOptimizer(G, S, D, B, weights, num_ants=20, max_iter=50)
        best_path, cost, metrics = aco.run()
        
        if best_path:
            status = "Basarili"
            success_count += 1
            total_cost_sum += cost
            
            # En düşük maliyeti kontrol et
            if cost < min_cost_value:
                min_cost_value = cost
                min_cost_info = f"No: {index+1} ({S}->{D})"
            
            cost_str = f"{cost:.2f}"
            d_str = f"{metrics['delay']:.2f}"
            r_str = f"{metrics['rel_cost']:.2f}"
            b_str = f"{metrics['bw_cost']:.2f}"
        else:
            status = "Basarisiz"
            cost_str = "-"
            d_str = "-"
            r_str = "-"
            b_str = "-"
        
        print(f"{index+1:<4} {S:<6} {D:<6} {B:<8} {status:<10} {d_str:<10} {r_str:<10} {b_str:<10} {cost_str:<10}")

    print("-" * 85)
    
    # --- GENEL OZET TABLOSU ---
    if success_count > 0:
        avg_cost = total_cost_sum / success_count
    else:
        avg_cost = 0.0
        min_cost_value = 0.0

    print("\n--- GENEL PERFORMANS OZETI ---")
    print(f"Toplam Senaryo     : {total_scenarios}")
    print(f"Basarili Cozum     : {success_count}")
    print(f"Ortalama Maliyet   : {avg_cost:.2f}")
    print(f"En Dusuk Maliyet   : {min_cost_value:.2f} [Senaryo {min_cost_info}]")

    print("------------------------------")

