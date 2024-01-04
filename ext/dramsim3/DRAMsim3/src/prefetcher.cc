#include "prefetcher.h"

namespace dramsim3 {

//Maintain data consistency when write new datas in the same address of the entry in the prefetch-buffer
void Prefetcher::W_ivicte(const Command &cmd){
    auto it = PrefetchBuffer.begin();
    while (it != PrefetchBuffer.end()) {
        if (it->addr == cmd.hex_addr){
            it = PrefetchBuffer.erase(it);
        } 
        else {
            it++;
        }   
    }
}

//When the prefetche-buffer is full, the least used entry will be ivicted
uint64_t Prefetcher::R_ivicte(uint64_t clk){
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
}

//decide whether to issue prefetch(if the row is open)
bool NextLine_Prefetcher::IssuePrefetch(const Command &cmd){
    if (!cmd.IsPrefetch){
        if (cmd.cmd_type == CommandType::READ){
        return true;
        }
    }
    return false;
}

//Get the Perfetch command
Transaction NextLine_Prefetcher::GetPrefetch(const Command &cmd){
    Transaction Prefetch;
    Prefetch.addr = cmd.hex_addr+64;
    Prefetch.IsPrefetch = true;
    Prefetch.is_write = false;
    prefetch_total++;
    return  Prefetch;
}

void Prefetcher::UpdatePrefetchBuffer(Transaction &trans, uint64_t clk){
    for (auto it = PrefetchBuffer.begin(); it != PrefetchBuffer.end(); ++it){
        if (it->addr == trans.addr){
            return;
        }
    }
    if (PrefetchBuffer.size() >= PrefetchBuffer.capacity()){
        R_ivicte(clk);
    }
    PrefetchEntry entry;
    entry.addr = trans.addr;
    entry.hit_count = 0;
    PrefetchBuffer.push_back(entry);
}

trans_info SPP_Prefetcher::get_info(const Transaction &trans){
    auto addr = config_.AddressMapping(trans.addr);
    int tag = 100000 * addr.bank + addr.row;
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
    PrefetchFilter.insert({addr, 0});
}

void Prefetch_Filter::ivicte_entry(uint64_t addr){
    auto it = PrefetchFilter.find(addr);
    if (it != PrefetchFilter.end()){
        PrefetchFilter.erase(it);
    }
}

void Prefetch_Filter::update_useful(const Transaction &trans){
    auto it = PrefetchFilter.find(trans.addr);
    if (it != PrefetchFilter.end()){
        it->second = 1;
    }
}

void SPP_Prefetcher::updateSTandPT(trans_info info){
    uint16_t index = ST.getsignature(info);
    int delta = ST.getdelta(info);
    PT.update(index, delta);
    ST.update(info, delta);
    sig = ST.getsignature(info);
}

void SPP_Prefetcher::GetPrefetch(uint16_t signature){
    prefetch_delta = PT.prefetch_delta(signature);
    prefetch_trans.addr = prefetch_trans.addr + 64 * prefetch_delta.delta;
    prefetch_trans.IsPrefetch = true;
    prefetch_trans.is_write = false;
    P = a * P * prefetch_delta.p;
    sig = ST.newsignature(sig, prefetch_delta.delta);
}

bool SPP_Prefetcher::IssuePrefetch(const Transaction &trans){
    if (P < Tp){
        return false;
    } else {
        auto it = PF.PrefetchFilter.find(trans.addr);
        if (it != PF.PrefetchFilter.end()){
            return false;
        } else {
            return true;
        }
    }
}

void SPP_Prefetcher::UpdatePrefetchBuffer(Transaction &trans, uint64_t clk){
    for (auto it = PrefetchBuffer.begin(); it != PrefetchBuffer.end(); ++it){
        if (it->addr == trans.addr){
            return;
        }
    }
    if (PrefetchBuffer.size() >= PrefetchBuffer.capacity()){
        uint64_t ivite_addr = R_ivicte(clk);
        PF.ivicte_entry(ivite_addr);
    }
    PrefetchEntry entry;
    entry.addr = trans.addr;
    entry.hit_count = 0;
    PrefetchBuffer.push_back(entry);
}
}