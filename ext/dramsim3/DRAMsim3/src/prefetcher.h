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

struct PF_entry{
    int valid;
    int useful;
};

class Prefetch_Filter {
public:
    std::unordered_map<uint64_t, PF_entry>PrefetchFilter;

    void add_entry(uint64_t addr);
    void ivicte_entry(uint64_t addr);
    bool update_useful(uint64_t addr);
    void update_valid();
    bool hit(uint64_t addr);

friend class Prefetch_Buffer;
};

struct PrefetchEntry{
    uint64_t addr;
    int hit_count;
    int valid;
    int life;
};

class Prefetch_Buffer {
private:
    std::list<PrefetchEntry*> l;
    std::unordered_map<uint64_t, std::list<PrefetchEntry*>::iterator> m;
    int capacity;

public:
    Prefetch_Buffer(int capacity) {
        this->capacity = capacity;
    }

    void set(uint64_t addr, Prefetch_Filter PF);
    void ivicte(uint64_t addr);
    bool hit(uint64_t addr);
    void epoch_update(Prefetch_Filter PF);
    int prefetch_latency(uint64_t addr);
};

struct trans_info {
    int tag;
    uint64_t hex_addr;
    Address addr;
};

struct sb_entry {
    int tag;
    uint64_t addr;
    int delta;
};

class global_history_register {
public:    
    std::unordered_map<int, std::pair<uint64_t, int>> ghr;

    void update_ghr(int tag, uint64_t addr, int delta);
    int search_ghr(int tag, uint64_t addr);
};

class stream_buffer {
private:
    std::list<sb_entry> stream_buffer;
    global_history_register ghr;
    int capacity;

public:
    int delta[8];
    void update(uint16_t tag, uint64_t addr);
    void get_delta(uint16_t tag);
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
public:
    std::unordered_map<uint16_t,PT_entry>PatternTable;
    void update(uint16_t index, int delta);
    void updatesig(uint16_t index);
    prefetch_info prefetch_delta(uint16_t signature);

};

struct History_Table_entry {
    uint16_t tag;
    uint64_t addr;
    History_Table_entry* next;
    History_Table_entry () = default;
    History_Table_entry (uint16_t tag, uint64_t addr) : tag(tag), addr(addr), next(nullptr) {}
};

class History_Table {
public:
    History_Table(int group, int way);
    History_Table_entry** HistoryTable;
    int way;
    int group;
    int count[8];
    int64_t *delta;
    void update_historytable(uint16_t tag, uint64_t addr);
    void get_delta(uint16_t tag, uint64_t addr);
};

class Delta_Table :public Pattern_Table{
public:
    std::vector<int> prefetch_delta;
    void update_coverage();
    void get_delta(uint16_t tag);
    void update_capacity(int distance);
};

class Time_Table {
public:
    std::unordered_map<uint64_t, uint64_t> TimeTable;
    int capacity = 16;

    void update(Transaction &trans);
};

struct timestamp {
    double arrival_latency;
    double fetch_latency;
    int num_arrival;
    int num_fetch;
};

class Latency_Table {
private:
    std::unordered_map<int, timestamp> LatencyTable;
    Time_Table TT;
    timestamp time;

public:
    void update_arrival(Transaction &trans);
    void update_fetch(Transaction &trans);
    bool Istimely(const Transaction &trans, Transaction &prefetch_trans);
};

struct epoch_info{
    int epoch_total;
    int epoch_hit;
    int epoch_read_done;
    int epoch_trans_num;
    int last_trans_num;
    double epoch_read_latency;
    double last_read_latency;
    double epoch_a;

    epoch_info()
        : epoch_total(0),
          epoch_hit(0),
          epoch_read_done(0),
          epoch_trans_num(0),
          last_trans_num(0),
          epoch_read_latency(0.0),
          last_read_latency(0.0),
          epoch_a(0.0) {}
};

class Prefetcher
{
public:
    Prefetcher(const Config &config, double Tl, double Th, int distance, int max_distance):
    prefetch_total(0),
    prefetch_hit(0),
    i(0),
    PrefetchBuffer(128),
    config_(config),
    Tl(Tl),
    Th(Th),
    distance(distance),
    max_distance(max_distance),
    epoch_stats()
    {}
    ~Prefetcher(){}

    double Tl;
    double Th;
    int prefetch_total;
    int prefetch_hit;
    int distance;
    int max_distance;
    int i;

    Transaction prefetch_trans;
    Prefetch_Buffer PrefetchBuffer;
    Prefetch_Filter PF;
    Latency_Table LT;
    epoch_info epoch_stats;
    const Config &config_;

    virtual void W_ivicte(uint64_t addr);
    virtual void UpdatePrefetchBuffer(Transaction &trans);
    virtual bool PrefetchHit(uint64_t addr);
    virtual bool IssuePrefetch(const Transaction &trans, Transaction &prefetch_trans); //prefetch filter
    virtual void Updatea_epoch_info();
    virtual void Updatelatency(Transaction &trans, uint64_t clk);
    virtual void UpdateaDistance();
    virtual void initial(const Transaction &trans);
    virtual bool Continue();
    virtual Transaction GetPrefetch()=0;
    trans_info get_info(const Transaction &trans);
    int get_tag(uint64_t addr);
    uint16_t get_tag_uint16(uint64_t addr);
};

class NextLine_Prefetcher : public Prefetcher {
public:
    NextLine_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.75, 1, 10) {}
    ~NextLine_Prefetcher(){};
    
    Transaction GetPrefetch() override;
};

class Stream_Prefetcher : public Prefetcher {
public:
    Stream_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.5, 5, 8) {}
    ~Stream_Prefetcher(){};
    
    stream_buffer Stream_buffer;
    uint16_t tag;
    Transaction GetPrefetch() override;
    void initial(const Transaction &trans) override;
};

class SPP_Prefetcher : public Prefetcher {
public:
    SPP_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.5, 3, 10) {}
    ~SPP_Prefetcher(){};

    Signature_Table ST;
    Pattern_Table PT;

    double P = 1;
    double a = 0.8;
    uint16_t sig;
    prefetch_info prefetch_delta;

    Transaction GetPrefetch() override;
    //bool IssuePrefetch(const Transaction &trans, Transaction &prefetch_trans) override;
    void updateSTandPT(trans_info info);
    void UpdateaDistance() override;
    void initial(const Transaction &trans) override;
    bool Continue() override;
};

class Delta_Prefetcher : public Prefetcher {
public:
    Delta_Prefetcher(const Config &config) : Prefetcher(config, 0.25, 0.5, 3, 8), HT(History_Table(8, 16)){}
    ~Delta_Prefetcher(){};

    uint16_t tag;
    Delta_Table DT;
    History_Table HT;

    void initial(const Transaction &trans) override;
    void update(uint16_t tag, uint64_t addr);
    Transaction GetPrefetch() override;
    void UpdateaDistance() override;
};
}