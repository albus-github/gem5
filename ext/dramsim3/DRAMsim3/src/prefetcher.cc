#include "prefetcher.h"

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
    if (trans_addr.bank == prefetch_addr.bank && trans_addr.row == prefetch_addr.row && trans_addr.bankgroup == prefetch_addr.bankgroup && trans.addr != prefetch_trans.addr){
        if (PF.PrefetchFilter.find(prefetch_trans.addr) == PF.PrefetchFilter.end()){
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
    //PrefetchBuffer.epoch_update(PF);
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
void NextLine_Prefetcher::GetPrefetch(){
    prefetch_trans.addr += 64;
    prefetch_trans.IsPrefetch = true;
    prefetch_trans.is_write = false;
}

trans_info SPP_Prefetcher::get_info(const Transaction &trans){
    auto addr = config_.AddressMapping(trans.addr);
    //int tag = 100000 * addr.bank + addr.row;    //v1
    int tag = trans.addr >> 12;    //v2
    trans_info info = {tag, trans.addr, addr};
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
    auto it = PatternTable.find(index);
    delta_entry entry;
    entry.delta = delta;
    entry.c_delta = 1;
    if (it != PatternTable.end()){
        it->second.c_sig ++;
        for (auto delta_it = it->second.delta.begin(); delta_it != it->second.delta.end(); delta_it++){
            if (delta == delta_it->delta){
                delta_it->c_delta ++;
                return;
            }
        }
        it->second.delta.push_back(entry);
    } else {
        PT_entry pt_entry;
        pt_entry.c_sig = 1;
        pt_entry.delta.push_back(entry);
        PatternTable.insert({index, pt_entry});
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
    PT.update(index, delta);
    ST.update(info, delta);
    sig = ST.getsignature(info);
}

void SPP_Prefetcher::GetPrefetch(){
    prefetch_delta = PT.prefetch_delta(sig);
    prefetch_trans.addr = prefetch_trans.addr + 64 * prefetch_delta.delta;
    prefetch_trans.IsPrefetch = true;
    prefetch_trans.is_write = false;
    P = a * P * prefetch_delta.p;
    sig = ST.newsignature(sig, prefetch_delta.delta);
}

void SPP_Prefetcher::UpdateaDistance(){
    a = Updatea();
}

void SPP_Prefetcher::initial(const Transaction &trans){
    prefetch_trans = trans;
    trans_info transinfo = get_info(trans);
    updateSTandPT(transinfo);
    P = 1;
    i = 0;
}

bool SPP_Prefetcher::Continue(){
    if (P > Th && i < distance)
        return true;
    return false;
}
}