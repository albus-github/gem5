#include "prefetcher.h"
#include "command_queue.h"

namespace dramsim3 {

//Maintain data consistency when write new datas in the same address of the entry in the prefetch-buffer
void Prefetcher::W_ivicte(uint64_t addr){
    PrefetchBuffer.ivicte(addr);
    PF.ivicte_entry(addr);
}

void Prefetch_Buffer::set(uint64_t addr, Prefetch_Filter PF) {
    if (m.find(addr) != m.end()) {
        PrefetchEntry* p = *(m[addr]);
        l.erase(m[addr]);
        m.erase(addr);
        l.push_front(p);
        m[addr] = l.begin();
        p->life = 0;
    } else {
        PrefetchEntry* p = new PrefetchEntry();
        p->addr = addr;
        p->hit_count = 0;
        p->valid = 0;
        p->life = 0;
        if (l.size() >= capacity){
            auto last = l.back();
            l.pop_back();
            m.erase(last->addr);
            l.push_front(p);
            m.insert({addr, l.begin()});
            PF.ivicte_entry(last->addr);
        } else {
            l.push_front(p);
            m.insert({addr, l.begin()});               
        }
    }
}

bool Prefetch_Buffer::hit(uint64_t addr){
    if (m.find(addr) != m.end()){
        PrefetchEntry* p = *(m[addr]);
        l.erase(m[addr]);
        m.erase(addr);

        auto insert_pos = l.begin();
        for (; insert_pos != l.end(); ++insert_pos) {
            if ((*insert_pos)->valid == 1) {
                break;
            }
        }
        l.insert(insert_pos, p);
        m.insert({addr, --insert_pos});

        /*l.push_front(p);
        m[addr] = l.begin();*/

        p->valid = 1;
        p->hit_count ++;
        if (p->hit_count > 1){
            std::cout<<"Addr: "<<addr<<std::endl;
        }
        return true;
    }
    return false;
}

void Prefetch_Buffer::ivicte(uint64_t addr){
    if (m.find(addr) != m.end()){
        l.erase(m[addr]);
        m.erase(addr);
    }
}

void Prefetch_Buffer::epoch_update(Prefetch_Filter PF){
    for (auto it = l.begin(); it != l.end();){
        (*it)->life ++;
        if ((*it)->life == 5){
            PF.ivicte_entry((*it)->addr);
            m.erase((*it)->addr);
            it = l.erase(it);
        } else
            it ++;
    }
}

int Prefetch_Buffer::prefetch_latency(uint64_t addr){
    if (m.find(addr) != m.end()){
        PrefetchEntry* p = *(m[addr]);
        return p->life;
    }
}

void Time_Table::update(Transaction &trans){
    auto it = TimeTable.find(trans.addr);
    if (it != TimeTable.end()){
        TimeTable.erase(it);
    } else {
        if (TimeTable.size() >= capacity){
            auto minElement = std::min_element(TimeTable.begin(), TimeTable.end(),
                [](const std::pair<uint64_t, uint64_t> &lhs, const std::pair<uint64_t, uint64_t> &rhs) {
                    return lhs.second < rhs.second;
                });
            TimeTable.erase(minElement);
        }
    }
    TimeTable.emplace(trans.addr, trans.added_cycle);
}

void Latency_Table::update_arrival(Transaction &trans){
    int delta = 0;
    auto maxElement = std::max_element(TT.TimeTable.begin(), TT.TimeTable.end(),
        [](const std::pair<uint64_t, uint64_t> &lhs, const std::pair<uint64_t, uint64_t> &rhs) {
            return lhs.second < rhs.second;
        });
    if (maxElement != TT.TimeTable.end()){
        time.num_arrival ++;
        time.arrival_latency = (time.arrival_latency * (time.num_arrival - 1) + trans.added_cycle - maxElement->second) / time.num_arrival;
    }
    for (auto it = TT.TimeTable.begin(); it != TT.TimeTable.end(); it++){
        delta = trans.addr - it->first;
        auto delta_it = LatencyTable.find(delta);
        if (delta_it != LatencyTable.end()){
            delta_it->second.num_arrival ++;
            delta_it->second.arrival_latency = (delta_it->second.arrival_latency * (delta_it->second.num_arrival - 1) + trans.added_cycle - it->second) / delta_it->second.num_arrival;
        } else if (abs(delta) < 1024 * 64){
            timestamp entry;
            entry.arrival_latency = trans.added_cycle - it->second;
            entry.fetch_latency = 0;
            entry.num_arrival = 1;
            entry.num_fetch = 0;
            LatencyTable.insert(std::make_pair(delta, entry));
        }
    }
    TT.update(trans);
}

void Latency_Table::update_fetch(Transaction &trans){
    int delta = 0;
    time.num_fetch ++;
    time.fetch_latency = (time.fetch_latency * (time.num_fetch - 1) + trans.complete_cycle - trans.added_cycle) / time.num_fetch;
    for (auto it = TT.TimeTable.begin(); it != TT.TimeTable.end(); it++){
        if (trans.added_cycle <= it->second)
            continue;
        delta = trans.addr - it->first;
        auto delta_it = LatencyTable.find(delta);
        if (delta_it != LatencyTable.end()){
            delta_it->second.num_fetch ++;
            delta_it->second.fetch_latency = (delta_it->second.fetch_latency * (delta_it->second.num_fetch - 1) + trans.complete_cycle - trans.added_cycle) / delta_it->second.num_fetch;
        }
    }
}

bool Latency_Table::Istimely(const Transaction &trans, Transaction &prefetch_trans){
    int delta = prefetch_trans.addr - trans.addr;
    auto it = LatencyTable.find(delta);
    if (it != LatencyTable.end()){
        if (it->second.fetch_latency > it->second.arrival_latency){
            return false;
        }
    } else if (time.fetch_latency < time.arrival_latency * 3){
        return false;
    }
    return true;
}

bool Prefetcher::PrefetchHit(uint64_t addr){
    if (PF.update_useful(addr)){
        epoch_hit ++;
    }
    return PrefetchBuffer.hit(addr);
}

//When the prefetche-buffer is full, the least used entry will be ivicted
/*uint64_t Prefetcher::R_ivicte(uint64_t clk){
    if (!PrefetchBuffer.empty()){
        for (auto it = PrefetchBuffer.begin(); it != PrefetchBuffer.end(); it++){
            if ((clk - it->add_cycle) > 200){
                PrefetchBuffer.erase(it);
                return it->addr;
            }
        }

        auto minIt = std::min_element(
        PrefetchBuffer.begin(), PrefetchBuffer.end(),
        [](const PrefetchEntry &a, const PrefetchEntry &b) {
            return a.hit_count < b.hit_count;
        }
        );
        PrefetchBuffer.erase(minIt);
        return minIt->addr;
    }
}*/

//decide whether to issue prefetch
bool Prefetcher::IssuePrefetch(const Transaction &trans, Transaction &prefetch_trans){
    Address trans_addr = config_.AddressMapping(trans.addr);
    Address prefetch_addr = config_.AddressMapping(prefetch_trans.addr);
    Address next_addr = config_.AddressMapping(prefetch_trans.addr + 64);
    if (trans_addr.row == prefetch_addr.row && trans.addr != prefetch_trans.addr || trans_addr.bank != prefetch_addr.bank || trans_addr.bankgroup != prefetch_addr.bankgroup){
        if (PF.PrefetchFilter.find(prefetch_trans.addr) == PF.PrefetchFilter.end() /*&& LT.Istimely(trans, prefetch_trans)*/){
            /*if (prefetch_addr.row != next_addr.row || prefetch_addr.bank != next_addr.bank || prefetch_addr.bankgroup != next_addr.bankgroup){
                prefetch_trans.IsPrefetch = 2;
            }*/
            return true;
        }
    }
    return false;
}

double Prefetcher::Updatea(){
    double a;
    if (epoch_total != 0){
        a = epoch_hit / epoch_total;
    } else {
        a = 0.5;
    }
    epoch_hit = 0;
    epoch_total = 0;
    //PrefetchBuffer.epoch_update(PF);  //life time
    PF.update_valid();
    return a;
}

void Prefetcher::UpdateaDistance(){
    double epcoh_a = Updatea();
    if (epcoh_a > Th){
        if (distance < 5){
            distance = 5;
        } else if (distance <10){
            distance ++;
        }
    } else if (epcoh_a > Tl){
            distance = 5;
    } else {
        if (distance > 5){
            distance = 5;
        } else if (distance == 1){
            distance = 1;
        } else{
            distance --;
        }
    }
}

void Prefetcher::UpdatePrefetchBuffer(Transaction &trans){
    PrefetchBuffer.set(trans.addr, PF);
}

void Prefetcher::initial(const Transaction &trans){
    i = 0;
    prefetch_trans = trans;
}

bool Prefetcher::Continue(){
    if (i < distance)
        return true;
    return false;
}

//Get the Perfetch command
Transaction NextLine_Prefetcher::GetPrefetch(){
    prefetch_trans.addr += 64;
    prefetch_trans.IsPrefetch = 1;
    prefetch_trans.is_write = false;
    return prefetch_trans;
}

trans_info Prefetcher::get_info(const Transaction &trans){
    auto addr = config_.AddressMapping(trans.addr);
    //int tag = 100000 * addr.bank + addr.row;    //v1
    //int tag = trans.addr >> 12;    //v2
    trans_info info = {0, trans.addr, addr};
    return info;
}

int Signature_Table::getdelta(trans_info info){
    for (auto it = SignatureTable.begin(); it != SignatureTable.end(); it++){
        if (it->tag == info.tag){
            int delta = info.addr.column - it->last_offset;
            return delta;
        }
    }
    return 0;
}

uint16_t Signature_Table::getsignature(trans_info info){
    for (auto it = SignatureTable.begin(); it != SignatureTable.end(); it++){
        if (it->tag == info.tag){
            return it->signature;
        }
    }
    ST_entry entry = {info.tag, 0, 0};
    SignatureTable.push_back(entry);
    return entry.signature;
}

uint16_t Signature_Table::newsignature(uint16_t signature, int delta){
    uint16_t mask = 0b0000111111111111;
    uint16_t new_signature = ((signature << 3) ^ delta) & mask;
    return new_signature;
}

void Signature_Table::update(trans_info info, int delta){
    for (auto it = SignatureTable.begin(); it != SignatureTable.end(); it++){
        if (it->tag == info.tag){
            it->last_offset = info.addr.column;
            it->signature = newsignature(it->signature, delta);
            return;
        }
    }
    ST_entry entry = {info.tag, info.addr.column, newsignature(0, info.addr.column)};
    SignatureTable.push_back(entry);
    return;  
}

void Pattern_Table::update(uint16_t index, int delta){
    if (delta == 0)
        return;
    auto it = PatternTable.find(index);
    delta_entry entry;
    entry.delta = delta;
    entry.c_delta = 1;
    if (it != PatternTable.end()){
        for (auto delta_it = it->second.delta.begin(); delta_it != it->second.delta.end(); delta_it++){
            if (delta == delta_it->delta){
                delta_it->c_delta ++;
                return;
            }
        }
        if (it->second.delta.size() == 16) {
            it->second.delta.erase(it->second.delta.begin());
        }
        it->second.delta.push_back(entry);
    } else {
        PT_entry pt_entry;
        pt_entry.c_sig = 1;
        pt_entry.delta.push_back(entry);
        PatternTable.insert({index, pt_entry});
    }
}

void Pattern_Table::updatesig(uint16_t index){
    auto it = PatternTable.find(index);
    if (it != PatternTable.end()){
        it->second.c_sig++;
    }
}

prefetch_info Pattern_Table::prefetch_delta(uint16_t signature){
    prefetch_info prefetch_delta;
    auto it = PatternTable.find(signature);
    if (it != PatternTable.end()){
        auto max_delta_it = std::max_element(
            it->second.delta.begin(), it->second.delta.end(),
                [](const delta_entry &a, const delta_entry &b) {
                    return a.c_delta < b.c_delta;
                }
        );
        int delta = max_delta_it->delta;
        prefetch_delta.delta = delta;
        double p;
        if (it->second.c_sig != 0){
            p = max_delta_it->c_delta / it->second.c_sig;
        } else{
            p = 0;
        }
        if (p >= 0.25 && delta != 0){
            prefetch_delta.p = p;            
        }
        else{
            prefetch_delta.p = 0;
        }
        return prefetch_delta;
    } else {
        prefetch_delta.delta = 0;
        prefetch_delta.p = 0;
        return prefetch_delta;
    }
}

void Prefetch_Filter::add_entry(uint64_t addr){
    PrefetchFilter.insert({addr, {1,0}});
}

void Prefetch_Filter::ivicte_entry(uint64_t addr){
    auto it = PrefetchFilter.find(addr);
    if (it != PrefetchFilter.end()){
        PrefetchFilter.erase(it);
    }
}

bool Prefetch_Filter::update_useful(uint64_t addr){
    auto it = PrefetchFilter.find(addr);
    if (it != PrefetchFilter.end()){
        if (it->second.useful == 0){
            it->second.useful = 1;
            if (it->second.valid == 1)
            return true;
        }
    }
    return false;
}

History_Table::History_Table(int group, int way) {
  this->group = group;
  this->way = way;
  HistoryTable = new History_Table_entry*[group];
  delta = new int64_t[group];
  for (int i = 0; i < group; i++) {
    HistoryTable[i] = new History_Table_entry[way];
  }
}

void History_Table::update_historytable(uint16_t tag, uint64_t addr){
    int set = tag % group;
    History_Table_entry* entry = new History_Table_entry(tag, addr);
    History_Table_entry* prev = nullptr;
    History_Table_entry* curr = HistoryTable[set];
    /*while (curr != nullptr && curr->tag != entry->tag) {
        prev = curr;
        curr = curr->next;
    }
    if (curr != nullptr) { 
        if (prev != nullptr) {
            prev->next = curr->next;
            curr->next = HistoryTable[set];
            HistoryTable[set] = curr;
        }
    } else {*/
        entry->next = HistoryTable[set];
        HistoryTable[set] = entry;
        count[set]++;
        if (count[set] > way) {
            prev = nullptr;
            curr = HistoryTable[set];
            while (curr->next != nullptr) {
                prev = curr;
                curr = curr->next;
            }
            if (prev != nullptr) {
                prev->next = nullptr;
                delete curr;
            }
            count[set]--; 
        }
    //}
}

void History_Table::get_delta(uint16_t tag, uint64_t addr){
    int set = tag % group;
    int i = 0;
    History_Table_entry* curr = HistoryTable[set];
    while (curr != nullptr && i < 8) {
        if (curr->tag == tag) {
            delta[i] = addr - curr->addr;
            ++i;
        }
        curr = curr->next;
    }
    return;
}

void Delta_Table::update_coverage(){
    for (auto it = PatternTable.begin(); it != PatternTable.end(); ++it){
        if (it->second.c_sig == 16){
            for (auto deltait = it->second.delta.begin(); deltait != it->second.delta.end(); ++deltait){
                deltait->c_delta = 0;
            }
        }
        it->second.c_sig = 0;
    }
    return;
}

void Delta_Table::get_delta(uint16_t tag){
    auto it = PatternTable.find(tag);
    if (it != PatternTable.end()){
        PT_entry entry = it->second;
        std::sort(entry.delta.begin(), entry.delta.end(),
            [](const delta_entry &a, const delta_entry &b) {
                return a.c_delta > b.c_delta;
                }
        );
        for (int i = 0; i < 8; i++) {
            if (entry.delta[i].delta == 0){
                continue;
            } else {
                if (i < entry.delta.size()) {
                prefetch_delta[i] = entry.delta[i].delta;
                } else {
                prefetch_delta[i] = 0;
                }
            }
        }

    } else {
        for (int i = 0; i < prefetch_delta.size(); i++) {
            prefetch_delta[i] = 0;
        }
        return;
    }
}

void Delta_Table::update_capacity(int distance){
    prefetch_delta.resize(distance);
}

void Prefetch_Filter::update_valid(){
    for (auto& entry : PrefetchFilter) {
        entry.second.valid = 0;
    }
}

bool Prefetch_Filter::hit(uint64_t addr){
    if (PrefetchFilter.find(addr) != PrefetchFilter.end())
        return true;
    return false;
}

void SPP_Prefetcher::updateSTandPT(trans_info info){
    uint16_t index = ST.getsignature(info);
    int delta = ST.getdelta(info);
    PT.updatesig(index);
    PT.update(index, delta);
    ST.update(info, delta);
    sig = ST.getsignature(info);
}

Transaction SPP_Prefetcher::GetPrefetch(){
    prefetch_delta = PT.prefetch_delta(sig);
    prefetch_trans.addr = prefetch_trans.addr + 64 * prefetch_delta.delta;
    prefetch_trans.IsPrefetch = 1;
    prefetch_trans.is_write = false;
    P = a * P * prefetch_delta.p;
    sig = ST.newsignature(sig, prefetch_delta.delta);
    return prefetch_trans;
}

void SPP_Prefetcher::UpdateaDistance(){
    a = Updatea();
}

int SPP_Prefetcher::get_tag(uint64_t addr){
    int tag = addr >> 12;
    return tag;
}

void SPP_Prefetcher::initial(const Transaction &trans){
    prefetch_trans = trans;
    int tag = get_tag(trans.addr);
    trans_info transinfo = get_info(trans);
    transinfo.tag = tag;
    updateSTandPT(transinfo);
    P = 1;
    i = 0;
}

bool SPP_Prefetcher::Continue(){
    if (P > Th && i < distance)
        return true;
    return false;
}

void Delta_Prefetcher::initial(const Transaction &trans){
    i = 0;
    prefetch_trans = trans;
    DT.update_capacity(distance);
    for (int i = 0; i < 8 ; ++i){
        HT.delta[i] = 0;
    }
    for (int j = 0; j < DT.prefetch_delta.size(); ++j){
        DT.prefetch_delta[j] = 0;
    }
    tag = get_tag(trans.addr);
    DT.update_coverage();
    update(tag, trans.addr);
}

uint16_t Delta_Prefetcher::get_tag(uint64_t addr){
    uint16_t mask = 0xFFFF;
    addr = addr >> 12;
    uint16_t index = addr & mask;
    return index;
}

void Delta_Prefetcher::update(uint16_t tag, uint64_t addr){
    HT.get_delta(tag, addr);
    HT.update_historytable(tag, addr);
    DT.updatesig(tag);
    for (int i = 0; i < 8; ++i){
        DT.update(tag, HT.delta[i]);
    }
    DT.get_delta(tag);
}

Transaction Delta_Prefetcher::GetPrefetch(){
    Transaction prefetch;
    prefetch.addr = prefetch_trans.addr + DT.prefetch_delta[i];
    prefetch.IsPrefetch = 1;
    prefetch.is_write = false;
    return prefetch;
}

void Delta_Prefetcher::UpdateaDistance(){
    double epcoh_a = Updatea();
    if (epcoh_a > Th){
        if (distance < 8){
            distance = 8;
        } else if (distance < HT.way){
            distance ++;
        }
    } else if (epcoh_a > Tl){
            distance = 8;
    } else {
        if (distance > 8){
            distance = 8;
        } else if (distance == 1){
            distance = 1;
        } else{
            distance --;
        }
    }
}
}