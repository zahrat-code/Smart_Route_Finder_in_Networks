from . import path_utilities as rp
from ..generation import generate_graf as gp
from ..core import Metrics as mr
import random
import pandas as pd


def population(G,source,target,size):
    #popülasyon oluşturma işlemi
    pop_list=[]
    tester=0
    while tester<(size*10):#Alacağımız kadarın 10 katı kadar deneme verdim.Her bir yol girmesi için 10 şans verdim.
        list1=rp.generate_random_path(G,source,target)#Elifin oluşturduğu rastgele yol oluşturma fonksiyonuyla rastgele yollar aldım
        if list1!=None and list1 not in pop_list and len(list1)>=2:#Eğer bu yol var olup olmadığını,popülasyonda var olup olmadığını ve en az 2 node olup olmadığına bakıyor
            pop_list.append(list1)

        if len(pop_list)==size:#Önceden popülasyon dolarsa döngüyü kırıyor.
            break
        tester+=1
    return pop_list


def fitness_calculation(G,pop_list,w_delay=0.5, w_rel=0.1,w_band=0.4,max_delay=100,demand_mbps=0.2):
    #fitness değeerini hesaplama fonsiyonu,burada aslında maliyet hesaplanıyor.Yani en az değeri olan daha iyi.
    pop_fit=[]
    #w_delay+w_rel+w_band=1.Bu denklem şart.

    for pop in pop_list:#Burada tek tek popülasyonda olanların maliyetini hesaplıyor,yaptığım metrics sınıfında.
        TotalDelay=mr.Total_Delay(G,pop)
        TotalReliability=mr.Total_Reliability(G,pop)
        TotalBandwidth=mr.Total_Bandwidth(G,pop)
        min_mbps=float('inf')

        for temp in range(len(pop)-1):
            u=pop[temp]
            v=pop[temp+1]
            mbps=G.edges[u,v]['bandwidth_mbps']
            if mbps<min_mbps:
                min_mbps=mbps


        if TotalDelay > max_delay:#Eğer toplam delay bizim belirlediğimiz max_delaydan yüksekse değerini çöp yapıyoruz.Maksat o yolu seçmesini engellemek.
            fitness = 999999
        elif demand_mbps>min_mbps:
            fitness = 999999
        else:
            fitness=((TotalDelay*w_delay)+(TotalReliability*w_rel)+(TotalBandwidth*w_band))

        pop_fit.append((pop,fitness))#Burada hem yolu hem de onun maliyetini ekliyoruz tupple olarak.

    return pop_fit

def selection(pop_fit):
    #Anne baba seçimi.
    select=[]
    if len(pop_fit) < 4:#Bu if bloğunda gelen maliyeti hesaplanmış yolların sayısı 4 den az ise direkt anne baba seçimi yapıyor.
        pop_fit.sort(key=lambda x: x[1])
        if len(pop_fit) >= 2:
            return pop_fit[0][0], pop_fit[1][0]
        elif len(pop_fit) == 1:
            return pop_fit[0][0], pop_fit[0][0]
        else:
            return None, None
    count=0
    while len(select)<4 and count<50:#Burada  rastgele 4 tanesi seçilmeye çalışılıyor.Aynı değerler olmaması çallışılıyor.Çok zorlamasın diye sayaç koydum.
            temp=random.choice(pop_fit)
            if temp not in select:
                select.append(temp)
            count+=1
    while len(select)<4:#Eğer hala seçilmediyse seçilene kadar ekleme yapılıyor.
        tempeture=random.choice(pop_fit)
        select.append(tempeture)

    select.sort(key=lambda x:x[1])#Burada maliyet değerlerini sıraladım.En düşük olan başta olmak kaydıyla.

    father=select[0]#Sadece yolu alıyorum.Anne ve baba da.
    mother=select[1]

    return father[0],mother[0]

def crossover(father,mother):
    if father==None or mother==None:#Anne veya baba yoksa çocuk da yok.
        return None

    common_node=[node for node in father if node in mother]#ortak noktalarını aldım,crossover yapabilmek için.
    child=[]

    if len(common_node)<2:#ortak nokta 2 den az ise hiç ortak nokta yok.Zaten garanti source ile target olmak zorunda.
        return None

    for index in range(len(common_node)-1):
        u=common_node[index]#Sırasıyla ortak nokta aldığımız için burada ilk ile bir sonraki ortak noktayı alıyorum.
        v=common_node[index+1]

        indFaU=father.index(u)#Burada babnın ortak noktasının indeksini alıyorum.
        indFaV=father.index(v)
        listFa=father[indFaU:indFaV]#Aldığım indekslerin yardımıyla kesim yapıyorum.

        indMoU=mother.index(u)#Aynı senaryo annede de geçerli.
        indMoV=mother.index(v)
        listMo=mother[indMoU:indMoV]

        rand_cho=random.choice([listFa,listMo])#rastgele seçim yapıyorum aralarında.
        child.extend(rand_cho) #Listeye tek tek ekleme yapıyorum.

    child.append(common_node[-1])#En sonda target ı ekliyorum.
    return rp.yolu_Sadelestir(child)#Elifin yaptığı yolu sadeleştir fonksiyonuyla yolu sadeleştiriyorum.Sonra o değeri döndürüyorum.

