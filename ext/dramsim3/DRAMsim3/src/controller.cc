#include "controller.h"
#include <iomanip>
#include <iostream>
#include <limits>
#include "../../../../../../../usr/include/c++/11/bits/ios_base.h"

namespace dramsim3 {

#ifdef THERMAL          //memtory controller的基础配置
Controller::Controller(int channel, const Config &config, const Timing &timing,
                       ThermalCalculator &thermal_calc)
#else
Controller::Controller(int channel, const Config &config, const Timing &timing)         //channel（通道数量），config（配置，包括DRAM 参数和一些管理策略（协议？，地质映射）），Timing（DRAM 的时序约束）
#endif  // THERMAL
    : channel_id_(channel),         //channel传递给channel_id
      clk_(0),
      config_(config),
      simple_stats_(config_, channel_id_),          //根据配置和通道设置状态机
      channel_state_(config, timing),           //根据配置和时序约束设置通道的状态
      cmd_queue_(channel_id_, config, channel_state_, simple_stats_),
      refresh_(config, channel_state_),
      is_rw_denp_(false),
      PrefetchBuffer(32),
      prefetch_total(0),
      prefetch_hit(0),
#ifdef THERMAL
      thermal_calc_(thermal_calc),
#endif  // THERMAL
      is_unified_queue_(config.unified_queue),
      row_buf_policy_(config.row_buf_policy == "CLOSE_PAGE"         //设置page policy，应该也是在config中设计
                          ? RowBufPolicy::CLOSE_PAGE
                          : RowBufPolicy::OPEN_PAGE),
      last_trans_clk_(0),
      write_draining_(0) {
    if (is_unified_queue_) {            //设置请求队列的大小，应该也是在config中设计
        unified_queue_.reserve(config_.trans_queue_size);
    } else {
        read_queue_.reserve(config_.trans_queue_size);
        write_buffer_.reserve(config_.trans_queue_size);
    }

#ifdef CMD_TRACE
    std::string trace_file_name = config_.output_prefix + "ch_" +
                                  std::to_string(channel_id_) + "cmd.trace";
    std::cout << "Command Trace write to " << trace_file_name << std::endl;
    cmd_trace_.open(trace_file_name, std::ofstream::out);
#endif  // CMD_TRACE
}

std::pair<uint64_t, int> Controller::ReturnDoneTrans(uint64_t clk) {
    auto it = return_queue_.begin();
    while (it != return_queue_.end()) {
        if (clk >= it->complete_cycle) {
            std::cout<<"Addr: "<<it->addr<<", "<<"Add_ cycle: "<<it->added_cycle<<", "<<"complete_cycle: "<<it->complete_cycle<<", "<<"IsPrefetch: "<<it->IsPrefetch<<std::endl;
            if (it->IsPrefetch){
                UpdatePrefetchBuffer(*it);
                it = return_queue_.erase(it);
                return std::make_pair(-1, -1);
            } else {
                if (it->is_write) {
                    simple_stats_.Increment("num_writes_done");
                } else {
                    simple_stats_.Increment("num_reads_done");
                    simple_stats_.AddValue("read_latency", clk_ - it->added_cycle);
                }
                auto pair = std::make_pair(it->addr, it->is_write);
                it = return_queue_.erase(it);
                return pair;
            }
        } else {
            ++it;
        }
    }
    return std::make_pair(-1, -1);
}

void Controller::ClockTick() {
    // update refresh counter
    refresh_.ClockTick();

    bool cmd_issued = false;
    //std::cout<<"Nember of trans in the return_queue: "<<return_queue_.size()<<", "<<clk_<<std::endl;
    Command cmd;
    if (channel_state_.IsRefreshWaiting()) {
        cmd = cmd_queue_.FinishRefresh();
    }

    // cannot find a refresh related command or there's no refresh
    if (!cmd.IsValid()) {
        cmd = cmd_queue_.GetCommandToIssue();
        std::string cmd_type;
        switch(cmd.cmd_type){
            case CommandType::ACTIVATE: cmd_type = "ACTIVE"; break;
            case CommandType::PRECHARGE: cmd_type = "PRECHARGE"; break;
            case CommandType::READ: cmd_type = "READ"; break;
            case CommandType::WRITE: cmd_type = "WRITE"; break;
            default: cmd_type = " ";
        }
        //std::cout<<"GetCommand: "<<cmd_type<<", "<<"Addr: "<<cmd.addr.bankgroup<<", "<<cmd.addr.bank<<", "<<cmd.addr.row<<", "<<cmd.addr.column<<", "<<"Cycle: "<<clk_<<std::endl;
    }

    if (cmd.IsValid()) {
        std::string cmd_type;
        switch(cmd.cmd_type){
            case CommandType::ACTIVATE: cmd_type = "ACTIVE"; break;
            case CommandType::PRECHARGE: cmd_type = "PRECHARGE"; break;
            case CommandType::READ: cmd_type = "READ"; break;
            case CommandType::WRITE: cmd_type = "WRITE"; break;
            default: cmd_type = " ";
        }
        std::cout<<"IssueCommand: "<<cmd_type<<", "<<"Addr: "<<cmd.hex_addr<<", "<<cmd.addr.bankgroup<<", "<<cmd.addr.bank<<", "<<cmd.addr.row<<", "<<cmd.addr.column<<", "<<"Cycle: "<<clk_<<std::endl;
        if (IssuePrefetch(cmd)){
            Transaction Prefetch_trans=GetPrefetch(cmd);
            AddPrefetchTrans(Prefetch_trans);
        }
        if (cmd.cmd_type == CommandType::WRITE || cmd.cmd_type == CommandType::WRITE_PRECHARGE){
            W_ivicte(cmd);
        }
        IssueCommand(cmd);
        cmd_issued = true;

        if (config_.enable_hbm_dual_cmd) {
            auto second_cmd = cmd_queue_.GetCommandToIssue();
            if (second_cmd.IsValid()) {
                if (second_cmd.IsReadWrite() != cmd.IsReadWrite()) {
                    IssueCommand(second_cmd);
                    simple_stats_.Increment("hbm_dual_cmds");
                }
            }
        }
    }

    // power updates pt 1
    for (int i = 0; i < config_.ranks; i++) {
        if (channel_state_.IsRankSelfRefreshing(i)) {
            simple_stats_.IncrementVec("sref_cycles", i);
        } else {
            bool all_idle = channel_state_.IsAllBankIdleInRank(i);
            if (all_idle) {
                simple_stats_.IncrementVec("all_bank_idle_cycles", i);
                channel_state_.rank_idle_cycles[i] += 1;
            } else {
                simple_stats_.IncrementVec("rank_active_cycles", i);
                // reset
                channel_state_.rank_idle_cycles[i] = 0;
            }
        }
    }

    // power updates pt 2: move idle ranks into self-refresh mode to save power
    if (config_.enable_self_refresh && !cmd_issued) {
        for (auto i = 0; i < config_.ranks; i++) {
            if (channel_state_.IsRankSelfRefreshing(i)) {
                // wake up!
                if (!cmd_queue_.rank_q_empty[i]) {
                    auto addr = Address();
                    addr.rank = i;
                    auto cmd = Command(CommandType::SREF_EXIT, addr, -1, false);
                    cmd = channel_state_.GetReadyCommand(cmd, clk_);
                    if (cmd.IsValid()) {
                        IssueCommand(cmd);
                        break;
                    }
                }
            } else {
                if (cmd_queue_.rank_q_empty[i] &&
                    channel_state_.rank_idle_cycles[i] >=
                        config_.sref_threshold) {
                    auto addr = Address();
                    addr.rank = i;
                    auto cmd = Command(CommandType::SREF_ENTER, addr, -1, false);
                    cmd = channel_state_.GetReadyCommand(cmd, clk_);
                    if (cmd.IsValid()) {
                        IssueCommand(cmd);
                        break;
                    }
                }
            }
        }
    }

    ScheduleTransaction();
    std::cout<<"Issue Prefetch: "<<prefetch_total<<", "<<"Prefetch hit: "<<prefetch_hit<<std::endl;
    clk_++;
    cmd_queue_.ClockTick();
    simple_stats_.Increment("num_cycles");
    return;
}

bool Controller::WillAcceptTransaction(uint64_t hex_addr, bool is_write) const {
    if (is_unified_queue_) {
        return unified_queue_.size() < unified_queue_.capacity();
    } else if (!is_write) {
        return read_queue_.size() < read_queue_.capacity();
    } else {
        return write_buffer_.size() < write_buffer_.capacity();
    }
}

bool Controller::AddTransaction(Transaction trans) {
    trans.IsPrefetch = false;
    trans.added_cycle = clk_;
    simple_stats_.AddValue("interarrival_latency", clk_ - last_trans_clk_);
    last_trans_clk_ = clk_;

    if (trans.is_write) {
        if (pending_wr_q_.count(trans.addr) == 0) {  // can not merge writes
            pending_wr_q_.insert(std::make_pair(trans.addr, trans));
            if (is_unified_queue_) {
                unified_queue_.push_back(trans);
            } else {
                write_buffer_.push_back(trans);
            }
        //std::cout<<"Addr: "<<trans.addr<<", "<<"AddTrans cycle: "<<clk_<<std::endl;
        }
        trans.complete_cycle = clk_ + 1;
        return_queue_.push_back(trans);
        return true;
    } else {  // read
        // if in write buffer, use the write buffer value
        if (pending_wr_q_.count(trans.addr) > 0) {
            trans.complete_cycle = clk_ + 1;
            return_queue_.push_back(trans);
            return true;
        }
        pending_rd_q_.insert(std::make_pair(trans.addr, trans));
        if (pending_rd_q_.count(trans.addr) == 1) {
            if (is_unified_queue_) {
                unified_queue_.push_back(trans);
            } else {
                read_queue_.push_back(trans);
            }
        }
        std::cout<<"Addr: "<<trans.addr<<", "<<"AddTrans cycle: "<<clk_<<std::endl;
        return true;
    }
}

void Controller::ScheduleTransaction() {
    // determine whether to schedule read or write
    if (is_rw_denp_ == false && write_draining_ == 0 && !is_unified_queue_) {
        // we basically have a upper and lower threshold for write buffer
        if ((write_buffer_.size() >= write_buffer_.capacity()) ||
            (write_buffer_.size() > 8 && cmd_queue_.QueueEmpty())) {
            write_draining_ = write_buffer_.size();
        }
    }

    std::vector<Transaction> &queue =
        is_unified_queue_ ? unified_queue_
                          : write_draining_ > 0 ? write_buffer_ : read_queue_;
    for (auto it = queue.begin(); it != queue.end(); it++) {
        if (PrefetchHit(it->addr)){
            IssueHitTrans(*it);
            queue.erase(it);
            break;
        }
        else{
          auto cmd = TransToCommand(*it);
          if (cmd_queue_.WillAcceptCommand(cmd.Rank(), cmd.Bankgroup(),
                                             cmd.Bank())) {
                if (!is_unified_queue_ && cmd.IsWrite()) {
                    // Enforce R->W dependency
                 if (pending_rd_q_.count(it->addr) > 0) {
                        write_draining_ = 0;
                        is_rw_denp_ = true;
                        break;
                    }
                 write_draining_ -= 1;
                }
                is_rw_denp_ = false;
                cmd_queue_.AddCommand(cmd);
                queue.erase(it);
                break;
            }
        }
    }
}

void Controller::IssueCommand(const Command &cmd) {
#ifdef CMD_TRACE
    cmd_trace_ << std::left << std::setw(18) << clk_ << " " << cmd << std::endl;
#endif  // CMD_TRACE
#ifdef THERMAL
    // add channel in, only needed by thermal module
    thermal_calc_.UpdateCMDPower(channel_id_, cmd, clk_);
#endif  // THERMAL
    // if read/write, update pending queue and return queue
    if (cmd.IsRead()) {
        auto num_reads = pending_rd_q_.count(cmd.hex_addr);
        if (num_reads == 0) {
            std::cerr << cmd.hex_addr << " not in read queue! " << std::endl;
            exit(1);
        }
        // if there are multiple reads pending return them all         将pending_rd_q中访问相同地址的命令一起发送
        while (num_reads > 0) {
            auto it = pending_rd_q_.find(cmd.hex_addr);
            it->second.complete_cycle = clk_ + config_.read_delay;
            return_queue_.push_back(it->second);
            pending_rd_q_.erase(it);
            num_reads -= 1;
        }
    } else if (cmd.IsWrite()) {
        // there should be only 1 write to the same location at a time
        auto it = pending_wr_q_.find(cmd.hex_addr);
        if (it == pending_wr_q_.end()) {
            std::cerr << cmd.hex_addr << " not in write queue!" << std::endl;
            exit(1);
        }
        auto wr_lat = clk_ - it->second.added_cycle + config_.write_delay;
        simple_stats_.AddValue("write_latency", wr_lat);
        pending_wr_q_.erase(it);
    }
    // must update stats before states (for row hits)
    UpdateCommandStats(cmd);
    channel_state_.UpdateTimingAndStates(cmd, clk_);
}

Command Controller::TransToCommand(const Transaction &trans) {
    auto addr = config_.AddressMapping(trans.addr);
    bool IsPrefetch = trans.IsPrefetch;
    CommandType cmd_type;
    if (row_buf_policy_ == RowBufPolicy::OPEN_PAGE) {
        cmd_type = trans.is_write ? CommandType::WRITE : CommandType::READ;
    } else {
        cmd_type = trans.is_write ? CommandType::WRITE_PRECHARGE
                                  : CommandType::READ_PRECHARGE;
    }
    return Command(cmd_type, addr, trans.addr, IsPrefetch);
}

int Controller::QueueUsage() const { return cmd_queue_.QueueUsage(); }

void Controller::PrintEpochStats() {
    simple_stats_.Increment("epoch_num");
    simple_stats_.PrintEpochStats();
#ifdef THERMAL
    for (int r = 0; r < config_.ranks; r++) {
        double bg_energy = simple_stats_.RankBackgroundEnergy(r);
        thermal_calc_.UpdateBackgroundEnergy(channel_id_, r, bg_energy);
    }
#endif  // THERMAL
    return;
}

void Controller::PrintFinalStats() {
    simple_stats_.PrintFinalStats();

#ifdef THERMAL
    for (int r = 0; r < config_.ranks; r++) {
        double bg_energy = simple_stats_.RankBackgroundEnergy(r);
        thermal_calc_.UpdateBackgroundEnergy(channel_id_, r, bg_energy);
    }
#endif  // THERMAL
    return;
}

void Controller::UpdateCommandStats(const Command &cmd) {                   //仅仅起统计次数的作用？
    switch (cmd.cmd_type) {
        case CommandType::READ:
        case CommandType::READ_PRECHARGE:
            simple_stats_.Increment("num_read_cmds");
            if (channel_state_.RowHitCount(cmd.Rank(), cmd.Bankgroup(),
                                           cmd.Bank()) != 0) {
                simple_stats_.Increment("num_read_row_hits");
            }
            break;
        case CommandType::WRITE:
        case CommandType::WRITE_PRECHARGE:
            simple_stats_.Increment("num_write_cmds");
            if (channel_state_.RowHitCount(cmd.Rank(), cmd.Bankgroup(),
                                           cmd.Bank()) != 0) {
                simple_stats_.Increment("num_write_row_hits");
            }
            break;
        case CommandType::ACTIVATE:
            simple_stats_.Increment("num_act_cmds");
            break;
        case CommandType::PRECHARGE:
            simple_stats_.Increment("num_pre_cmds");
            break;
        case CommandType::REFRESH:
            simple_stats_.Increment("num_ref_cmds");
            break;
        case CommandType::REFRESH_BANK:
            simple_stats_.Increment("num_refb_cmds");
            break;
        case CommandType::SREF_ENTER:
            simple_stats_.Increment("num_srefe_cmds");
            break;
        case CommandType::SREF_EXIT:
            simple_stats_.Increment("num_srefx_cmds");
            break;
        default:
            AbruptExit(__FILE__, __LINE__);
    }
}

//Maintain data consistency when write new datas in the same address of the entry in the prefetch-buffer
void Controller::W_ivicte(const Command &cmd){
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
void Controller::R_ivicte(){
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
bool Controller::IssuePrefetch(const Command &cmd){
    if (!cmd.IsPrefetch){
        if (cmd.cmd_type == CommandType::READ){
        return true;
        }
    }
    return false;
}

//Get the Perfetch command
Transaction Controller::GetPrefetch(const Command &cmd){
    Transaction Prefetch;
    Prefetch.addr = cmd.hex_addr+64;
    Prefetch.IsPrefetch = true;
    Prefetch.is_write = false;
    Prefetch.added_cycle = clk_;
    Prefetch.complete_cycle = clk_+1;
    prefetch_total++;
    std::cout<<"Prefetch Addr: "<<Prefetch.addr<<std::endl;
    return  Prefetch;
}

bool Controller::PrefetchHit(uint64_t addr){
    for (auto it = PrefetchBuffer.begin(); it != PrefetchBuffer.end(); it++){
        if (addr == it->addr){
            if (it->hit_count == 0){
                prefetch_hit++;
            }
            it->hit_count++;
            return true;
        }
    }
    return false;
}

void Controller::IssueHitTrans(Transaction &trans){
    trans.complete_cycle = clk_ + config_.burst_cycle;
    return_queue_.push_back(trans);
    auto it = pending_rd_q_.begin();
    while (it != pending_rd_q_.end()) {
        if (it->second.addr == trans.addr && it->second.added_cycle == trans.added_cycle){
            it = pending_rd_q_.erase(it);
        } else {
            it++;
        }
    }
}

void Controller::AddPrefetchTrans(Transaction &trans){
    pending_rd_q_.insert(std::make_pair(trans.addr, trans));
    if (pending_rd_q_.count(trans.addr) == 1) {
        if (is_unified_queue_) {
            unified_queue_.push_back(trans);
        } else {
            read_queue_.push_back(trans);
        }
    }
}

void Controller::UpdatePrefetchBuffer(Transaction &trans){
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
}  // namespace dramsim3