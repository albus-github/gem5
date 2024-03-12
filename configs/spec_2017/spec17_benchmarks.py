import m5
from m5.objects import *

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


#500.perlbench_r 
perlbench_r = Process(pid = 500) 
perlbench_r.executable = run_dir('perlbench_r')+'perlbench_r_base.mytest-m64'
data = run_dir('perlbench_r')+'checkspam.pl'
perlbench_r.cmd = [perlbench_r.executable] + ['-I'+run_dir('perlbench_r')+'lib',data,'2500','5','25','11','150','1','1','1','1']

#600.perlbench_s 
perlbench_s = Process(pid = 600)
perlbench_s.executable = run_dir('perlbench_s')+'perlbench_s_base.mytest-m64'
data = run_dir('perlbench_s')+'checkspam.pl'
perlbench_s.cmd = [perlbench_s.executable] + ['-I'+run_dir('perlbench_s')+'lib',data,'2500','5','25','11','150','1','1','1','1']

#502.gcc_r 
gcc_r = Process(pid = 502)
gcc_r.executable =  run_dir('gcc_r')+'cpugcc_r_base.mytest-m64'
gcc_r.cmd = [gcc_r.executable] + [run_dir('gcc_r')+'gcc-pp.c','-O3','-finline-limit=0','-fif-conversion','-fif-conversion2','-o','gcc-pp.opts-O3_-finline-limit_0_-fif-conversion_-fif-conversion2.s']

#602.gcc_s 
gcc_s = Process(pid = 602)
gcc_s.executable =  run_dir('gcc_s')+'sgcc_base.mytest-m64'
gcc_s.cmd = [gcc_s.executable] + [run_dir('gcc_s')+'gcc-pp.c','-O5','-fipa-pta','-o','gcc-pp.opts-O5_-fipa-pta.s']

#505.mcf_r
mcf_r = Process(pid = 505) 
mcf_r.executable = run_dir('mcf_r')+'mcf_r_base.mytest-m64'
data = run_dir('mcf_r')+'inp.in'
mcf_r.cmd = [mcf_r.executable] + [data]

#605.mcf_s 
mcf_s = Process(pid = 605) 
mcf_s.executable = run_dir('mcf_s')+'mcf_s_base.mytest-m64'
data = run_dir('mcf_s')+'inp.in'
mcf_s.cmd = [mcf_s.executable] + [data]

#520.omnetpp_r 
omnetpp_r = Process(pid = 520) 
omnetpp_r.executable = run_dir('omnetpp_r')+'omnetpp_r_base.mytest-m64'
# omnetpp_r.cmd = [omnetpp_r.executable]+['-c General','-r 0']
omnetpp_r.cmd = [omnetpp_r.executable]+['-c', 'General', '-r', '0']

#620.omnetpp_s 
omnetpp_s = Process(pid = 620) 
omnetpp_s.executable = run_dir('omnetpp_s')+'omnetpp_s_base.mytest-m64'
# omnetpp_s.cmd = [omnetpp_s.executable]+['-c General','-r 0']
omnetpp_s.cmd = [omnetpp_s.executable]+['-c', 'General', '-r', '0']

#523.xalancbmk_r  
xalancbmk_r = Process(pid = 523) 
xalancbmk_r.executable =  run_dir('xalancbmk_r')+'cpuxalan_r_base.mytest-m64'
xalancbmk_r.cmd = [xalancbmk_r.executable] + ['-v',run_dir('xalancbmk_r')+'t5.xml',run_dir('xalancbmk_r')+'xalanc.xsl']

#623.xalancbmk_s  
xalancbmk_s = Process(pid = 623) 
xalancbmk_s.executable = run_dir('xalancbmk_s')+'xalancbmk_s_base.mytest-m64'
xalancbmk_s.cmd = [xalancbmk_s.executable] + ['-v',run_dir('xalancbmk_s')+'t5.xml',run_dir('xalancbmk_s')+'xalanc.xsl']

#525.x264_r   
x264_r = Process(pid = 525) 
x264_r.executable = run_dir('x264_r')+'x264_r_base.mytest-m64'
x264_r.cmd = [x264_r.executable] + ['--pass','1','--stats','x264_stats.log','--bitrate','1000','--frames','1000','-o','BuckBunny_New.264','BuckBunny.yuv','1280x720']

#625.x264_s   
x264_s = Process(pid = 625) 
x264_s.executable = run_dir('x264_s')+'x264_s_base.mytest-m64'
x264_s.cmd = [x264_s.executable] + ['--pass','1','--stats','x264_stats.log','--bitrate','1000','--frames','1000','-o','BuckBunny_New.264','BuckBunny.yuv','1280x720']

#531.deepsjeng_r 
deepsjeng_r = Process(pid = 531) 
deepsjeng_r.executable = run_dir('deepsjeng_r')+'deepsjeng_r_base.mytest-m64'
deepsjeng_r.cmd = [deepsjeng_r.executable] + [run_dir('deepsjeng_r')+'ref.txt']