def multi_mutation(G,child,mutation_rate=0.1):

    if random.random() < mutation_rate and len(child)>2:#Zar atıyorum.Eğer zar tutarsa mutasyon yapılacak.Ayrıyeten çocuğun uzunlu 2 den büyük olması lazım.(S,T)
        temp=None
        zar=random.random()
        if zar<0.33:
            temp=mutation_version1(G,child)
        elif zar<0.66:
            temp=mutation_version2(G,child)
        else:
            temp=mutation_version3(G,child)

        if temp==None:#Boş gelirse mutasyon yaptırmadım.Eğer tam yol geldiyse Elifin yolu sadeleştir fonksiyonuyla yolu sadeleştirip değeri dönderdim.
            return child
        else:
            return rp.yolu_Sadelestir(temp)
    else:
        return child

def mutation_version1(G,child):
    choice = random.randint(1, len(child) - 2)  # Rastgele indeks sayısı aldım.Source ile target ı dahil etmedim.
    temp = child[:choice + 1]  # Seçilen yerde dahil,oraya kadarını aldım.
    temp = rp.tamamla_path(G, temp, child[-1])  # Elifin yaptığı yolu tamamla fonskiyonuyla yolu tamamlattırdım.
    return temp

def mutation_version2(G,child):
    choice = random.randint(1, len(child) - 2)
    child_head=child[:choice + 1]
    tail=child[choice:]
    temp_target=child[choice]
    temp_source=child[0]
    counter=0
    head=None
    while counter<10:
        head=rp.generate_random_path(G,temp_source,temp_target)
        if head is not None and head!=child_head:
            break
        counter+=1
    if head is None:return None
    temp=head[:-1]+tail
    return temp

def mutation_version3(G,child):
    if len(child)>4:
        count=0
        while count<20:
            choice1 = random.randint(1, len(child) - 2)
            choice2 = random.randint(1, len(child) - 2)
            if abs(choice1 - choice2) > 1:
                break
            else:
                count+=1
        if count==20:return child
        firstIndex=min(choice1, choice2)
        lastIndex=max(choice1, choice2)
        temp_head=child[:firstIndex+1]
        tail=child[lastIndex:]
        header=rp.tamamla_path(G,temp_head,child[lastIndex])
        if header is not None:
            mutation_child=header+tail[1:]
            return mutation_child
        else:return None
    else:
        return child

def genetic_algorithm(G,source,target,demand_mbps,pop_size=50,generations=100,mutation_rate=0.1,w_delay=0.33,w_rel=0.33,w_band=0.34,max_delay=100):
    #Main kısmı
    population_group=population(G,source,target,pop_size)#Popülasyon oluşturdum.
    global_best_value=99999#En iyi değeri şimdilik 999999 verdim.İleride en iyi değer değişmezse geçiçi olarak mutasyon oranını arttıracağım.
    mutation_value_count=0#Buda bir üstteki kodun sayacı.
    current_mutation_rate=mutation_rate#Mutation rate kaybolmasın diye geçici bir mutation rate yaptım.Maksat eski oranı kullanmak için.Bunla iş yapacağız.
    for i in range(generations):#Kaç nesil gitsin maksadıyla oluşturuldu.
        fitness_group = fitness_calculation(G, population_group, w_delay, w_rel, w_band,max_delay,demand_mbps)#fitness değerleri hesaplandı.
        best_generetion=[]#çocuklar için oluşturuldu.
        fitness_group.sort(key=lambda x: x[1])#Sıraladım başta.Çünkü bir aşağıda yıldızlarla işaretledğim yerde en iyi iki kişiyi kaybetmemek için onları gruba ekledim.

        if fitness_group[0][1] < global_best_value:#Burada mutasyon oranını yükesltmek amacıyla yapıldı.En iyi değer bulunduysa sayacı sıfırladım.
            global_best_value=fitness_group[0][1]
            mutation_value_count=0
            current_mutation_rate=mutation_rate
        else:#Eğer en iyi değer hala dönmediyse sayacı arttırıyorum.
            mutation_value_count+=1

        if mutation_value_count==10:#Belli bir 10 nesildir hala en iyi değer gelmediyse mutasyon aranını  arttırıyorum.
            current_mutation_rate=0.3

        if mutation_value_count==20:#20 nesıl olunca da mutasyon oranını eski haline getiriyorum.
            current_mutation_rate = mutation_rate

        if rp.yol_gecerli_mi(G,fitness_group[0][0],source,target):#*****Yol geçerli olup olmadığına da baktım.Değerde bozulma ihtimaline karşın kopyaladım.Referrans almadım.
            best_generetion.append(fitness_group[0][0][:])#Referans almadım,kopyaladım.

        if rp.yol_gecerli_mi(G,fitness_group[1][0],source,target):#*****Yol geçerli olup olmadığına da baktım.Değerde bozulma ihtimaline karşın kopyaladım.Referrans almadım.
            best_generetion.append(fitness_group[1][0][:])#Referans almadım,kopyaladım.

        child_count=0#Çocuk while döngüsünde kaç kere eklenmediyse diye sayaç oluşturdum.
        generation_count=0#Eğer best_generation dolmazsa çok zorlamaması açısından sayaç koydum.Her nesil için 1000 kere hak var.
        while len(best_generetion)<pop_size and generation_count<1000:

            father, mother = selection(fitness_group)#Anne baba seçiliyor.
            child = crossover(father, mother)#Crossoveryapılıyor.
            if child is None: continue#Çocuk yoksa devam.
            child = multi_mutation(G, child, current_mutation_rate)#Mutasyon yapılıyor,yapılacaksa tabi.

            if rp.yol_gecerli_mi(G,child, source,target):#Elifin yazdığı yol geçerli mi fonksiyonunda yolun olup olmadığına bakılıyor.True yada false döndürüyor.
                if child not in best_generetion or child_count>15:#Çocuk best_generetion da yoksa veya sayaç 15 i geçtiyse çocuğu ekliyor.
                    best_generetion.append(child)
                    child_count=0
                else:
                    child_count+=1
            generation_count+=1

        population_group=best_generetion#En sonda oluşan çocuklar bir diğer nesili oluşturmak için çocuk yapacak.Yani bunlar anne,baba seçimi olacak.


    fitness_group = fitness_calculation(G, population_group, w_delay, w_rel, w_band,max_delay,demand_mbps)#En sonda oluşan best yolların fitness ını(maliyetini) hesapladım.
    fitness_group.sort(key=lambda x:x[1])#Sıraladım.En düşük maliyet en başta.
    return fitness_group[0][0]#En iyisi döndürdüm.


