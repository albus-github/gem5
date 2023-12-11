#ifndef __CONTROLLER_H
#define __CONTROLLER_H

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

enum class RowBufPolicy { OPEN_PAGE, CLOSE_PAGE, SIZE };

class PrefetchEntry{
public:
    uint64_t addr;
    int hit_count;
};

class Controller {
   public:
#ifdef THERMAL
    Controller(int channel, const Config &config, const Timing &timing,
               ThermalCalculator &thermalcalc);
#else
    Controller(int channel, const Config &config, const Timing &timing);
#endif  // THERMAL
    void ClockTick();
    bool WillAcceptTransaction(uint64_t hex_addr, bool is_write) const;
    bool AddTransaction(Transaction trans);
    int QueueUsage() const;
    // Stats output
    void PrintEpochStats();
    void PrintFinalStats();
    void ResetStats() { simple_stats_.Reset(); }
    std::pair<uint64_t, int> ReturnDoneTrans(uint64_t clock);
    bool IsComplete(){return return_queue_.empty();}

    int channel_id_;

   private:
    uint64_t clk_;
    const Config &config_;
    SimpleStats simple_stats_;
    ChannelState channel_state_;
    CommandQueue cmd_queue_;
    Refresh refresh_;
    bool is_rw_denp_;
    std::vector<PrefetchEntry>PrefetchBuffer;
    int prefetch_total;
    int prefetch_hit;

#ifdef THERMAL
    ThermalCalculator &thermal_calc_;
#endif  // THERMAL

    // queue that takes transactions from CPU side
    bool is_unified_queue_;
    std::vector<Transaction> unified_queue_;            //读写请求共享同一队列
    std::vector<Transaction> read_queue_;
    std::vector<Transaction> write_buffer_;

    // transactions that are not completed, use map for convenience
    std::multimap<uint64_t, Transaction> pending_rd_q_;
    std::multimap<uint64_t, Transaction> pending_wr_q_;

    // completed transactions
    std::vector<Transaction> return_queue_;

    // row buffer policy
    RowBufPolicy row_buf_policy_;

#ifdef CMD_TRACE
    std::ofstream cmd_trace_;
#endif  // CMD_TRACE

    // used to calculate inter-arrival latency
    uint64_t last_trans_clk_;

    // transaction queueing
    int write_draining_;
    void ScheduleTransaction();
    void IssueCommand(const Command &tmp_cmd);
    Command TransToCommand(const Transaction &trans);
    void UpdateCommandStats(const Command &cmd);

    void W_ivicte(const Command &cmd);
    void R_ivicte();
    bool IssuePrefetch(const Command &cmd);
    Transaction GetPrefetch(const Command &cmd);
    bool PrefetchHit(uint64_t addr);
    void IssueHitTrans(Transaction &trans);
    void UpdatePrefetchBuffer(Transaction &trans);
    void AddPrefetchTrans(Transaction &trans);
};
}  // namespace dramsim3
#endif