#631.deepsjeng_s  
deepsjeng_s = Process(pid = 631) 
deepsjeng_s.executable = run_dir('deepsjeng_s')+'deepsjeng_s_base.mytest-m64'
deepsjeng_s.cmd = [deepsjeng_s.executable] + [run_dir('deepsjeng_s')+'ref.txt']

#541.leela_r  
leela_r = Process(pid = 541) 
leela_r.executable = run_dir('leela_r')+'leela_r_base.mytest-m64'
data = run_dir('leela_r')+'ref.sgf'
leela_r.cmd = [leela_r.executable] + [data]

#641.leela_s  
leela_s = Process(pid = 641) 
leela_s.executable = run_dir('leela_s')+'leela_s_base.mytest-m64'
data = run_dir('leela_s')+'ref.sgf'
leela_s.cmd = [leela_s.executable] + [data]

#548.exchange2_r    
exchange2_r = Process(pid = 548) 
exchange2_r.executable = run_dir('exchange2_r')+'exchange2_r_base.mytest-m64'
exchange2_r.cmd = [exchange2_r.executable] + ['6']

#648.exchange2_s   
exchange2_s = Process(pid = 648) 
exchange2_s.executable = run_dir('exchange2_s')+'exchange2_s_base.mytest-m64'
exchange2_s.cmd = [exchange2_s.executable] + ['6']

#557.xz_r   
xz_r = Process(pid = 557) 
xz_r.executable = run_dir('xz_r')+'xz_r_base.mytest-m64'
xz_r.cmd = [xz_r.executable] + [run_dir('xz_r')+'cld.tar.xz','160','19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474','59796407','61004416','6']

#657.xz_s   
xz_s = Process(pid = 657) 
xz_s.executable = run_dir('xz_s')+'xz_s_base.mytest-m64'
xz_s.cmd = [xz_s.executable] + [run_dir('xz_s')+'cpu2006docs.tar.xz','6643','055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae','1036078272','1111795472','4']

#503.bwaves_r    
bwaves_r = Process(pid = 503) 
bwaves_r.executable = run_dir('bwaves_r')+'bwaves_r_base.mytest-m64'
bwaves_r.cmd = [bwaves_r.executable] + ['bwaves_3']
bwaves_r.input = run_dir('bwaves_r')+'bwaves_3.in'

#603.bwaves_s    
bwaves_s = Process(pid = 603) 
bwaves_s.executable = run_dir('bwaves_s')+'speed_bwaves_base.mytest-m64'
bwaves_s.cmd = [bwaves_s.executable] + ['bwaves_1']
bwaves_s.input = run_dir('bwaves_s')+'bwaves_1.in'

#507.cactuBSSN_r   
cactuBSSN_r = Process(pid = 507) 
cactuBSSN_r.executable = run_dir('cactuBSSN_r')+'cactusBSSN_r_base.mytest-m64'
data = run_dir('cactuBSSN_r')+'spec_ref.par'
cactuBSSN_r.cmd = [cactuBSSN_r.executable] + [data]

#607.cactuBSSN_s   
cactuBSSN_s = Process(pid = 607) 
cactuBSSN_s.executable = run_dir('cactuBSSN_s')+'cactuBSSN_s_base.mytest-m64'
data = run_dir('cactuBSSN_s')+'spec_ref.par'
cactuBSSN_s.cmd = [cactuBSSN_s.executable] + [data]

#508.namd_r    
namd_r = Process(pid = 508) 
namd_r.executable = run_dir('namd_r')+'namd_r_base.mytest-m64'
namd_r.cmd = [namd_r.executable] + ['--input',run_dir('namd_r')+'apoa1.input','--output',run_dir('namd_r')+'apoa1.ref.output','--iterations','65'] 

#510.parest_r    
parest_r = Process(pid = 510) 
parest_r.executable = run_dir('parest_r')+'parest_r_base.mytest-m64'
data = run_dir('parest_r')+'ref.prm'
parest_r.cmd = [parest_r.executable] + [data]

#511.povray_r    
povray_r = Process(pid = 511) 
povray_r.executable = run_dir('povray_r')+'povray_r_base.mytest-m64'
data = run_dir('povray_r')+'SPEC-benchmark-ref.ini'
povray_r.cmd = [povray_r.executable] + [data]

#519.lbm_r   
lbm_r = Process(pid = 519) 
lbm_r.executable = run_dir('lbm_r')+'lbm_r_base.mytest-m64'
lbm_r.cmd = [lbm_r.executable] + ['3000','reference.dat','0','0',run_dir('lbm_r')+'100_100_130_ldc.of']

#619.lbm_s     
lbm_s = Process(pid = 619) 
lbm_s.executable = run_dir('lbm_s')+'lbm_s_base.mytest-m64'
lbm_s.cmd = [lbm_s.executable] + ['2000','reference.dat','0','0',run_dir('lbm_s')+'200_200_260_ldc.of']

