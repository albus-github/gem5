#include <fstream>
#include <map>
#include <unordered_set>
#include <vector>
#include <unordered_map>
#include "configuration.h"
#include "common.h"

#ifdef THERMAL
#include "thermal.h"
#endif  // THERMAL

namespace dramsim3 {

struct PrefetchEntry{
    uint64_t addr;
    int hit_count;
    uint64_t add_cycle;
};

class Prefetcher
{
public:
    Prefetcher():prefetch_total(0), prefetch_hit(0), PrefetchBuffer(32){}
    ~Prefetcher(){}
    
    int prefetch_total;
    int prefetch_hit;
    std::vector<PrefetchEntry>PrefetchBuffer;

    virtual void W_ivicte(const Command &cmd);
    virtual uint64_t R_ivicte(uint64_t clk);
    virtual void UpdatePrefetchBuffer(Transaction &trans, uint64_t clk);
};

class NextLine_Prefetcher : public Prefetcher { 
public:
    NextLine_Prefetcher() : Prefetcher() {}
    ~NextLine_Prefetcher(){};

    int distance = 5;
    bool IssuePrefetch(const Transaction &trans);
    Transaction GetPrefetch(const Transaction &trans);
};

struct trans_info {
    int tag;
    uint64_t hex_addr;
    Address addr;
};

struct ST_entry {
    int tag;
    int last_offset;
    uint16_t signature;
};

class Signature_Table {
private:
    std::vector<ST_entry>SignatureTable;

public:
    void update(trans_info info, int delta);
    uint16_t getsignature(trans_info info);
    int getdelta(trans_info info);
    uint16_t newsignature(uint16_t signature, int delta);
};

struct delta_entry {
    int delta;
    int c_delta;
};

struct PT_entry {
    std::vector<delta_entry> delta;
    int c_sig;
};

struct prefetch_info{
    int delta;
    double p;
};

class Pattern_Table {
private:
    std::unordered_map<uint16_t,PT_entry>PatternTable;

public:
    void update(uint16_t index, int delta);
    prefetch_info prefetch_delta(uint16_t signature);

};

class Prefetch_Filter {
public:
    std::unordered_map<uint64_t, int>PrefetchFilter;

    void add_entry(uint64_t addr);
    void ivicte_entry(uint64_t addr);
    void update_useful(const Transaction &trans);
};

class SPP_Prefetcher : public Prefetcher {
private:
    const Config &config_;

public:
    SPP_Prefetcher(const Config &config) : Prefetcher(), config_(config) {}
    ~SPP_Prefetcher(){};

    Signature_Table ST;
    Pattern_Table PT;
    Prefetch_Filter PF;

    double Tp = 0.25;
    double P = 1;
    double a = 0.8;
    uint16_t sig;
    prefetch_info prefetch_delta;
    Transaction prefetch_trans;

    void GetPrefetch(uint16_t signaure);
    bool IssuePrefetch(const Transaction &trans);
    void updateSTandPT(trans_info info);
    trans_info get_info(const Transaction &trans);
    void UpdatePrefetchBuffer(Transaction &trans, uint64_t clk) override;
};

}