def read_demands(filename):

    try:
        df = pd.read_csv(filename, sep=";")
        rows = []
        for index, row in df.iterrows():
            source = int(row["src"])
            target = int(row["dst"])
            str_band = str(row["demand_mbps"])

            band = float(str_band.replace(",", "."))
            one_row = (source, target, band)
            rows.append(one_row)

        return rows
    except Exception as e:
        print(f"Dosya okuma hatası : {e}")
        return []


def main():
    print("==========================================")
    print("      GENETİK ALGORİTMA AĞ SİMÜLASYONU     ")
    print("==========================================\n")

    # 1. Dosya İsimleri
    demand_file = "data/DemandData.xlsx"

    # 2. Grafı Yükle
    print("📡 1. Adım: Ağ Topolojisi (Graf) Yükleniyor...")
    try:
        G = gp.graf_uret()  # Arkadaşının fonksiyonu
        print(f"   ✅ Graf Başarıyla Oluşturuldu ({len(G.nodes)} Düğüm, {len(G.edges)} Kenar)\n")
    except Exception as e:
        print(f"   ❌ Graf oluşturulurken hata: {e}")
        return

    # 3. Talepleri Oku
    print(f"📋 2. Adım: Talep Dosyası Okunuyor ({demand_file})...")
    demands = read_demands(demand_file)
    print(f"   ✅ Toplam {len(demands)} adet talep işlenecek.\n")

    # 4. Her Talep İçin Algoritmayı Çalıştır
    print("🚀 3. Adım: Simülasyon Başlıyor...\n")

    successful_routes = 0

    for i, (src, dst, bw_demand) in enumerate(demands):
        print(f"🔹 Talep {i + 1}: Kaynak {src} -> Hedef {dst} | İstenen Hız: {bw_demand} Mbps")

        # Algoritmayı Çağır
        try:
            best_path = ga.genetic_algorithm(
                G,
                source=src,
                target=dst,
                demand_mbps=bw_demand,  # Artık bu parametre işleniyor!
                pop_size=50,
                generations=100,
                mutation_rate=0.1,
                max_delay=200  # Gerçek verilerde gecikme yüksek olabilir
            )

            # Sonuç Kontrolü
            if best_path:
                print(f"   ✅ YOL BULUNDU: {best_path}")
                # İstersen detayları yazdır:
                d = mr.Total_Delay(G, best_path)
                print(f"   📊 Gecikme: {d:.2f} ms")
                successful_routes += 1
            else:
                print("   ❌ UYGUN YOL BULUNAMADI (Kapasite yetersiz veya kopukluk var)")

        except Exception as e:
            print(f"   ⚠️ Algoritma hatası: {e}")

        print("-" * 40)

    print(f"\n🏁 Simülasyon Tamamlandı.")
    print(f"📊 Başarı Oranı: {successful_routes}/{len(demands)}")


if __name__ == "__main__":
    main()