#521.wrf_r     
wrf_r = Process(pid = 521) 
wrf_r.executable = run_dir('wrf_r')+'wrf_r_base.mytest-m64'
wrf_r.cmd = [wrf_r.executable]

#621.wrf_s      
wrf_s = Process(pid = 621) 
wrf_s.executable = run_dir('wrf_s')+'wrf_s_base.mytest-m64'
wrf_s.cmd = [wrf_s.executable]

#526.blender_r   
blender_r = Process(pid = 526) 
blender_r.executable = run_dir('blender_r')+'blender_r_base.mytest-m64'
blender_r.cmd = [blender_r.executable] + [run_dir('blender_r')+'sh3_no_char.blend','--render-output','sh3_no_char_','--threads','1','-b','-F','RAWTGA','-s','849','-e','849','-a']

#527.cam4_r      
cam4_r = Process(pid = 527) 
cam4_r.executable = run_dir('cam4_r')+'cam4_r_base.mytest-m64'
cam4_r.cmd = [cam4_r.executable]

#627.cam4_s     
cam4_s = Process(pid = 627) 
cam4_s.executable = run_dir('cam4_s')+'cam4_s_base.mytest-m64'
cam4_s.cmd = [cam4_s.executable]

#628.pop2_s       
pop2_s = Process(pid = 628) 
pop2_s.executable = run_dir('pop2_s')+'speed_pop2_base.mytest-m64'
pop2_s.cmd = [pop2_s.executable]

#538.imagick_r    
imagick_r = Process(pid = 538) 
imagick_r.executable = run_dir('imagick_r')+'imagick_r_base.mytest-m64'
imagick_r.cmd = [imagick_r.executable] + ['-limit','disk','0',run_dir('imagick_r')+'refrate_input.tga','-edge','41','-resample','181%','-emboss','31','-colorspace','YUV','-mean-shift','19x19+15%','-resize','30%','refrate_output.tga']

#638.imagick_s    
imagick_s = Process(pid = 638) 
imagick_s.executable = run_dir('imagick_s')+'imagick_s_base.mytest-m64'
imagick_s.cmd = [imagick_s.executable] + ['-limit','disk','0',run_dir('imagick_s')+'refspeed_input.tga','-resize','817%','-rotate','-2.76','-shave','540x375','-alpha','remove','-auto-level','-contrast-stretch','1x1%','-colorspace','Lab','-channel','R','-equalize','+channel','-colorspace','sRGB','-define','histogram:unique-colors=false','-adaptiveblur','0x5','-despeckle','-auto-gamma','-adaptive-sharpen','55','-enhance','-brightness-contrast','10x10','-resize','30%','refspeed_output.tga']

#544.nab_r     
nab_r = Process(pid = 544) 
nab_r.executable = run_dir('nab_r')+'nab_r_base.mytest-m64'
nab_r.cmd = [nab_r.executable] + ['1am0','1122214447','122']

#644.nab_s     
nab_s = Process(pid = 644) 
nab_s.executable = run_dir('nab_s')+'nab_s_base.mytest-m64'
nab_s.cmd = [nab_s.executable] + ['3j1n','20140317','220']

#549.fotonik3d_r       
fotonik3d_r = Process(pid = 549) 
fotonik3d_r.executable = run_dir('fotonik3d_r')+'fotonik3d_r_base.mytest-m64'
fotonik3d_r.cmd = [fotonik3d_r.executable]

#649.fotonik3d_s       
fotonik3d_s = Process(pid = 649) 
fotonik3d_s.executable = run_dir('fotonik3d_s')+'fotonik3d_s_base.mytest-m64'
fotonik3d_s.cmd = [fotonik3d_s.executable]

#554.roms_r     
roms_r = Process(pid = 554) 
roms_r.executable = run_dir('roms_r')+'roms_r_base.mytest-m64'
roms_r.cmd = [roms_r.executable]
roms_r.input = run_dir('roms_r')+'ocean_benchmark2.in.x'

#654.roms_s     
roms_s = Process(pid = 654) 
roms_s.executable = run_dir('roms_s')+'sroms_base.mytest-m64'
roms_s.cmd = [roms_s.executable]
roms_s.input = run_dir('roms_s')+'ocean_benchmark3.in.x'

#997.specrand_fr       
specrand_fr = Process(pid = 997) 
specrand_fr.executable = run_dir('specrand_fr')+'specrand_fr_base.mytest-m64'
# specrand_fr.cmd = [specrand_fr.executable] + ['324342 24239']
specrand_fr.cmd = [specrand_fr.executable] + [' 1255432124', '234923']

#999.specrand_ir       
specrand_ir = Process(pid = 999) 
specrand_ir.executable = run_dir('specrand_ir')+'specrand_ir_base.mytest-m64'
specrand_ir.cmd = [specrand_ir.executable] + ['1255432124', ' 234923']