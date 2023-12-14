#include "prefetcher.h"

namespace dramsim3 {

//Maintain data consistency when write new datas in the same address of the entry in the prefetch-buffer
void NextLine_Prefetcher::W_ivicte(const Command &cmd){
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
void NextLine_Prefetcher::R_ivicte(){
    if (!PrefetchBuffer.empty()){
        auto minIt = std::min_element(
        PrefetchBuffer.begin(), PrefetchBuffer.end(),
        [](const PrefetchEntry &a, const PrefetchEntry &b) {
            return a.hit_count < b.hit_count;
        }
        );
        PrefetchBuffer.erase(minIt);
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

void NextLine_Prefetcher::UpdatePrefetchBuffer(Transaction &trans){
    for (auto it = PrefetchBuffer.begin(); it != PrefetchBuffer.end(); ++it){
        if (it->addr == trans.addr){
            return;
        }
    }
    if (PrefetchBuffer.size() >= PrefetchBuffer.capacity()){
        R_ivicte();
    }
    PrefetchEntry entry;
    entry.addr = trans.addr;
    entry.hit_count = 0;
    PrefetchBuffer.push_back(entry);
}
}