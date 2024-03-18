import os
import sh
from os.path import join as pjoin

benchmark_code = {
    'perlbench_r': '500.perlbench_r',
    'gcc_r': '502.gcc_r',
    'bwaves_r': '503.bwaves_r',
    'mcf_r': '505.mcf_r',
    'cactuBSSN_r': '507.cactuBSSN_r',
    'namd_r': '508.namd_r',
    'parest_r': '510.parest_r',
    'povray_r': '511.povray_r',
    'lbm_r': '519.lbm_r',
    'omnetpp_r': '520.omnetpp_r',
    'wrf_r': '521.wrf_r',
    'xalancbmk_r': '523.xalancbmk_r',
    'x264_r': '525.x264_r',
    'blender_r': '526.blender_r',
    'cam4_r': '527.cam4_r',
    'deepsjeng_r': '531.deepsjeng_r',
    'imagick_r': '538.imagick_r',
    'leela_r': '541.leela_r',
    'nab_r': '544.nab_r',
    'exchange2_r': '548.exchange2_r',
    'fotonik3d_r': '549.fotonik3d_r',
    'roms_r': '554.roms_r',
    'xz_r': '557.xz_r',
    'perlbench_s': '600.perlbench_s',
    'gcc_s': '602.gcc_s',
    'bwaves_s': '603.bwaves_s',
    'mcf_s': '605.mcf_s',
    'cactuBSSN_s': '607.cactuBSSN_s',
    'lbm_s': '619.lbm_s',
    'omnetpp_s': '620.omnetpp_s',
    'wrf_s': '621.wrf_s',
    'xalancbmk_s': '623.xalancbmk_s',
    'x264_s': '625.x264_s',
    'cam4_s': '627.cam4_s',
    'pop2_s': '628.pop2_s',
    'deepsjeng_s': '631.deepsjeng_s',
    'imagick_s': '638.imagick_s',
    'leela_s': '641.leela_s',
    'nab_s': '644.nab_s',
    'exchange2_s': '648.exchange2_s',
    'fotonik3d_s': '649.fotonik3d_s',
    'roms_s': '654.roms_s',
    'xz_s': '657.xz_s',
    'specrand_fr': '997.specrand_fr',
    'specrand_ir': '999.specrand_ir',
}

def run_dir(benchmark):
    if benchmark[-1] == "r":
        return '/home/albus/spec2017/benchspec/CPU/'+benchmark_code[benchmark]+'/run/run_base_refrate_mytest-m64.0000/'
    if benchmark[-1] == "s":
        return '/home/albus/spec2017/benchspec/CPU/'+benchmark_code[benchmark]+'/run/run_base_refspeed_mytest-m64.0000/'

def avoid_repeated(func, outdir, binary=None, *args, **kwargs):
    func_name = func.__name__

    running_lock_name = 'running-{}'.format(func_name)
    running_lock_file = pjoin(outdir, running_lock_name)

    if os.path.isfile(running_lock_file):
        print('running lock found in {}, skip!'.format(outdir))
        return
    else:
        sh.touch(running_lock_file)

    ts_name = 'ts-{}'.format(func_name)
    out_ts_file = pjoin(outdir, ts_name)
    if os.path.isfile(out_ts_file):
        out_ts = os.path.getmtime(out_ts_file)
    else:
        out_ts = 0.0

    script_dir = os.path.dirname(os.path.realpath(__file__))
    script_ts_file = pjoin(script_dir, ts_name)
    if not os.path.isfile(script_ts_file):
        sh.touch(script_ts_file)

    newest = os.path.getmtime(script_ts_file)

    if not binary is None:
        binary_ts = os.path.getmtime(binary)
        newest = max(binary_ts, newest)


    if out_ts < newest:
        try:
            func(*args, **kwargs)
            sh.touch(out_ts_file)
        except Exception as e:
            print(e)
        sh.rm(running_lock_file)
    else:
        print('{} is older than {}, skip!'.format(out_ts_file,
            script_ts_file))
        if os.path.isfile(running_lock_file):
            sh.rm(running_lock_file)


def gem5_home():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    paths = script_dir.split('/')
    return '/'.join(paths[:-2])  # delete '/util/run_sh_scrpits'


def gem5_build(arch):
    return pjoin(gem5_home(), 'build/{}'.format(arch))


def gem5_exec(spec_version = '2006'):
    if spec_version == '2006':
        return os.environ['gem5_run_dir']
    elif spec_version == '2017':
        return '/home/albus/spec2017/benchspec/CPU'
    return None

def gem5_cpt_dir(arch, version=2006):
    cpt_dirs = {
            2006: {
                'ARM': '/ramdisk/zyy/gem5_run/spec-simpoint-cpt-arm-gcc-4.8',
                'RISCV': '/home/zyy/spec-simpoint-cpt-riscv-gcc-8.2',
                },
            2017: {
                'ARM': None,
                'RISCV': '/home/zyy/gem5-results/spec2017_simpoint_cpts_finished',
                'X86': '/home/albus/gem5-results/spec2017_simpoint_cpts_finished',
                },
            }
    return cpt_dirs[version][arch]

stats_base_dir = '/home/albus/gem5-results-2017'

