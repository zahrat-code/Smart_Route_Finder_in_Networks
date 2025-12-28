import networkx as nx
from math import log,exp
from ..generation import generate_graf as gg


def Total_Delay(G,path):
    """
        Verilen yolun toplam gecikmesini (Link + Node Processing) hesaplar.
        """
    TotalDelay = 0

    for i in range(len(path)-1):
        u=path[i]
        v=path[i+1]
        TotalDelay += G.edges[u,v]["link_delay_ms"]

    for i in range(1,len(path)-1):
        TotalDelay+=G.nodes[path[i]]["processing_delay_ms"]

    return round(TotalDelay,4)

def Total_Reliability(G,path):
    """
        Verilen yolun toplam güvenilirliğini hesaplar.
        Not: Çarpım işlemini toplama çevirmek için -log dönüşümü kullanılmıştır.
        Düşük değer = Yüksek Güvenilirlik.
        """
    TotalReliability = 0

    for i in range(len(path)-1):
        u=path[i]
        v=path[i+1]
        r_link = G.edges[u,v]["link_reliability"]
        if r_link <= 0: r_link = 0.0001
        TotalReliability += (-1*log(r_link))

    for i in range(1,len(path)-1):
        r_node = G.nodes[path[i]]["node_reliability"]
        if r_node <= 0: r_node = 0.0001
        TotalReliability+=(-1*log(r_node))

    return round(TotalReliability,4)

def Total_Bandwidth(G,path):
    """
        Verilen yolun bant genişliği maliyetini hesaplar.
        OSPF mantığı (1000 / Bandwidth) kullanılmıştır.
        """

    ResourceCost=0
    for i in range(len(path)-1):
        u=path[i]
        v=path[i+1]
        bw = G.edges[u,v]["bandwidth_mbps"]
        if bw <= 0:
            ResourceCost += 100000 # High penalty for 0 bandwidth
        else:
            ResourceCost+= (1000/bw)
    return round(ResourceCost,4)


if __name__ == "__main__":
    print("--- METRİK HESAPLAMA TESTİ BAŞLIYOR ---\n")

    # 1. Grafı Oluştur
    G = gg.graf_uret()
    print(f"Graf oluşturuldu. Node sayısı: {len(G.nodes)}")

    # 2. Rastgele bir yol bul (0'dan 4'e en kısa yol gibi)
    # Not: Senin algoritman değil, test için hazır fonksiyon kullanıyoruz.
    try:
        ornek_yol = nx.shortest_path(G, source=0, target=4)
        print(f"Test edilecek yol: {ornek_yol}")
        print("-" * 30)

        # 3. Senin Fonksiyonlarını Test Et

        # --- TEST A: GECİKME ---
        gecikme = Total_Delay(G, ornek_yol)
        print(f"1. Toplam Gecikme (Total_Delay): {gecikme} ms")

        # --- TEST B: GÜVENİLİRLİK ---
        guvenilirlik_cost = Total_Reliability(G, ornek_yol)
        gercek_yuzde = exp(-guvenilirlik_cost)  # Maliyeti yüzdeye geri çeviriyoruz
        print(f"2. Güvenilirlik Maliyeti (Cost): {guvenilirlik_cost}")
        print(f"   -> Gerçek Güvenilirlik Oranı: %{gercek_yuzde * 100:.4f}")

        # --- TEST C: BANT GENİŞLİĞİ ---
        bant_maliyeti = Total_Bandwidth(G, ornek_yol)
        print(f"3. Bant Genişliği Maliyeti: {bant_maliyeti}")

        print("-" * 30)
        print("✅ TEST BAŞARIYLA TAMAMLANDI. Kodların hatasız çalışıyor.")

    except nx.NetworkXNoPath:
        print("❌ Hata: Seçilen düğümler arasında yol yok. Seed değiştirip tekrar dene.")
    except KeyError as e:
        print(f"❌ Hata: İsim uyuşmazlığı var! Kod '{e}' ismini bulamıyor.")
    except Exception as e:
        print(f"❌ Beklenmedik Hata: {e}")