import networkx as nx
import pandas as pd



import os

# Excel dosyalarının yolları
# Script location: src/generation/generate_graf.py
# Data location: src/data/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # points to src
DATA_DIR = os.path.join(BASE_DIR, "data")

NODE_DATA_PATH = os.path.join(DATA_DIR, "NodeData.xlsx")
EDGE_DATA_PATH = os.path.join(DATA_DIR, "EdgeData.xlsx")



# Excel'den Graf oluşturucu 
def graf_uret():

    # Boş bir graph oluştur
    G = nx.Graph()

    
    #  NODE VERİLERİNİ OKU
    df_nodes = pd.read_excel(NODE_DATA_PATH)

    # Her satır bir node'u temsil eder
    for _, row in df_nodes.iterrows():
        node_id = int(row["node_id"])

        G.add_node(
            node_id,
            processing_delay_ms = float(row["s_ms"]),
            node_reliability    = float(row["r_node"])
        )

   
    # 2) EDGE VERİLERİNİ OKU
    df_edges = pd.read_excel(EDGE_DATA_PATH)

    # Her satır bir edge'i temsil eder
    for _, row in df_edges.iterrows():
        src = int(row["src"])
        dst = int(row["dst"])

        G.add_edge(
            src,
            dst,
            bandwidth_mbps   = float(row["capacity_mbps"]),
            link_delay_ms    = float(row["delay_ms"]),
            link_reliability = float(row["r_link"])
        )

    return G


# Grafik yapısını kontrol et
def kontrol_yazdir(G):
    print("GRAF HIZLI KONTROL")
    print("Düğüm sayısı:", G.number_of_nodes())
    print("Kenar sayısı:", G.number_of_edges())

    # Örnek node yazdır
    node = list(G.nodes())[0]
    print(f"Örnek düğüm {node} özellikler:", G.nodes[node])

    # Örnek edge yazdır
    u, v = list(G.edges())[0]
    print(f"Örnek kenar ({u}, {v}) özellikler:", G.edges[u, v])

    print("Bağlı mı?:", nx.is_connected(G))


# Ana çalıştırma bloğu
if __name__ == "__main__":
    G = graf_uret()
    kontrol_yazdir(G)
