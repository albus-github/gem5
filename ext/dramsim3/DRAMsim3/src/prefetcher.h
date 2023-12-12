#include <fstream>
#include <map>
#include <unordered_set>
#include <vector>
#include "channel_state.h"
#include "command_queue.h"
#include "common.h"
#include "refresh.h"
#include "simple_stats.h"

#ifdef THERMAL
#include "thermal.h"
#endif  // THERMAL

namespace dramsim3 {

class PrefetchEntry{
public:
    uint64_t addr;
    int hit_count;
};

class Prefetcher
{
public:
    Prefetcher():prefetch_total(0), prefetch_hit(0){}
    ~Prefetcher(){}
    std::vector<PrefetchEntry>PrefetchBuffer;
    int prefetch_total;
    int prefetch_hit;

    virtual void W_ivicte(const Command &cmd) = 0;
    virtual void R_ivicte() = 0;
    virtual bool IssuePrefetch(const Command &cmd) = 0;
    virtual Transaction GetPrefetch(const Command &cmd) = 0;
    virtual void UpdatePrefetchBuffer(Transaction &trans) = 0;
};

class NextLine_Prefetcher : public Prefetcher { 
public:
    NextLine_Prefetcher() : Prefetcher() {}
    ~NextLine_Prefetcher(){};
    void W_ivicte(const Command &cmd) override;
    void R_ivicte() override;
    bool IssuePrefetch(const Command &cmd) override;
    Transaction GetPrefetch(const Command &cmd) override;
    void UpdatePrefetchBuffer(Transaction &trans) override;
};

}