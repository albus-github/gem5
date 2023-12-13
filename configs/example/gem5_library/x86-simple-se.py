# Copyright (c) 2021 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This gem5 configuation script creates a simple board to run an ARM
"hello world" binary.

This is setup is the close to the simplest setup possible using the gem5
library. It does not contain any kind of caching, IO, or any non-essential
components.

Usage
-----

```
scons build/ARM/gem5.opt
./build/ARM/gem5.opt configs/example/gem5_library/arm-hello.py
```
"""

from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.resources.resource import BinaryResource
from gem5.components.memory.dramsim_3 import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.boards.x86_board_se import X86Board_se
from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.simulate.simulator import Simulator

# This check ensures the gem5 binary is compiled to the ARM ISA target. If not,
# an exception will be thrown.
requires(
	isa_required=ISA.X86,
	coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
	)

# In this setup we don't have a cache. `NoCache` can be used for such setups.
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB",
    l1d_assoc=8,
    l1i_size="16kB",
    l1i_assoc=8,
    l2_size="256kB",
    l2_assoc=16,
    num_l2_banks=1,
)

# We use a single channel DDR3_1600 memory system
memory = SingleChannelDDR3_1600(size="3GB")

# We use a simple Timing processor with one core.
processor = SimpleProcessor(cpu_type=CPUTypes.O3, isa=ISA.X86, num_cores=1)

# The gem5 library simble board which can be used to run simple SE-mode
# simulations.
board = X86Board_se(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Here we set the workload. In this case we want to run a simple "Hello World!"
# program compiled to the ARM ISA. The `Resource` class will automatically
# download the binary from the gem5 Resources cloud bucket if it's not already
# present.
board.set_se_binary_workload(
    # The `Resource` class reads the `resources.json` file from the gem5
    # resources repository:
    # https://github.com/gem5/gem5-resources.
    # Any resource specified in this file will be automatically retrieved.
    # At the time of writing, this file is a WIP and does not contain all
    # resources. Jira ticket: https://gem5.atlassian.net/browse/GEM5-1096
    BinaryResource("/home/albus/spec2017/benchspec/CPU/531.deepsjeng_r/run/run_base_refrate_mytest-m64.0000/deepsjeng_r_base.mytest-m64")
)

# Lastly we run the simulation.
simulator = Simulator(board=board)
simulator.run()

print(
    "Exiting @ tick {} because {}.".format(
        simulator.get_current_tick(), simulator.get_last_exit_event_cause()
    )
)
