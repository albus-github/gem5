#include <fstream>
#include <map>
#include <list>
#include <unordered_set>
#include <vector>
#include <unordered_map>
#include "configuration.h"
#include "common.h"

#ifdef THERMAL
#include "thermal.h"
#endif  // THERMAL

namespace dramsim3 {

class Prefetch_Filter {
public:
    std::unordered_map<uint64_t, int>PrefetchFilter;

    void add_entry(uint64_t addr);
    void ivicte_entry(uint64_t addr);
    void update_useful(uint64_t addr);

friend class Prefetch_Buffer;
};

struct PrefetchEntry{
    uint64_t addr;
    int hit_count;
};

class Prefetch_Buffer {
private:
    std::list<PrefetchEntry*> l; // 双向链表
    std::unordered_map<uint64_t, std::list<PrefetchEntry*>::iterator> m; // 哈希表
    int capacity;

public:
    Prefetch_Buffer(int capacity) { // 构造函数
        this->capacity = capacity;
        l.push_back(new PrefetchEntry()); // 初始化空列表
    }

    void set(uint64_t addr, Prefetch_Filter PF);
    void ivicte(uint64_t addr);
    int hit(uint64_t addr);
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

class Prefetcher
{
public:
    Prefetcher(const Config &config, double Tl, double Th, int distance):
    prefetch_total(0),
    prefetch_hit(0),
    epoch_total(0),
    epoch_hit(0),
    PrefetchBuffer(32),
    config_(config),
    Tl(Tl),
    Th(Th),
    distance(distance)
    {}
    ~Prefetcher(){}

    double Tl;
    double Th;
    int prefetch_total;
    int prefetch_hit;
    double epoch_total;
    double epoch_hit;
    int distance;

    Transaction prefetch_trans;
    Prefetch_Buffer PrefetchBuffer;
    Prefetch_Filter PF;
    const Config &config_;

    virtual void W_ivicte(uint64_t addr);
    virtual void UpdatePrefetchBuffer(Transaction &trans);
    virtual bool PrefetchHit(uint64_t addr);
    virtual bool IssuePrefetch(const Transaction &trans, Transaction &prefetch_trans);
    virtual double Updatea();
    virtual void UpdateaDistance();
};

class NextLine_Prefetcher : public Prefetcher {
public:
    NextLine_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.75, 5) {}
    ~NextLine_Prefetcher(){};
    
    void GetPrefetch();
};

class SPP_Prefetcher : public Prefetcher {
public:
    SPP_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.75, 5) {}
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
    bool IssuePrefetch(const Transaction &trans, Transaction &prefetch_trans) override;
    void updateSTandPT(trans_info info);
    trans_info get_info(const Transaction &trans);
    //void UpdateaDistance() override;
};

}