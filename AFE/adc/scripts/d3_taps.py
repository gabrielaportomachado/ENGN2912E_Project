#!/usr/bin/env python3
"""Run scripts/d3_sta.tcl for the 5 lib corners on lg/runs/d3/final, parse tap arrivals and print tables.  usage: d3_taps.py [out.log]  (sta output cached in sim/.ptmp)"""
import subprocess, re, os, sys, json
ADC=os.path.normpath(os.path.join(os.path.dirname(__file__),'..'))
RUN=ADC+'/lg/runs/d3/final'
CORN=['tt_025C_3v30','ss_125C_3v00','ss_n40C_3v00','ff_n40C_3v60','ff_125C_3v60']
def run(c):
    env=dict(os.environ,CORNER=c,RUN=RUN)
    return subprocess.run(['sta','-no_init','-no_splash','-exit',ADC+'/scripts/d3_sta.tcl'],env=env,capture_output=True,text=True).stdout
def parse(txt):
    d={'rise':[None]*8,'fall':[None]*8,'cap':[None]*8,'slack':{}}
    cur=None
    for ln in txt.splitlines():
        m=re.match(r'ADC (\d) (RISE|FALL)',ln)
        if m: cur=(int(m.group(1)),m.group(2).lower()); continue
        m=re.match(r'cmp_clk\[(\d)\] \(output\)\s+INF\s+([\d.]+)',ln)
        if m: d[cur[1]][int(m.group(1))]=float(m.group(2)); continue
        m=re.match(r'ADC (\d) CAPPATH P=([\d.]+)',ln)
        if m: cp=(int(m.group(1)),m.group(2)); continue
        m=re.search(r'(-?[\d.]+)\s+slack',ln)
        if m and 'cp' in dir(): d['slack'][cp]=float(m.group(1))
        m=re.match(r'\s+[\d.]+\s+([\d.]+) \^ _\d+_/CLK',ln)
        if m and 'cp' in dir() and cp[1]=='500' and d['cap'][cp[0]] is None: d['cap'][cp[0]]=float(m.group(1))
    return d
def per_type(txt):
    t={}
    for ln in txt.splitlines():
        m=re.match(r'\s+([\d.]+)\s+[\d.]+ [\^v] ckg\.t\[0\]\.(first|wch)\.ch?\.?g?.*\((gf180mcu_fd_sc_mcu7t5v0__(dly[a-d]_1))\)',ln)
        m=re.match(r'\s+([\d.]+)\s+[\d.]+ [\^v] ckg\.t\[[0-9]\]\..*\(gf180mcu_fd_sc_mcu7t5v0__(dly[a-d])_1\)',ln)
        if m: t.setdefault(m.group(2),[]).append(float(m.group(1)))
    return {k:sum(v)/len(v) for k,v in t.items()}
if __name__=='__main__':
    out=open(sys.argv[1],'w') if len(sys.argv)>1 else sys.stdout
    data={}
    os.makedirs(ADC+'/sim/.ptmp',exist_ok=True)
    for c in CORN:
        txt=run(c); open(ADC+'/sim/.ptmp/sta_'+c+'.txt','w').write(txt); data[c]=parse(txt); data[c]['types']=per_type(txt)
    pass
    P=lambda *a: print(*a,file=out)
    P('Comparator clock taps from OpenSTA on the LibreLane netlist + nom SPEF (no CTS, ideal SCLK edge at the port).  rise = cmp_clk[i] rising (window start), fall = window end, W = fall - rise,')
    P('cap = capture-flop clock arrival (tapw).  Delta = rise[i+1]-rise[i].  All in ns.')
    for c in CORN:
        d=data[c]; P('\n== corner',c,'   per-cell delays in the chain:',{k:round(v,3) for k,v in d['types'].items()})
        P('ADC  rise   fall    W     cap   Delta')
        for i in range(8):
            P('%d  %7.2f %7.2f %5.2f %7.2f %6s'%(i,d['rise'][i],d['fall'][i],d['fall'][i]-d['rise'][i],d['cap'][i] or 0,('%.2f'%(d['rise'][i]-d['rise'][i-1])) if i else '-'))
    P('\nRatios (rise of ADC 0 / ADC 7 window end):')
    for c in CORN: P('  %-14s T0 %.2f  last end %.2f  ratio to ff_n40: T0 %.2f  last %.2f'%(c,data[c]['rise'][0],data[c]['fall'][7],data[c]['rise'][0]/data['ff_n40C_3v60']['rise'][0],data[c]['fall'][7]/data['ff_n40C_3v60']['fall'][7]))
    P('\nCheck 1 (direct): last window end + 5 ns margin < T at 3 MHz (333.3 ns) and 2 MHz (500 ns); Check 2: T0 >= 24 ns (D2 DAC settling), per corner')
    for c in CORN:
        d=data[c]; e=d['fall'][7]
        P('  %-14s T0 %6.2f (>=24: %s)  last end %7.2f  margin@3MHz %7.2f (%s)  margin@2MHz %7.2f (%s)  STA slack cap->code @333.3: %s  @500: %s'%(c,d['rise'][0],'ok' if d['rise'][0]>=24 else 'FAIL',e,333.333-e,'ok' if 333.333-e>=5 else 'FAIL',500-e,'ok' if 500-e>=5 else 'FAIL',min(v for k,v in d['slack'].items() if k[1]=='333.333'),min(v for k,v in d['slack'].items() if k[1]=='500')))
    import shutil; shutil.rmtree(ADC+'/sim/.ptmp',ignore_errors=True)
