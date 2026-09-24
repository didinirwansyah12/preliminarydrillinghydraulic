import math
from pathlib import Path
import os
import io
from datetime import date
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Preliminary Drilling Hydraulic Assessment", page_icon="🛢️", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1500px;padding-top:1.0rem;padding-bottom:1.2rem}
.pdha-spacer{height:2.2rem!important;line-height:2.2rem!important;display:block!important}
.pdha-header-wrap{display:block!important;visibility:visible!important;opacity:1!important;position:relative!important;z-index:999999!important;width:100%;margin:0 0 1.0rem 0!important;padding:0!important;overflow:visible!important;clear:both!important}
.pdha-title{display:block!important;visibility:visible!important;opacity:1!important;color:#f4f4f4!important;font-size:34px!important;font-weight:800!important;line-height:1.2!important;margin:0 0 18px 0!important;padding:0!important;letter-spacing:-.3px!important;white-space:normal!important;text-shadow:none!important}
.pdha-sub{display:block!important;visibility:visible!important;color:#9aa0a6!important;font-size:14px!important;font-weight:600!important;line-height:1.25!important;margin:0 0 20px 0!important;padding:0!important}
.pdha-note{display:block!important;visibility:visible!important;background:#19344e!important;color:#48a5ff!important;padding:17px 16px!important;border-radius:8px!important;font-size:14px!important;line-height:1.35!important;box-sizing:border-box;width:100%;overflow:visible!important}
[data-testid="stNumberInput"] input, div[data-testid="stNumberInput"] input, div[data-testid="stNumberInput"] input[type="number"]{font-size:16px!important;font-weight:500!important;line-height:1.25!important;min-height:2.6rem!important;font-family:inherit!important;opacity:1!important}
[data-testid="stNumberInput"] input::placeholder{font-size:16px!important}
[data-testid="stNumberInput"] button{min-height:2.6rem!important}
.section{color:#073b73;font-weight:800;font-size:18px;margin:.3rem 0 .45rem}.result{color:#0b63b6;font-weight:800;font-size:18px;margin:.3rem 0 .45rem}
[data-testid="stMetric"]{border:1px solid #d5dde6;border-radius:7px;padding:5px}
</style>
<div class="pdha-spacer">&nbsp;</div>
<div class="pdha-header-wrap">
  <div class="pdha-title">Preliminary Drilling Hydraulic Tool</div>
  <div class="pdha-sub">Power Law fluid model | developed by Didin Irwansyah for Rigsis Drilling Team</div>
  <div class="pdha-note">This prototype is intended for preliminary assessment only. It is not a replacement for detailed drilling hydraulic analysis from Mud Company.</div>
</div>
""", unsafe_allow_html=True)

API_CASING = {
    "9-5/8 in × 29.30 lb/ft":{"od":9.625,"id":9.063,"drift":8.907},"9-5/8 in × 32.30 lb/ft":{"od":9.625,"id":9.001,"drift":8.845},"9-5/8 in × 36.00 lb/ft":{"od":9.625,"id":8.921,"drift":8.765},"9-5/8 in × 40.00 lb/ft":{"od":9.625,"id":8.835,"drift":8.679},"9-5/8 in × 47.00 lb/ft":{"od":9.625,"id":8.681,"drift":8.525},
    "10-3/4 in × 40.50 lb/ft":{"od":10.750,"id":10.050,"drift":9.984},"10-3/4 in × 51.00 lb/ft":{"od":10.750,"id":9.850,"drift":9.694},"10-3/4 in × 55.50 lb/ft":{"od":10.750,"id":9.760,"drift":9.604},"10-3/4 in × 65.70 lb/ft":{"od":10.750,"id":9.560,"drift":9.404},
    "11-3/4 in × 42.00 lb/ft":{"od":11.750,"id":11.084,"drift":10.928},"11-3/4 in × 47.00 lb/ft":{"od":11.750,"id":11.000,"drift":10.844},"11-3/4 in × 54.00 lb/ft":{"od":11.750,"id":10.880,"drift":10.724},"11-3/4 in × 60.00 lb/ft":{"od":11.750,"id":10.772,"drift":10.616},
    "13-3/8 in × 48.00 lb/ft":{"od":13.375,"id":12.715,"drift":12.559},"13-3/8 in × 54.50 lb/ft":{"od":13.375,"id":12.615,"drift":12.459},"13-3/8 in × 61.00 lb/ft":{"od":13.375,"id":12.515,"drift":12.359},"13-3/8 in × 68.00 lb/ft":{"od":13.375,"id":12.415,"drift":12.259},"13-3/8 in × 72.00 lb/ft":{"od":13.375,"id":12.347,"drift":12.191},
    "16 in × 65.00 lb/ft":{"od":16.000,"id":15.250,"drift":15.062},"16 in × 75.00 lb/ft":{"od":16.000,"id":15.124,"drift":14.936},"16 in × 84.00 lb/ft":{"od":16.000,"id":15.010,"drift":14.822},"18-5/8 in × 87.50 lb/ft":{"od":18.625,"id":17.755,"drift":17.567},
    "20 in × 94.00 lb/ft":{"od":20.000,"id":19.124,"drift":18.936},"20 in × 106.50 lb/ft":{"od":20.000,"id":19.000,"drift":18.812},"20 in × 133.00 lb/ft":{"od":20.000,"id":18.730,"drift":18.542},"20 in × 169.00 lb/ft":{"od":20.000,"id":18.376,"drift":18.188},
}

def _font(size,bold=False):
    # Use a bundled font first so local and Streamlit Cloud render the schematic identically.
    bundled = Path(__file__).parent / "assets" / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    candidates=[bundled]
    win_font_dir=Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts"
    candidates += ([win_font_dir/"arialbd.ttf",win_font_dir/"calibrib.ttf",Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")] if bold else [win_font_dir/"arial.ttf",win_font_dir/"calibri.ttf",Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf")])
    for f in candidates:
        if f.exists(): return ImageFont.truetype(str(f),size=size)
    raise RuntimeError("No TrueType font available for Well Schematic rendering.")

def _center_text(draw,box,text,font,fill=(0,0,0)):
    x1,y1,x2,y2=box; bb=draw.textbbox((0,0),text,font=font); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    draw.text(((x1+x2-tw)/2,(y1+y2-th)/2-2),text,font=font,fill=fill)

def render_schematic(td,previous_casing_depth,dp_len,hwdp_len,dc_len):
    img=Image.open(Path(__file__).parent/"assets"/"well_schematic.jpg").convert("RGB"); d=ImageDraw.Draw(img)
    sx,sy=img.width/1469,img.height/2048
    base={"dp":(856,585,1094,655),"csg":(593,956,830,1027),"hwdp":(1138,1212,1375,1282),"dc":(1138,1544,1376,1615),"oh":(940,1942,1177,2012)}
    boxes={k:tuple(int(v) for v in (x1*sx,y1*sy,x2*sx,y2*sy)) for k,(x1,y1,x2,y2) in base.items()}
    # These values are rasterized into the image.  Use a fixed, bundled font and
    # sizes that remain readable after Streamlit scales the image to the column width.
    fy,fw=_font(52,True),_font(30,True)
    vals={"dp":f"{dp_len:,.0f} m","hwdp":f"{hwdp_len:,.0f} m","dc":f"{dc_len:,.0f} m","csg":f"0 – {previous_casing_depth:,.0f} m","oh":f"{previous_casing_depth:,.0f} – {td:,.0f} m"}
    for key in ("dp","hwdp","dc"): _center_text(d,boxes[key],vals[key],fy)
    for key in ("csg","oh"): _center_text(d,boxes[key],vals[key],fw)
    return img

def pl(R600,R300):
    if R600<=R300 or R300<=0: raise ValueError("R600 must be greater than R300.")
    # WellPlan Power Law formulation in API units.
    n=3.32192809*math.log10(R600/R300)
    k=(0.01065*R300)/((1.70333*300)**n)
    return n,k

def gf(n,a):
    return (((3-a)*n+1)/((4-a)*n))*(1+a/2)

def pipe(Q,rho,L,ID,n,k):
    # WellPlan Power Law pipe-body pressure-loss calculation.
    # rho input is mud weight in ppg; convert to lbm/ft^3 for API-unit equations.
    rho_lbmft3=rho*7.48052
    V_fpm=24.51*Q/ID**2
    V_fps=V_fpm/60.0
    D_ft=ID/12.0
    Gp=(((3*n+1)/(4*n))**n)*8**(n-1)
    gc=32.174
    Re=(rho_lbmft3*V_fps**(2-n)*D_ft**n)/(gc*Gp*k)
    RL=3470-1370*n
    RT=4270-1370*n
    a=(math.log10(n)+3.93)/50
    b=(1.75-math.log10(n))/7
    if Re<=RL:
        f=16/Re
        regime="Laminar"
    elif Re<=RT:
        f=16/RL + (Re-RL)/800*(a/(RT**b)-16/RL)
        regime="Transitional"
    else:
        f=a/(Re**b)
        regime="Turbulent"
    L_ft=L*3.28084
    dp=(rho_lbmft3/gc)*V_fps**2*f*L_ft*(2/D_ft)/144.0
    return dp,V_fps,Re,f,regime

def tool_joint_coefficient(Re):
    if Re < 1000:
        return 0.0
    if Re <= 3000:
        return 1.91*math.log10(Re)-5.64
    if Re <= 13000:
        return 4.66-1.05*math.log10(Re)
    return 0.33

def tool_joint_loss(Q,rho,body_id,tj_id,n,k,avg_joint_length,component_length):
    # Internal Tool Joint (ITJ) minor loss. The WellPlan correlation uses
    # the component-body velocity/Reynolds number; TJ ID is retained as an
    # input/documentation field but is not an explicit term in the correlation.
    _, V_fps, Re, _, regime = pipe(Q,rho,1.0,body_id,n,k)
    ktj=tool_joint_coefficient(Re)
    gc=32.174
    one_tj_psi=(rho*7.48052)*ktj*V_fps**2/(2*gc)/144.0
    n_joints=component_length/avg_joint_length if avg_joint_length>0 else 0.0
    total_psi=one_tj_psi*n_joints
    return total_psi,V_fps,Re,ktj,n_joints,one_tj_psi,regime

def ann(Q,rho,L,hole,OD,n,k):
    # WellPlan Power Law annulus pressure-loss calculation.
    dh_in=hole-OD
    if dh_in<=0: raise ValueError(f"Hole size {hole:.3f} in must exceed pipe OD {OD:.3f} in.")
    rho_lbmft3=rho*7.48052
    V_fpm=24.51*Q/(hole**2-OD**2)
    V_fps=V_fpm/60.0
    dh_ft=dh_in/12.0
    Ga=(((2*n+1)/(2*n))**n)*8**(n-1)
    gc=32.174
    Re=(rho_lbmft3*V_fps**(2-n)*dh_ft**n)/(gc*(2/3)*Ga*k)
    RL=3470-1370*n
    RT=4270-1370*n
    a=(math.log10(n)+3.93)/50
    b=(1.75-math.log10(n))/7
    if Re<=RL:
        f=24/Re
        regime="Laminar"
    elif Re<=RT:
        f=24/RL + (Re-RL)/800*(a/(RT**b)-24/RL)
        regime="Transitional"
    else:
        f=a/(Re**b)
        regime="Turbulent"
    L_ft=L*3.28084
    dp=(rho_lbmft3/gc)*V_fps**2*f*L_ft*(2/dh_ft)/144.0
    return dp,V_fps,Re,f,regime

def bit(Q,rho,tfa,cd=0.95):
    """Bit hydraulic loss using WellPlan-style nozzle discharge coefficient.
    rho is mud weight in ppg; pressure loss is returned in psi.
    """
    if tfa<=0 or cd<=0:
        return 0.0, 0.0
    gc=32.174
    rho_lbmft3=rho*7.48051948
    nozzle_v=0.3208*Q/tfa
    dp=(rho_lbmft3*nozzle_v**2)/(2*gc*cd**2)/144.0
    return dp,tfa

def moore_slip_velocity(Q,rho_m,hole,pipe_od,n,k,cutting_size,cutting_sg):
    """Standard preliminary cutting-slip model used for the in-house HC screen.
    The model is intentionally independent of ROP and drillpipe RPM.
    """
    if hole<=pipe_od: raise ValueError(f"Hole size {hole:.3f} in must exceed pipe OD {pipe_od:.3f} in.")
    if cutting_size<=0 or cutting_sg<=0 or rho_m<=0 or n<=0 or k<=0: raise ValueError("Invalid hole-cleaning input.")
    va_fpm=24.5*Q/(hole**2-pipe_od**2)
    K_moore=510*k
    mu_a=(K_moore/144)*(((hole-pipe_od)/(max(va_fpm,1e-9)/60))**(1-n))*(((2+1/n)/.0208)**n)
    rho_s=cutting_sg*8.3454; delta_rho=rho_s-rho_m
    if delta_rho<=0: return va_fpm,0.0,va_fpm,0.0
    v=174*cutting_size*(delta_rho**.667)/((rho_m*max(mu_a,1e-12))**.333)
    for _ in range(30):
        rep=928*rho_m*max(v,1e-12)*cutting_size/max(mu_a,1e-12)
        if rep<=1:
            nv=4972*cutting_size**2*delta_rho/(rho_m*max(mu_a,1e-12))
        elif rep<2000:
            nv=174*cutting_size*(delta_rho**.667)/((rho_m*max(mu_a,1e-12))**.333)
        else:
            nv=9.24*math.sqrt(cutting_size*delta_rho/rho_m)
        if abs(nv-v)<1e-8: v=nv; break
        v=nv
    rep=928*rho_m*max(v,1e-12)*cutting_size/max(mu_a,1e-12)
    v=max(v,0.0)
    return va_fpm,v,va_fpm-v,rep

def hole_cleaning_interval(Q,rho_m,hole,pipe_od,n,k,rop_mhr,cutting_size,cutting_sg):
    """In-house preliminary HC screen.
    Limits: CC <= 5%, transport velocity > 0, annular velocity >= 100 ft/min.
    CC is a simple volumetric feed-concentration / net-transport model:
        Co = (ROP_ft/hr * hole^2 / 1471) / (same + Q)
        CC = Co * Va / Vtransport
    """
    va,vslip,vtransport,rep=moore_slip_velocity(Q,rho_m,hole,pipe_od,n,k,cutting_size,cutting_sg)
    qcut=rop_mhr*3.28084*hole**2/1471.0
    co=100.0*qcut/(qcut+Q) if (qcut+Q)>0 else float('inf')
    cca=co*va/vtransport if vtransport>0 else float('inf')
    tr=vtransport/va if va>0 else 0.0
    status=(cca<=5.0 and vtransport>0.0 and va>=100.0)
    return va,vslip,vtransport,tr,cca,rep

def hole_cleaning_limits(Q,rho_m,hole,pipe_od,n,k,cutting_size,cutting_sg):
    """Return the maximum ROP allowed at a given flow by the three HC screens."""
    va,vslip,vtransport,tr,_,rep=hole_cleaning_interval(Q,rho_m,hole,pipe_od,n,k,1.0,cutting_size,cutting_sg)
    if vtransport<=0 or va<100.0:
        return {"va":va,"vslip":vslip,"vtransport":vtransport,"tr":tr,"rop_max":float('nan'),"criterion":"Transport Velocity / Annular Velocity","rep":rep}
    # For fixed Q and geometry, CC scales linearly with ROP in this simplified model.
    # Solve CC=5% directly rather than relying on a numerical search.
    # CC = 100 * [A/(A+Q)] * Va/(Va-Vslip), A = ROP_ft/hr * hole^2 / 1471
    target=5.0
    denom_factor=100.0*va/vtransport
    if denom_factor<=0 or target>=denom_factor:
        rop_max=float('inf')
    else:
        amax=target/denom_factor
        # amax = A/(A+Q) -> A = amax*Q/(1-amax)
        A=amax*Q/(1.0-amax)
        rop_max=A*1471.0/(3.28084*hole**2)
    return {"va":va,"vslip":vslip,"vtransport":vtransport,"tr":tr,"rop_max":rop_max,"criterion":"Cutting Concentration" if math.isfinite(rop_max) else "None","rep":rep}

def trajectory(td,kop,eob,final_inc,azimuth_deg=0.0):
    eob=max(kop,min(eob,td)); stations=[(0.,0.,azimuth_deg,"Surface"),(float(kop),0.,azimuth_deg,"KOP"),(eob,float(final_inc),azimuth_deg,"EOB"),(float(td),float(final_inc),azimuth_deg,"TD")]
    clean=[]
    for row in stations:
        if clean and abs(row[0]-clean[-1][0])<1e-9: clean[-1]=row
        else: clean.append(row)
    N=E=TVD=0.; out=[]
    out.append([clean[0][3],clean[0][0],clean[0][1],clean[0][2],TVD,N,E,math.hypot(N,E),0.])
    for prev,cur in zip(clean[:-1],clean[1:]):
        md1,i1,a1,_=prev; md2,i2,a2,_=cur; dmd=md2-md1; i1r,i2r=map(math.radians,(i1,i2)); a1r,a2r=map(math.radians,(a1,a2))
        dl=math.acos(max(-1,min(1,math.cos(i1r)*math.cos(i2r)+math.sin(i1r)*math.sin(i2r)*math.cos(a2r-a1r))))
        rf=1 if abs(dl)<1e-10 else 2/dl*math.tan(dl/2)
        dN=dmd/2*(math.sin(i1r)*math.cos(a1r)+math.sin(i2r)*math.cos(a2r))*rf; dE=dmd/2*(math.sin(i1r)*math.sin(a1r)+math.sin(i2r)*math.sin(a2r))*rf; dT=dmd/2*(math.cos(i1r)+math.cos(i2r))*rf
        N+=dN; E+=dE; TVD+=dT; dls=math.degrees(dl)/dmd*30 if dmd else 0
        out.append([cur[3],md2,i2,a2,dTVD if False else TVD,N,E,math.hypot(N,E),dls])
    return pd.DataFrame(out,columns=["Point","MD (m)","Inc (°)","Azi (°)","TVD (m)","Northing (m)","Easting (m)","Displacement (m)","DLS (°/30m)"])

def pressure_curve(flow_values,params):
    mw,n,k,dp_len,dp_id,dp_tj_id,avg_joint_length,hwdp_len,hwdp_id,hwdp_tj_id,dc_len,dc_id,pc,casing,oh,dp_od,hwdp_od,dc_od,tfa,surface,motor=params; rows=[]
    for q in flow_values:
        ds=0
        if dp_len: ds+=pipe(q,mw,dp_len,dp_id,n,k)[0] + tool_joint_loss(q,mw,dp_id,dp_tj_id,n,k,avg_joint_length,dp_len)[0]
        if hwdp_len: ds+=pipe(q,mw,hwdp_len,hwdp_id,n,k)[0] + tool_joint_loss(q,mw,hwdp_id,hwdp_tj_id,n,k,avg_joint_length,hwdp_len)[0]
        if dc_len: ds+=pipe(q,mw,dc_len,dc_id,n,k)[0]
        ann_total=0; depth=0
        for name,L,OD in [("Drill Pipe",dp_len,dp_od),("HWDP",hwdp_len,hwdp_od),("Drill Collar",dc_len,dc_od)]:
            s,e=depth,depth+L; depth=e
            if s<pc:
                b=min(e,pc)
                if b>s: ann_total+=ann(q,mw,b-s,casing["id"],OD,n,k)[0]
            if e>pc:
                a=max(s,pc)
                if e>a: ann_total+=ann(q,mw,e-a,oh,OD,n,k)[0]
        bp=bit(q,mw,tfa)[0]; rows.append([q,surface+motor+ds+bp+ann_total])
    return pd.DataFrame(rows,columns=["Flow Rate (gpm)","Pressure Loss (psi)"])

def calculate(p):
    td,pc,kop,eob,inc,casing,oh,dc_len,dc_id,dc_od,hwdp_len,hwdp_id,hwdp_od,hwdp_tj_id,dp_id,dp_od,dp_tj_id,avg_joint_length,mw,r600,r300,Q,tfa,surface,motor,rop,cutting_size,cutting_sg=[p[k] for k in p]
    n,k=pl(r600,r300); pv=r600-r300; yp=2*r300-r600; dp_len=max(td-dc_len-hwdp_len,0)
    traj=trajectory(td,kop,eob,inc)
    prows=[]; ptotal=0
    component_totals={"Drill Pipe":0.0,"HWDP":0.0,"Drill Collar":0.0}
    component_tj={"Drill Pipe":None,"HWDP":None}
    components=[("Drill Pipe",dp_len,dp_id,dp_tj_id,True),("HWDP",hwdp_len,hwdp_id,hwdp_tj_id,True),("Drill Collar",dc_len,dc_id,None,False)]
    for name,L,ID,TJID,has_tj in components:
        if L:
            vals=pipe(Q,mw,L,ID,n,k)
            tj=tool_joint_loss(Q,mw,ID,TJID,n,k,avg_joint_length,L) if has_tj else None
            component_totals[name]=vals[0]+(tj[0] if tj else 0.0)
            component_tj[name]=tj
            ptotal+=component_totals[name]
            prows.append([f"{name} Body",L,ID,vals[1],vals[2],vals[4],vals[3],vals[0]])
            if tj:
                prows.append([f"{name} Internal Tool Joint (ITJ)",tj[4],TJID,tj[1],tj[2],tj[6],tj[3],tj[0]])
    arows=[]; atotal=0; depth=0
    for name,L,OD in [("Drill Pipe",dp_len,dp_od),("HWDP",hwdp_len,hwdp_od),("Drill Collar",dc_len,dc_od)]:
        s,e=depth,depth+L; depth=e
        if s<pc:
            b=min(e,pc)
            if b>s:
                vals=ann(Q,mw,b-s,casing["id"],OD,n,k); atotal+=vals[0]; arows.append([name,s,b,b-s,casing["id"],OD,"Casing",vals[1],vals[2],vals[4],vals[3],vals[0]])
        if e>pc:
            a=max(s,pc)
            if e>a:
                vals=ann(Q,mw,e-a,oh,OD,n,k); atotal+=vals[0]; arows.append([name,a,e,e-a,oh,OD,"Open Hole",vals[1],vals[2],vals[4],vals[3],vals[0]])
    bdp,_=bit(Q,mw,tfa); equipment=surface+motor; string_total=ptotal+bdp; total=equipment+string_total+atotal
    tj_loss=sum((component_tj[name][0] for name in component_tj if component_tj[name]),0.0)
    # Pressure-loss summary with Bit separated from drillstring body.
    string_body_total=ptotal
    pressure_df=pd.DataFrame([["Surface Line",surface],["Mud Motor",motor],["String (DP + HWDP + DC)",string_body_total],["Bit",bdp],["Annulus (DP + HWDP + DC)",atotal],["Total Pressure Loss",total]],columns=["Section","Delta P (psi)"]); pressure_df["% of Total"]=pressure_df["Delta P (psi)"]/total*100
    # Match WellPlan Page 7 contributor grouping: string by BHA component, annulus by BHA component.
    drill_labels=["Drill Pipe","HWDP","Drill Collar"]
    drill_values=[component_totals["Drill Pipe"],component_totals["HWDP"],component_totals["Drill Collar"]]
    ann_map={comp:0. for comp in ["Drill Pipe","HWDP","Drill Collar"]}
    for rr in arows: ann_map[rr[0]]+=rr[11]
    ann_labels=[x for x,v in ann_map.items() if v>0]; ann_values=[ann_map[x] for x in ann_labels]
    def interval_geom(mid):
        section="Casing" if mid<pc else "Open Hole"; hole=casing["id"] if mid<pc else oh
        # From surface to TD: DP -> HWDP -> DC.
        if mid<dp_len: comp,pod="Drill Pipe",dp_od
        elif mid<dp_len+hwdp_len: comp,pod="HWDP",hwdp_od
        else: comp,pod="Drill Collar",dc_od
        return section,comp,hole,pod
    hc=[]; stations=list(range(30,int(math.floor(td/30))*30+1,30));
    if not stations or stations[-1]<td: stations.append(float(td))
    for md in stations:
        top=max(0.,md-30); mid=(top+md)/2; sec,comp,hole,pod=interval_geom(mid)
        try: vals=hole_cleaning_interval(Q,mw,hole,pod,n,k,rop,cutting_size,cutting_sg); hc.append([md,mid,sec,comp,hole,pod,*vals])
        except Exception: hc.append([md,mid,sec,comp,hole,pod,*([float('nan')]*6)])
    hc_df=pd.DataFrame(hc,columns=["MD (m)","Mid MD (m)","Section","Drillstring Component","Hole Size (in)","Pipe OD (in)","Annular Velocity (ft/min)","Cutting Slip Velocity (ft/min)","Cutting Transport Velocity (ft/min)","Transport Ratio","Cutting Concentration (%)","Particle Re"])
    def hc_at(q,mid,rv):
        sec,comp,hole,pod=interval_geom(mid); return hole_cleaning_interval(q,mw,hole,pod,n,k,rv,cutting_size,cutting_sg)
    def hc_limits_at(q,mid):
        sec,comp,hole,pod=interval_geom(mid); return hole_cleaning_limits(q,mw,hole,pod,n,k,cutting_size,cutting_sg)
    def acceptable(q,mid,rv):
        va,vslip,vt,tr,cc,rep=hc_at(q,mid,rv)
        return va>=100.0 and vt>0.0 and cc<=5.0
    def minq(mid,rv):
        # Annular-velocity floor is a hard lower bound. Then search for CC/transport compliance.
        sec,comp,hole,pod=interval_geom(mid)
        q_av=100.0*(hole**2-pod**2)/24.5
        if not math.isfinite(q_av): return float('nan')
        lo=max(1.0,q_av); hi=max(lo*1.25,lo+50.0)
        if acceptable(hi,mid,rv):
            for _ in range(45):
                mq=(lo+hi)/2
                if acceptable(mq,mid,rv): hi=mq
                else: lo=mq
            return hi
        for _ in range(30):
            hi*=1.5
            if hi>20000: return float('nan')
            if acceptable(hi,mid,rv):
                for _ in range(45):
                    mq=(lo+hi)/2
                    if acceptable(mq,mid,rv): hi=mq
                    else: lo=mq
                return hi
        return float('nan')
    minflow_rows=[]
    for rrow in hc:
        mq=minq(rrow[1],rop)
        if not math.isfinite(mq):
            crit="No feasible flowrate"
        else:
            va,vslip,vt,tr,cc,rep=hc_at(mq*1.000001,rrow[1],rop)
            margins={"Cutting Concentration":5.0-cc,"Transport Velocity":vt,"Annular Velocity":va-100.0}
            crit=min(margins,key=margins.get)
        minflow_rows.append([rrow[0],mq,crit])
    minflow=pd.DataFrame(minflow_rows,columns=["Depth (m)","Minimum Flowrate (gpm)","Limiting Criterion"])
    rop_sensitivity=[rop+i for i in [0,10,20,30,40,50]]
    minflow_sens_rows=[]
    for rrow in hc:
        row=[rrow[0]]
        for rv in rop_sensitivity:
            row.append(minq(rrow[1],rv))
        minflow_sens_rows.append(row)
    minflow_sens_columns=["Depth (m)"]+[f"{rv:.0f} m/hr" + (" - current ROP" if abs(rv-rop)<1e-9 else "") for rv in rop_sensitivity]
    minflow_sens_df=pd.DataFrame(minflow_sens_rows,columns=minflow_sens_columns)
    minflow_criteria=[]
    for rrow in hc:
        mq=minq(rrow[1],rop)
        if not math.isfinite(mq):
            crit="No feasible flowrate"
        else:
            va,vslip,vt,tr,cc,rep=hc_at(mq*1.000001,rrow[1],rop)
            margins={"Cutting Concentration":5.0-cc,"Transport Velocity":vt,"Annular Velocity":va-100.0}
            crit=min(margins,key=margins.get)
        minflow_criteria.append(crit)
    minflow["Limiting Criterion"]=minflow_criteria
    # Maximum allowable ROP at the current flow, evaluated at each 30 m interval.
    rop_limits=[]
    for rrow in hc:
        lim=hc_limits_at(Q,rrow[1]); rop_limits.append([rrow[0],rrow[1],lim["va"],lim["vslip"],lim["vtransport"],lim["rop_max"],lim["criterion"]])
    rop_limit_df=pd.DataFrame(rop_limits,columns=["Depth (m)","Mid MD (m)","Annular Velocity (ft/min)","Slip Velocity (ft/min)","Transport Velocity (ft/min)","Maximum ROP (m/hr)","Limiting Criterion"])
    # Maximum allowable ROP versus depth at five flowrates centered on the input flowrate.
    # Cases: FL-100, FL-50, FL, FL+50 and FL+100 gpm.
    rop_flow_points=[max(1.0,Q-100.0),max(1.0,Q-50.0),Q,Q+50.0,Q+100.0]
    rop_flow_points=list(dict.fromkeys(rop_flow_points))
    rop_depth_rows=[]
    for rrow in hc:
        row=[rrow[0]]
        for fq in rop_flow_points:
            lim=hc_limits_at(fq,rrow[1])
            row.append(lim["rop_max"] if lim["vtransport"]>0 and lim["va"]>=100.0 and math.isfinite(lim["rop_max"]) else float("nan"))
        rop_depth_rows.append(row)
    rop_depth_columns=["Depth (m)"]+[f"{fq:.0f} gpm" + (" - current input" if abs(fq-Q)<1e-9 else "") for fq in rop_flow_points]
    rop_depth_df=pd.DataFrame(rop_depth_rows,columns=rop_depth_columns)
    # Flow-rate / ROP operating envelope at the worst interval. This is the primary screening relationship.
    flow_points=[max(100.,Q*0.4),max(150.,Q*0.55),max(200.,Q*0.7),max(250.,Q*0.85),Q,max(Q*1.15,Q+50),max(Q*1.35,Q+100),max(Q*1.6,Q+150),max(Q*2.0,Q+300)]
    flow_points=sorted(set(round(x,1) for x in flow_points if x<=5000))
    envelope=[]
    for fq in flow_points:
        candidates=[]
        criteria=[]
        for rrow in hc:
            lim=hc_limits_at(fq,rrow[1]); candidates.append(lim["rop_max"]); criteria.append(lim["criterion"])
            if lim["vtransport"]<=0: candidates.append(float('nan'))
            if lim["va"]<100: candidates.append(float('nan'))
        finite=[x for x in candidates if math.isfinite(x)]
        env=min(finite) if finite and len(finite)==len([x for x in candidates if not math.isnan(x)]) else (min(finite) if finite else float('nan'))
        # A flow is not operationally acceptable if any interval violates AV or transport at any ROP.
        feasible=all(hc_limits_at(fq,rrow[1])["va"]>=100 and hc_limits_at(fq,rrow[1])["vtransport"]>0 for rrow in hc)
        envelope.append([fq,env,feasible])
    envelope_df=pd.DataFrame(envelope,columns=["Flow Rate (gpm)","Maximum Allowable ROP (m/hr)","Hydraulically Feasible"])
    finite_cc=hc_df["Cutting Concentration (%)"].dropna(); finite_ct=hc_df["Cutting Transport Velocity (ft/min)"].dropna(); worst_cc=float(finite_cc.max()) if len(finite_cc) else float('nan'); worst_cc_md=float(hc_df.loc[hc_df["Cutting Concentration (%)"].idxmax(),"MD (m)"]) if len(finite_cc) else None; worst_ct=float(finite_ct.min()) if len(finite_ct) else float('nan'); worst_ct_md=float(hc_df.loc[hc_df["Cutting Transport Velocity (ft/min)"].idxmin(),"MD (m)"]) if len(finite_ct) else None
    finite_rop=rop_limit_df["Maximum ROP (m/hr)"].dropna(); max_allowable_rop=float(finite_rop.min()) if len(finite_rop) else float('nan'); max_allowable_rop_md=float(rop_limit_df.loc[rop_limit_df["Maximum ROP (m/hr)"].idxmin(),"Depth (m)"]) if len(finite_rop) else None
    limiting_criterion="Cutting Concentration" if len(finite_rop) and math.isfinite(max_allowable_rop) else "Transport Velocity / Annular Velocity"
    bit_hp=bdp*Q/1714
    bit_power=100*bdp/total if total else 0
    nozzle_v=.3208*Q/tfa if tfa>0 else 0.0
    hole_area=math.pi/4*oh**2
    hsi=bit_hp/hole_area if hole_area>0 else 0.0
    impact=0.01823*0.95*Q*math.sqrt(max(mw*bdp,0.0))
    return locals()

def pie_fig(labels,values,title):
    import matplotlib.pyplot as plt
    # Same canvas size for the two WellPlan-style contributor charts.
    fig,ax=plt.subplots(figsize=(4.1,3.1))
    total=sum(values)
    def apct(pct):
        val=pct*total/100; return f"{pct:.0f}%\n({val:,.0f} psi)"
    ax.pie(values,labels=labels,autopct=apct,startangle=90,textprops={"fontsize":8},pctdistance=.67)
    ax.set_title(title,fontsize=10); fig.tight_layout(); return fig

def interactive_pressure(df,Q):
    import plotly.graph_objects as go
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df["Flow Rate (gpm)"],y=df["Pressure Loss (psi)"],mode="lines",name="Total Pressure Loss",hovertemplate="Flow: %{x:.0f} gpm<br>Pressure Loss: %{y:.1f} psi<extra></extra>"))
    exact=df.loc[(df["Flow Rate (gpm)"]-Q).abs().idxmin()]
    fig.add_trace(go.Scatter(x=[Q],y=[exact["Pressure Loss (psi)"]],mode="markers",name="Current Flowrate",hovertemplate="Current: %{x:.0f} gpm<br>ΔP: %{y:.1f} psi<extra></extra>"))
    fig.update_layout(height=360,margin=dict(l=45,r=20,t=45,b=45),xaxis_title="Flow Rate (gpm)",yaxis_title="Pressure Loss (psi)",hovermode="x unified")
    return fig

def interactive_minflow(df,pc):
    import plotly.graph_objects as go
    fig=go.Figure(); fig.add_trace(go.Scatter(x=df["Minimum Flowrate (gpm)"],y=df["Depth (m)"],mode="lines",name="Minimum Flowrate",hovertemplate="Min Flow: %{x:.0f} gpm<br>Depth: %{y:.0f} m<extra></extra>")); fig.add_hline(y=pc,line_dash="dash",annotation_text=f"Casing Point: {pc:,.0f} m"); fig.update_layout(height=360,margin=dict(l=45,r=20,t=45,b=45),xaxis_title="Minimum Flowrate (gpm)",yaxis_title="Depth (m)",yaxis=dict(autorange="reversed"),hovermode="x unified"); return fig

def interactive_rop_envelope(df):
    import plotly.graph_objects as go
    fig=go.Figure()
    v=df[df["Hydraulically Feasible"] & df["Maximum Allowable ROP (m/hr)"].notna()]
    if len(v):
        fig.add_trace(go.Scatter(x=v["Flow Rate (gpm)"],y=v["Maximum Allowable ROP (m/hr)"],mode="lines+markers",name="Max Allowable ROP",hovertemplate="Flow: %{x:.0f} gpm<br>Max ROP: %{y:.1f} m/hr<extra></extra>"))
    fig.add_hline(y=5, line_dash="dot", annotation_text="CC limit basis: 5%")
    fig.update_layout(height=360,margin=dict(l=45,r=20,t=45,b=45),xaxis_title="Flow Rate (gpm)",yaxis_title="Maximum Allowable ROP (m/hr)")
    return fig

def minflow_sensitivity_fig(df):
    import plotly.graph_objects as go
    fig=go.Figure()
    for col in df.columns[1:]:
        fig.add_trace(go.Scatter(x=df[col],y=df["Depth (m)"],mode="lines",name=col,hovertemplate=f"{col}<br>Minimum Flow: %{{x:.0f}} gpm<br>Depth: %{{y:.0f}} m<extra></extra>"))
    fig.update_layout(height=460,margin=dict(l=55,r=20,t=45,b=50),xaxis_title="Minimum Flowrate (gpm)",yaxis_title="Depth (m)",yaxis=dict(autorange="reversed"),hovermode="y unified",legend_title="ROP Sensitivity")
    return fig

def matplotlib_minflow(df,pc):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3)); v=df.dropna(); ax.plot(v.iloc[:,1],v.iloc[:,0],linewidth=2); ax.axhline(pc,linestyle="--",linewidth=1.2); ax.set_xlabel("Minimum Flowrate (gpm)"); ax.set_ylabel("Depth (m)"); ax.set_title("Minimum Flowrate vs Depth"); ax.invert_yaxis(); ax.grid(True,alpha=.25); fig.tight_layout(); return fig

def matplotlib_rop(df):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3)); v=df.dropna(); ax.plot(v.iloc[:,0],v.iloc[:,1],marker="o",linewidth=2); ax.set_xlabel("ROP (m/hr)"); ax.set_ylabel("Minimum Flowrate (gpm)"); ax.set_title("ROP vs Minimum Flowrate"); ax.grid(True,alpha=.25); fig.tight_layout(); return fig

def _report_plot_bytes(fig, dpi=150):
    import matplotlib.pyplot as plt
    bio=io.BytesIO(); fig.savefig(bio,format="png",dpi=dpi,bbox_inches="tight"); plt.close(fig); bio.seek(0); return bio

def report_rop_depth_matplotlib(df):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.2,4.0))
    for col in df.columns[1:]:
        ax.plot(df[col],df["Depth (m)"],linewidth=1.8,label=col)
    ax.set_xlabel("Maximum Allowable ROP (m/hr)"); ax.set_ylabel("Depth (m)")
    ax.set_title("Maximum Allowable ROP vs Depth — Flowrate Sensitivity")
    ax.invert_yaxis(); ax.grid(True,alpha=.25); ax.legend(fontsize=7,loc="best"); fig.tight_layout(); return fig

def report_minflow_rop_sensitivity_matplotlib(df):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.2,4.0))
    for col in df.columns[1:]:
        ax.plot(df[col],df["Depth (m)"],linewidth=1.8,label=col)
    ax.set_xlabel("Minimum Flowrate (gpm)"); ax.set_ylabel("Depth (m)")
    ax.set_title("Minimum Flowrate vs Depth — ROP Sensitivity")
    ax.invert_yaxis(); ax.grid(True,alpha=.25); ax.legend(fontsize=7,loc="best"); fig.tight_layout(); return fig

def make_pdf(r,meta,schematic,pressure_curve_df):
    from datetime import datetime
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image as RLImage,KeepTogether,LongTable
    from reportlab.lib.enums import TA_CENTER,TA_LEFT
    from reportlab.pdfbase.pdfmetrics import stringWidth
    import matplotlib.pyplot as plt

    PAGE_W,PAGE_H=A4
    margin_x=16*mm
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=margin_x,leftMargin=margin_x,topMargin=20*mm,bottomMargin=16*mm,title="Preliminary Drilling Hydraulic & Hole Cleaning Assessment",author=meta.get("prepared_by","Rigsis Drilling Team"))
    styles=getSampleStyleSheet()
    title=ParagraphStyle("ReportTitle",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=18,leading=22,alignment=TA_CENTER,textColor=colors.black,spaceAfter=5*mm)
    cover_sub=ParagraphStyle("CoverSub",parent=styles["BodyText"],fontName="Helvetica",fontSize=11,leading=15,alignment=TA_CENTER,textColor=colors.HexColor("#555555"))
    h1=ParagraphStyle("H1",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=15,leading=18,textColor=colors.HexColor("#202020"),spaceBefore=1*mm,spaceAfter=3*mm)
    h2=ParagraphStyle("H2",parent=styles["Heading2"],fontName="Helvetica-Bold",fontSize=10.5,leading=13,textColor=colors.HexColor("#222222"),spaceBefore=2*mm,spaceAfter=2*mm)
    body=ParagraphStyle("Body",parent=styles["BodyText"],fontName="Helvetica",fontSize=8.5,leading=12,textColor=colors.HexColor("#222222"),spaceAfter=2*mm)
    small=ParagraphStyle("Small",parent=body,fontSize=7,leading=9)
    tiny=ParagraphStyle("Tiny",parent=body,fontSize=8,leading=9.2)
    center=ParagraphStyle("Center",parent=body,alignment=TA_CENTER)
    table_head=ParagraphStyle("TableHead",parent=tiny,fontName="Helvetica-Bold",textColor=colors.white,leading=9.2)
    table_cell=ParagraphStyle("TableCell",parent=tiny,leading=9.2)

    logo_path=Path(__file__).parent/"assets"/"rigsis_logo.png"

    class NumberedCanvas(__import__("reportlab.pdfgen.canvas",fromlist=["Canvas"]).Canvas):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self._saved_page_states=[]
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
        def save(self):
            # Replay every saved page through ReportLab's normal showPage() path.
            # The previous implementation only called _startPage() while building
            # the original document, then called save() directly during replay.
            # That can produce a PDF with an invalid/empty page tree.
            total_pages=len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                if self._pageNumber>1:
                    self.setFont("Helvetica-Bold",8)
                    self.setFillColor(colors.HexColor("#222222"))
                    self.drawString(margin_x,PAGE_H-11*mm,"Preliminary Drilling Hydraulic & Hole Cleaning Assessment")
                    if logo_path.exists():
                        self.drawImage(str(logo_path),PAGE_W-margin_x-18*mm,PAGE_H-15.0*mm,width=18*mm,height=10.8*mm,mask='auto',preserveAspectRatio=True,anchor='sw')
                    self.setStrokeColor(colors.HexColor("#bdbdbd")); self.setLineWidth(.5)
                    self.line(margin_x,PAGE_H-15*mm,PAGE_W-margin_x,PAGE_H-15*mm)
                self.setFont("Helvetica",7); self.setFillColor(colors.HexColor("#666666"))
                self.drawString(margin_x,7*mm,f"Report Date: {meta['report_date']}")
                self.drawCentredString(PAGE_W/2,7*mm,meta['project'])
                self.drawRightString(PAGE_W-margin_x,7*mm,f"Page {self._pageNumber} of {total_pages}")
                __import__("reportlab.pdfgen.canvas",fromlist=["Canvas"]).Canvas.showPage(self)
            __import__("reportlab.pdfgen.canvas",fromlist=["Canvas"]).Canvas.save(self)

    def P(x,style=body):
        return Paragraph(str(x),style)

    def fmt(v,nd=2):
        try: return f"{float(v):,.{nd}f}"
        except Exception: return str(v)

    def df_table(df, widths=None, font=5.7, header_bg="#2b2b2b", repeat=1, wrap=True, highlight_columns=None, highlight_bg="#d9d9d9"):
        cols=list(df.columns)
        if widths:
            max_width=PAGE_W-2*margin_x
            total_width=sum(widths)
            if total_width>max_width:
                scale=max_width/total_width
                widths=[w*scale for w in widths]
        data=[[Paragraph(str(c),table_head) for c in cols]]
        for row in df.itertuples(index=False,name=None):
            cells=[]
            for v in row:
                txt="" if pd.isna(v) else str(v)
                cells.append(Paragraph(txt,table_cell if wrap else tiny))
            data.append(cells)
        cls=LongTable if len(data)>25 else Table
        t=cls(data,colWidths=widths,repeatRows=repeat,hAlign="LEFT")
        cmds=[("BACKGROUND",(0,0),(-1,0),colors.HexColor(header_bg)),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#b8b8b8")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),2.2),("RIGHTPADDING",(0,0),(-1,-1),2.2),("TOPPADDING",(0,0),(-1,-1),2.2),("BOTTOMPADDING",(0,0),(-1,-1),2.2)]
        for i in range(1,len(data)):
            if i%2==0: cmds.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor("#f6f6f6")))
        if highlight_columns:
            for col in highlight_columns:
                if col in cols:
                    j=cols.index(col)
                    cmds.append(("BACKGROUND",(j,1),(j,len(data)-1),colors.HexColor(highlight_bg)))
        t.setStyle(TableStyle(cmds)); return t

    def kv_table(rows):
        data=[[Paragraph("Parameter",table_head),Paragraph("Value",table_head)]]
        for k,v in rows: data.append([P(k,table_cell),P(v,table_cell)])
        t=Table(data,colWidths=[68*mm,104*mm],repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2b2b2b")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#b8b8b8")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f6f6f6")]),("FONTSIZE",(0,0),(-1,-1),7)])); return t

    story=[]
    # Cover page styled after the supplied Rigsis report: clean white page, centered identity block.
    story += [Spacer(1,42*mm)]
    if logo_path.exists():
        story.append(RLImage(str(logo_path),width=55*mm,height=33*mm,hAlign="CENTER"))
    else:
        story.append(Spacer(1,27*mm))
    story += [Spacer(1,20*mm),P("PRELIMINARY",title),P("DRILLING HYDRAULIC & HOLE CLEANING ASSESSMENT",title),Spacer(1,8*mm)]
    story += [P(f"<b>Well:</b> {meta['well_name']}",cover_sub),P(f"<b>Project / Field:</b> {meta['project']}",cover_sub),P(f"<b>Location:</b> {meta['location']}",cover_sub),Spacer(1,34*mm),P(f"Prepared by: {meta['prepared_by']}",cover_sub),P(f"Report Date: {meta['report_date']}",cover_sub),P(f"Report No.: {meta['report_number']}    Revision: {meta['revision']}",cover_sub),PageBreak()]

    # 1. Report Summary
    story += [P("1. Report Summary",h1)]
    summary_rows=[
        ("Project / Field Name",meta['project']),("Client / Company",meta['client']),("Location",meta['location']),
        ("Prepared By",meta['prepared_by']),("Report Number",meta['report_number']),("Revision",meta['revision']),
        ("Assessment Type",meta['assessment_type']),("Report Date",meta['report_date']),("Well Name",meta['well_name']),
        ("Total Depth",f"{r['td']:,.0f} m"),("Previous Casing Depth",f"{r['pc']:,.0f} m"),
        ("Final Inclination",f"{r.get('inc',0):,.1f}°"),("Flowrate",f"{r['Q']:,.0f} gpm"),("Total Pressure Loss",f"{r['pressure_df'].loc[r['pressure_df']['Section']=='Total Pressure Loss','Delta P (psi)'].iloc[0]:,.1f} psi"),("ROP",f"{r['rop']:,.1f} m/hr"),
        ("Maximum CC",f"{r['worst_cc']:,.2f} %"),("Minimum Transport Velocity",f"{r['worst_ct']:,.2f} ft/min"),
        ("Maximum Allowable ROP",f"{r['max_allowable_rop']:,.2f} m/hr"),("Minimum Flowrate",f"{r['minflow']['Minimum Flowrate (gpm)'].max():,.0f} gpm"),
        ("Limiting Criterion",r['limiting_criterion'])]
    story.append(kv_table(summary_rows)); story.append(Spacer(1,4*mm))
    story.append(P("This report presents a preliminary hydraulic and hole-cleaning assessment based on the Power Law rheology model and the screening criteria implemented in the online tool. Results are intended for engineering screening and should be verified against detailed hydraulics software, field data, and applicable standards before operational use.",body))

    story += [P("1.1 Mud Data",h2),df_table(pd.DataFrame([[fmt(r['mw'],1),fmt(r['r600'],0),fmt(r['r300'],0),fmt(r['pv'],1),fmt(r['yp'],1),fmt(r['n'],3),fmt(r['k'],5)]],columns=["MW (ppg)","R600","R300","PV (cP)","YP (lb/100 ft²)","n","k"]),widths=[24*mm]*7,highlight_columns=["PV (cP)","YP (lb/100 ft²)","n","k"],highlight_bg="#d2d2d2")]
    story += [P("1.2 Hole Section",h2),df_table(pd.DataFrame([["Casing",f"0–{r['pc']:.0f} m",f"{r['pc']:.0f} m",f"ID {r['casing']['id']:.3f} in"],["Open Hole",f"{r['pc']:.0f}–{r['td']:.0f} m",f"{r['td']-r['pc']:.0f} m",f"{r['oh']:.3f} in"]],columns=["Section","Depth","Length","ID / Hole Diameter"]),widths=[30*mm,48*mm,35*mm,55*mm])]
    dsrows=[["DP",fmt(r['dp_len'],0),f"0–{r['dp_len']:.0f}",fmt(r['dp_od'],3),fmt(r['dp_id'],3)],["HWDP",fmt(r['hwdp_len'],0),f"{r['dp_len']:.0f}–{r['dp_len']+r['hwdp_len']:.0f}",fmt(r['hwdp_od'],3),fmt(r['hwdp_id'],3)],["DC",fmt(r['dc_len'],0),f"{r['dp_len']+r['hwdp_len']:.0f}–{r['td']:.0f}",fmt(r['dc_od'],3),fmt(r['dc_id'],3)]]
    story += [P("1.3 Drillstring Component",h2),df_table(pd.DataFrame(dsrows,columns=["Type","Length (m)","Depth (m)","OD (in)","ID (in)"]),widths=[25*mm,30*mm,52*mm,30*mm,30*mm]),P(f"Tool Joint inputs: DP ITJ ID {r['dp_tj_id']:.3f} in | HWDP ITJ ID {r['hwdp_tj_id']:.3f} in | Average Joint Length {r['avg_joint_length']:.3f} m",small)]
    story += [P("1.4 Well Trajectory Summary",h2),df_table(r['traj'].round(2),widths=[24*mm,20*mm,19*mm,19*mm,24*mm,25*mm,25*mm,25*mm,22*mm]),PageBreak()]

    # 2. Methodology before Well Schematic, as requested.
    story += [P("2. Hydraulic & Hole Cleaning Methodology",h1)]
    methodology=[
        ("Fluid rheology", "Power Law model is derived from the input R600 and R300 readings. PV and YP are reported for reference, while the hydraulic calculation uses the Power Law parameters n and k."),
        ("Drillstring pressure loss", "Pressure loss is calculated for DP, HWDP and DC body sections using the Power Law formulation. DP and HWDP internal tool-joint (ITJ) losses are added using the implemented minor-loss correlation. DC ITJ loss is not included."),
        ("Annulus pressure loss", "Annular pressure loss is calculated by section using the applicable hole diameter and drillstring OD, including the casing/open-hole transition."),
        ("Bit hydraulics", "Bit pressure loss is calculated from flowrate, mud density, TFA and an internal discharge coefficient of 0.95. Bit HP, power at bit, nozzle velocity, HSI and impact force are then derived."),
        ("Hole-cleaning screening", "The tool evaluates each 30 m interval using three independent screening limits: Cutting Concentration ≤ 5%, Transport Velocity > 0 ft/min, and Annular Velocity ≥ 100 ft/min."),
        ("Hole-cleaning calculation method", "Annular Velocity is calculated from the flowrate and annular area using Va = 24.5Q/(Dh² − Dp²), with velocity in ft/min, Q in gpm, and diameters in inches. Cutting Concentration is calculated from the volumetric feed concentration Co and the net transport velocity: Co = [ROP(ft/hr)·Dh²/1471] / [ROP(ft/hr)·Dh²/1471 + Q], and CC = Co·Va/Vtransport. Transport Velocity is calculated as Vtransport = Va − Vslip, where Vslip is obtained from the implemented preliminary cutting-slip model using mud rheology, cutting size and density, and fluid density."),
        ("Minimum flowrate", "For each depth interval, minimum flowrate is searched from the annular-velocity floor upward until all three hole-cleaning criteria are satisfied."),
        ("Maximum allowable ROP", "At the selected flowrate, maximum allowable ROP is evaluated at each depth by solving the Cutting Concentration limit while also checking transport and annular-velocity conditions."),
    ]
    for name,desc in methodology:
        story += [P(f"<b>{name}</b>",body),P(desc,body)]
    story += [PageBreak()]

    # 3. Well schematic
    story += [P("3. Well Schematic",h1),P(f"{meta['well_name']} Well - Hole Section {r['oh']:.2f} in",ParagraphStyle("schemec",parent=center,fontSize=11,fontName="Helvetica-Bold")),Spacer(1,3*mm)]
    sb=io.BytesIO(); schematic.save(sb,format="PNG"); sb.seek(0); story += [RLImage(sb,width=105*mm,height=147*mm,hAlign="CENTER"),PageBreak()]

    # 4. Hydraulic setup and assessment result
    story += [P("4. Hydraulic Setup Data",h1),P("4.1 Setup Parameters",h2)]
    story += [df_table(pd.DataFrame([[fmt(r['Q'],0),fmt(r['tfa'],3),fmt(r['rop'],1),fmt(r['cutting_size'],3),fmt(r['cutting_sg'],2)]],columns=["Flowrate (gpm)","Bit TFA (in²)","ROP (m/hr)","Cutting Size (in)","Cutting Density (SG)"]),widths=[31*mm,32*mm,31*mm,39*mm,45*mm]),P("Bit discharge coefficient (Cd): 0.95",small)]
    story += [P("4.2 Equipment Pressure Loss",h2),df_table(pd.DataFrame([[fmt(r['surface'],1),fmt(r['motor'],1)]],columns=["Surface Line (psi)","Mud Motor (psi)"]),widths=[45*mm,45*mm]),Spacer(1,4*mm)]

    story += [P("5. Hydraulic & Hole Cleaning Assessment Results",h1),P("5.1 Pressure Loss Summary",h2)]
    # Keep bit separate from string in the summary.
    ps=r['pressure_df'].copy().rename(columns={"Delta P (psi)":"Pressure Loss (psi)"})
    story.append(df_table(ps.round(2),widths=[65*mm,42*mm,42*mm]))
    story += [P("5.2 String Pressure Loss Contributor",h2)]
    f=pie_fig(r['drill_labels'],r['drill_values'],"String Pressure Loss Contributor"); story.append(RLImage(_report_plot_bytes(f),width=82*mm,height=62*mm,hAlign="CENTER",kind="proportional"))
    story += [P("5.3 Annulus Pressure Loss Contributor",h2)]
    f=pie_fig(r['ann_labels'],r['ann_values'],"Annulus Pressure Loss Contributor"); story.append(RLImage(_report_plot_bytes(f),width=82*mm,height=62*mm,hAlign="CENTER",kind="proportional"))
    story += [PageBreak(),P("5.4 Flowrate vs Pressure Loss",h2)]
    f=interactive_pressure_matplotlib(pressure_curve_df,r['Q']); story.append(RLImage(_report_plot_bytes(f),width=170*mm,height=62*mm,hAlign="CENTER"))
    story += [P("5.5 Bit Summary",h2),df_table(pd.DataFrame([[fmt(r['bit_hp'],1),fmt(r['bit_power'],1),fmt(r['nozzle_v'],1),fmt(r['hsi'],2),fmt(r['impact'],1)]],columns=["Bit HP","% Power at Bit","Nozzle Velocity (ft/s)","HSI (hp/in²)","Impact Force (lbf)"]),widths=[32*mm,34*mm,38*mm,32*mm,38*mm]),P(f"Bit hydraulics: Cd = 0.95 | Hole area = {r['hole_area']:.2f} in².",small),Spacer(1,4*mm)]

    # 6. Hole Cleaning Summary, with both sensitivity charts used by the tool.
    story += [P("6. Hole Cleaning Summary",h1)]
    hc_summary_rows=[
        ("Maximum CC (%)",fmt(r['worst_cc'],2)),
        ("MD at Max CC (m)",fmt(r['worst_cc_md'],0)),
        ("Minimum Transport Velocity (ft/min)",fmt(r['worst_ct'],2)),
        ("MD at Min CTV (m)",fmt(r['worst_ct_md'],0)),
        ("Maximum Allowable ROP (m/hr)",fmt(r['max_allowable_rop'],2)),
        ("Minimum Flowrate (gpm)",fmt(r['minflow']['Minimum Flowrate (gpm)'].max(),0)),
        ("Limiting Criterion",r['limiting_criterion'])]
    story.append(kv_table(hc_summary_rows))
    story += [P("6.1 Maximum Allowable ROP vs Depth — Flowrate Sensitivity",h2)]
    f=report_rop_depth_matplotlib(r['rop_depth_df']); story.append(RLImage(_report_plot_bytes(f),width=170*mm,height=82*mm,hAlign="CENTER"))
    story += [PageBreak(),P("6.2 Minimum Flowrate vs Depth — ROP Sensitivity",h2)]
    f=report_minflow_rop_sensitivity_matplotlib(r['minflow_sens_df']); story.append(RLImage(_report_plot_bytes(f),width=170*mm,height=82*mm,hAlign="CENTER"))
    story += [P("Screening limits: Cutting Concentration ≤ 5% | Transport Velocity > 0 ft/min | Annular Velocity ≥ 100 ft/min",small),Spacer(1,4*mm)]

    # 7. Detailed Assessment Result — requested tables included.
    story += [PageBreak(),P("7. Attachment - Detailed Assessment Result",h1),P(f"7.1 Maximum Allowable ROP by Depth at {r['Q']:,.0f} gpm",h2)]
    story.append(df_table(r['rop_limit_df'].round(2),widths=[20*mm,22*mm,31*mm,28*mm,31*mm,29*mm,39*mm]))
    story += [P("7.2 Minimum Flowrate by Depth",h2)]
    story.append(df_table(r['minflow'].round(2),widths=[28*mm,48*mm,62*mm]))
    story += [P("7.3 Drillstring Pressure Loss — Detailed (DP/HWDP Body + ITJ + DC)",h2),P(f"ITJ inputs: DP ID {r['dp_tj_id']:.3f} in | HWDP ID {r['hwdp_tj_id']:.3f} in | Average Joint Length {r['avg_joint_length']:.3f} m | Total Internal ITJ Loss {r['tj_loss']:.1f} psi",small)]
    prows=pd.DataFrame(r['prows'],columns=["Component","Length / Connections","ID (in)","Velocity (ft/s)","Reynolds","Flow Regime / TJ K","Fanning f / Ktj","Pressure Loss (psi)"]).round(2)
    story.append(df_table(prows,widths=[24*mm,30*mm,20*mm,25*mm,25*mm,34*mm,26*mm,22*mm]))
    story += [P("7.4 Annulus Pressure Loss — Detailed",h2)]
    arows=pd.DataFrame(r['arows'],columns=["Component","MD From (m)","MD To (m)","Length (m)","Hole ID (in)","Pipe OD (in)","Section","Velocity (ft/s)","Reynolds","Flow Regime","Fanning f","Pressure Loss (psi)"]).round(2)
    story.append(df_table(arows,widths=[22*mm,18*mm,18*mm,18*mm,22*mm,20*mm,23*mm,24*mm,23*mm,24*mm,20*mm,20*mm]))
    story += [P("7.5 Hole Cleaning — 30 m Interval",h2)]
    story.append(df_table(r['hc_df'].drop(columns=['Transport Ratio']).round(2),widths=[17*mm,18*mm,23*mm,26*mm,19*mm,18*mm,24*mm,25*mm,27*mm,24*mm,20*mm,18*mm]))

    doc.build(story,canvasmaker=NumberedCanvas)
    buf.seek(0); return buf.getvalue()

def rop_depth_fig(df):
    import plotly.graph_objects as go
    fig=go.Figure()
    for col in df.columns[1:]:
        fig.add_trace(go.Scatter(x=df[col],y=df["Depth (m)"],mode="lines",name=col,hovertemplate=f"{col}<br>Max ROP: %{{x:.2f}} m/hr<br>Depth: %{{y:.0f}} m<extra></extra>"))
    fig.update_layout(height=460,margin=dict(l=55,r=20,t=45,b=50),xaxis_title="Maximum Allowable ROP (m/hr)",yaxis_title="Depth (m)",yaxis=dict(autorange="reversed"),hovermode="y unified",legend_title="Flowrate")
    return fig

def rop_envelope_fig(df):
    import plotly.graph_objects as go
    fig=go.Figure()
    v=df[df["Hydraulically Feasible"] & df["Maximum Allowable ROP (m/hr)"].notna()]
    if len(v):
        fig.add_trace(go.Scatter(x=v["Flow Rate (gpm)"],y=v["Maximum Allowable ROP (m/hr)"],mode="lines+markers",name="Max Allowable ROP",hovertemplate="Flow: %{x:.0f} gpm<br>Max ROP: %{y:.1f} m/hr<extra></extra>"))
    fig.update_layout(height=360,margin=dict(l=45,r=20,t=45,b=45),xaxis_title="Flow Rate (gpm)",yaxis_title="Maximum Allowable ROP (m/hr)",hovermode="x unified")
    return fig

def interactive_pressure_matplotlib(df,Q):
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,3)); ax.plot(df.iloc[:,0],df.iloc[:,1],linewidth=2); row=df.iloc[(df.iloc[:,0]-Q).abs().argmin()]; ax.scatter([Q],[row.iloc[1]],s=28); ax.set_xlabel("Flow Rate (gpm)"); ax.set_ylabel("Pressure Loss (psi)"); ax.grid(True,alpha=.25); fig.tight_layout(); return fig

# ---------------- INPUTS ----------------
left,mid,right=st.columns([.27,.43,.30],gap="small")
with left:
    st.markdown('<div class="section">1. Well Geometry</div>',unsafe_allow_html=True)
    td=st.number_input("Total Depth (TD), m",1.,15000.,2500.,50.)
    previous_casing_depth=st.number_input("Previous Casing Depth, m",1.,15000.,1000.,50.)
    kop=st.number_input("KOP, m",0.,14000.,400.,50.)
    eob=st.number_input("EOB, m",0.,14000.,700.,50.)
    inc=st.number_input("Final Inclination, °",0.,90.,30.,1.)
    casing_spec=st.selectbox("Previous Casing Spec",list(API_CASING.keys()),index=list(API_CASING.keys()).index("13-3/8 in × 72.00 lb/ft"))
    casing_data=API_CASING[casing_spec]; st.caption(f"OD {casing_data['od']:.3f} in | ID {casing_data['id']:.3f} in | Drift {casing_data['drift']:.3f} in")
    oh_hole=st.number_input("Open Hole Size, in",1.,30.,12.25,.25)
    st.markdown('<div class="section">2. Drill String Components</div>',unsafe_allow_html=True)
    dc_len=st.number_input("Drill Collar (DC) length, m",0.,10000.,200.,50.); dc_id=st.number_input("DC ID, in",.1,15.,2.750,.001,format="%.3f"); dc_od=st.number_input("DC OD, in",.1,20.,8.000,.001,format="%.3f")
    hwdp_len=st.number_input("HWDP length, m",0.,10000.,300.,50.); hwdp_id=st.number_input("HWDP ID, in",.1,15.,3.000,.001,format="%.3f"); hwdp_od=st.number_input("HWDP OD, in",.1,20.,5.000,.001,format="%.3f"); hwdp_tj_id=st.number_input("HWDP Tool Joint ID, in",.1,15.,3.063,.001,format="%.3f")
    dp_len=max(td-dc_len-hwdp_len,0.); st.number_input("Drill Pipe (DP) length, m",value=float(dp_len),disabled=True); dp_id=st.number_input("DP ID, in",.1,15.,4.276,.001,format="%.3f"); dp_od=st.number_input("DP OD, in",.1,20.,5.000,.001,format="%.3f"); dp_tj_id=st.number_input("DP Tool Joint ID, in",.1,15.,3.500,.001,format="%.3f")
    avg_joint_length=st.number_input("Average Joint Length, m",1.,20.,9.144,.001)
with mid:
    st.markdown('<div class="section">Well Schematic</div>',unsafe_allow_html=True); st.image(render_schematic(td,previous_casing_depth,dp_len,hwdp_len,dc_len),use_container_width=True); st.caption(f"J-Type profile | TD {td:,.0f} m | KOP {kop:,.0f} m | EOB {eob:,.0f} m | Final Inclination {inc:.1f}°")
with right:
    st.markdown('<div class="result">3. Mud Properties</div>',unsafe_allow_html=True)
    mw=st.number_input("Mud Weight (MW), ppg",1.,25.,9.2,.1); r600=st.number_input("R600",.1,500.,50.,1.); r300=st.number_input("R300",.1,500.,40.,1.)
    try:
        n,k=pl(r600,r300); pv=r600-r300; yp=2*r300-r600; st.write(f"**PV:** {pv:.1f} cP"); st.write(f"**YP:** {yp:.1f} lb/100 ft²"); st.write(f"**Power Law n:** {n:.3f}"); st.write(f"**Power Law k:** {k:.5f}")
    except ValueError as e: n=k=None; pv=yp=None; st.error(str(e))
    st.markdown('<div class="result">4. Flow Rate & Bit</div>',unsafe_allow_html=True); Q=st.number_input("Flow Rate, gpm",1.,5000.,900.,10.); tfa=st.number_input("Bit TFA, in²",.001,10.,2.086,.001,format="%.3f")
    st.markdown('<div class="result">5. Equipment Pressure Loss</div>',unsafe_allow_html=True); surface=st.number_input("Surface Line Pressure Loss, psi",0.,10000.,100.,10.); motor=st.number_input("Mud Motor Pressure Loss, psi",0.,10000.,0.,10.)
    st.markdown('<div class="result">6. Hole Cleaning Input</div>',unsafe_allow_html=True); rop=st.number_input("Rate of Penetration (ROP), m/hr",.1,500.,8.,1.); cutting_size=st.number_input("Cutting Size, in",.001,2.,.250,.001,format="%.3f"); cutting_sg=st.number_input("Cutting Density, SG",.1,5.,2.65,.01)

st.markdown('<div class="section">7. Report Information</div>',unsafe_allow_html=True)
ri1,ri2,ri3,ri4=st.columns(4)
with ri1: well_name=st.text_input("Well Name",value="WP07"); project=st.text_input("Project / Field Name",value="KKI Make-up Well Patuha 2026")
with ri2: client=st.text_input("Client / Company",value="Geo Dipa Energi"); location=st.text_input("Location",value="Patuha, West Java")
with ri3: prepared_by=st.text_input("Prepared By",value="Rigsis Drilling Team"); report_number=st.text_input("Report Number",value="1")
with ri4: revision=st.text_input("Revision",value="0"); st.text_input("Assessment Type",value="Preliminary Hydraulic & Hole Cleaning Assessment",disabled=True)
report_date=date.today()
st.caption(f"Report Date: {report_date.strftime("%d/%m/%Y")} (automatic)")

if "calc" not in st.session_state: st.session_state.calc=None
p={"td":td,"pc":previous_casing_depth,"kop":kop,"eob":eob,"inc":inc,"casing":casing_data,"oh":oh_hole,"dc_len":dc_len,"dc_id":dc_id,"dc_od":dc_od,"hwdp_len":hwdp_len,"hwdp_id":hwdp_id,"hwdp_od":hwdp_od,"hwdp_tj_id":hwdp_tj_id,"dp_id":dp_id,"dp_od":dp_od,"dp_tj_id":dp_tj_id,"avg_joint_length":avg_joint_length,"mw":mw,"r600":r600,"r300":r300,"Q":Q,"tfa":tfa,"surface":surface,"motor":motor,"rop":rop,"cutting_size":cutting_size,"cutting_sg":cutting_sg}

if st.button("Calculate Hydraulic Pressure",type="primary",use_container_width=True):
    if not (kop<eob<td and previous_casing_depth<td): st.error("Check KOP, EOB, casing depth, and TD.")
    else: st.session_state.calc=calculate(p)

r=st.session_state.calc
if r:
    st.divider(); st.markdown('<div class="result">Hydraulic & Hole Cleaning Assessment Results</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([.34,.33,.33],gap="small")
    with c1:
        st.markdown("**Pressure Loss Summary**")
        st.dataframe(r["pressure_df"].style.format({"Delta P (psi)":"{:,.1f}","% of Total":"{:,.1f}%"}),use_container_width=True,hide_index=True)
    with c2:
        st.markdown("**String Pressure Loss Contributor**")
        st.pyplot(pie_fig(r["drill_labels"],r["drill_values"],"String Pressure Loss Contributor"),use_container_width=True)
    with c3:
        st.markdown("**Annulus Pressure Loss Contributor**")
        st.pyplot(pie_fig(r["ann_labels"],r["ann_values"],"Annulus Pressure Loss Contributor"),use_container_width=True)

    st.markdown("**Bit Summary**")
    bs=st.columns(5)
    for i,(lbl,val) in enumerate([("Bit HP",f"{r['bit_hp']:,.1f}"),("% Power at Bit",f"{r['bit_power']:,.1f}%"),("Nozzle Velocity",f"{r['nozzle_v']:,.0f} ft/s"),("HSI",f"{r['hsi']:,.1f} hp/in²"),("Impact Force",f"{r['impact']:,.0f} lbf")]):
        bs[i].metric(lbl,val)
    st.caption(f"Bit hydraulics: Cd = 0.95 | Hole area = {r['hole_area']:,.2f} in² | HSI based on hole area")

    st.markdown("**Hole Cleaning Summary**")
    hca,hcb,hcc,hcd,hce=st.columns(5)
    hca.metric("Maximum CC",f"{r['worst_cc']:,.2f} %")
    hcb.metric("Minimum Transport Velocity",f"{r['worst_ct']:,.2f} ft/min")
    hcc.metric("Maximum Allowable ROP",f"{r['max_allowable_rop']:,.2f} m/hr")
    hcd.metric("Minimum Flowrate",f"{r['minflow']['Minimum Flowrate (gpm)'].max():,.0f} gpm")
    with hce:
        st.markdown(f"""<div style='border:1px solid rgba(250,250,250,.35);border-radius:8px;padding:8px 10px;min-height:88px;box-sizing:border-box;'>
<div style='font-size:0.82rem;color:rgba(250,250,250,.72);margin-bottom:4px;'>Limiting Criterion</div>
<div style='font-size:1.15rem;line-height:1.18;white-space:normal;overflow-wrap:anywhere;word-break:break-word;'>{r['limiting_criterion']}</div>
</div>""",unsafe_allow_html=True)
    st.caption("Screening limits: Cutting Concentration ≤ 5% | Transport Velocity > 0 ft/min | Annular Velocity ≥ 100 ft/min")

    st.markdown("**Flowrate vs Pressure Loss**")
    qmax=max(1000.,Q*1.75,2000.)
    flows=[max(50.,qmax*i/30) for i in range(1,31)]
    flows=sorted(set(flows+[Q]))
    curve=pressure_curve(flows,(mw,n,k,r["dp_len"],dp_id,dp_tj_id,avg_joint_length,hwdp_len,hwdp_id,hwdp_tj_id,dc_len,dc_id,previous_casing_depth,casing_data,oh_hole,dp_od,hwdp_od,dc_od,tfa,surface,motor))
    st.plotly_chart(interactive_pressure(curve,Q),use_container_width=True,key="pressure_loss_vs_flowrate")

    st.markdown("**Maximum Allowable ROP vs Depth**")
    st.plotly_chart(rop_depth_fig(r["rop_depth_df"]),use_container_width=True,key="max_rop_vs_depth")
    st.markdown("**Minimum Flowrate vs Depth**")
    st.plotly_chart(minflow_sensitivity_fig(r["minflow_sens_df"]),use_container_width=True,key="minimum_flowrate_vs_depth")

    st.markdown('<div class="result">Detailed Pressure Loss & Hole Cleaning</div>',unsafe_allow_html=True)
    traj_display=r["traj"]
    st.markdown("**Well Trajectory Summary — Minimum Curvature Method**")
    st.dataframe(traj_display.style.format({c:"{:,.2f}" for c in traj_display.columns if c!="Point"}),use_container_width=True,hide_index=True)
    st.markdown("**Drillstring Pressure Loss — Detailed (DP/HWDP Body + ITJ + DC)**")
    tjc1,tjc2,tjc3,tjc4=st.columns(4)
    tjc1.metric("Total ITJ Loss",f"{r['tj_loss']:,.1f} psi")
    tjc2.metric("Average Joint Length",f"{avg_joint_length:,.3f} m")
    tjc3.metric("DP ITJ ID",f"{dp_tj_id:.3f} in")
    tjc4.metric("HWDP ITJ ID",f"{hwdp_tj_id:.3f} in")
    st.dataframe(pd.DataFrame(r["prows"],columns=["Component","Length / Connections","ID (in)","Velocity (ft/s)","Reynolds","Flow Regime / TJ K","Fanning f / Ktj","Pressure Loss (psi)"]).style.format({"Length / Connections":"{:,.1f}","ID (in)":"{:,.3f}","Velocity (ft/s)":"{:,.2f}","Reynolds":"{:,.0f}","ΔP (psi)":"{:,.1f}"}),use_container_width=True,hide_index=True)
    st.markdown("**Annulus Pressure Loss — Detailed**")
    st.dataframe(pd.DataFrame(r["arows"],columns=["Component","MD From (m)","MD To (m)","Length (m)","Hole ID (in)","Pipe OD (in)","Section","Velocity (ft/s)","Reynolds","Flow Regime","Fanning f","Pressure Loss (psi)"]).style.format({"MD From (m)":"{:,.0f}","MD To (m)":"{:,.0f}","Length (m)":"{:,.1f}","Hole ID (in)":"{:,.3f}","Pipe OD (in)":"{:,.3f}","Velocity (ft/s)":"{:,.2f}","Reynolds":"{:,.0f}","Fanning f":"{:,.4f}","ΔP (psi)":"{:,.1f}"}),use_container_width=True,hide_index=True)
    st.markdown("**Hole Cleaning — 30 m Interval**")
    st.dataframe(r["hc_df"].drop(columns=["Transport Ratio"]).style.format({c:"{:,.2f}" for c in r["hc_df"].columns if c not in ["Section","Drillstring Component"]}),use_container_width=True,hide_index=True)
    st.markdown("**Maximum Allowable ROP by Depth — Current Input Flowrate**")
    st.dataframe(r["rop_limit_df"].style.format({c:"{:,.2f}" for c in r["rop_limit_df"].columns if c not in ["Limiting Criterion"]}),use_container_width=True,hide_index=True)
    st.markdown("**Minimum Flowrate by Depth**")
    st.dataframe(r["minflow"].style.format({"Depth (m)":"{:,.0f}","Minimum Flowrate (gpm)":"{:,.1f}"}),use_container_width=True,hide_index=True)

    st.divider(); st.markdown("### Generate Report")
    if st.button("Generate PDF Report",type="secondary",use_container_width=True):
        meta={"well_name":well_name,"project":project,"client":client,"location":location,"prepared_by":prepared_by,"report_number":report_number,"revision":revision,"report_date":report_date.strftime("%d %B %Y"),"assessment_type":"Preliminary Hydraulic & Hole Cleaning Assessment"}
        r["well_name"]=well_name; r["inc"]=inc; r["traj"]=traj_display; r["pc"]=previous_casing_depth; r["td"]=td; r["oh"]=oh_hole; r["casing"]=casing_data; r["mw"]=mw; r["r600"]=r600; r["r300"]=r300; r["pv"]=r["pv"]; r["yp"]=r["yp"]; r["n"]=r["n"]; r["k"]=r["k"]; r["Q"]=Q; r["tfa"]=tfa; r["rop"]=rop; r["cutting_size"]=cutting_size; r["cutting_sg"]=cutting_sg; r["surface"]=surface; r["motor"]=motor; r["drill_labels"]=r["drill_labels"]; r["drill_values"]=r["drill_values"]; r["ann_labels"]=r["ann_labels"]; r["ann_values"]=r["ann_values"]; r["dp_len"]=r["dp_len"]; r["hwdp_len"]=hwdp_len; r["dc_len"]=dc_len; r["dp_od"]=dp_od; r["dp_id"]=dp_id; r["hwdp_od"]=hwdp_od; r["hwdp_id"]=hwdp_id; r["dc_od"]=dc_od; r["dc_id"]=dc_id; r["avg_joint_length"]=avg_joint_length; r["dp_tj_id"]=dp_tj_id; r["hwdp_tj_id"]=hwdp_tj_id
        pdf=make_pdf(r,meta,render_schematic(td,previous_casing_depth,r["dp_len"],hwdp_len,dc_len),curve); st.download_button("Download PDF Report",data=pdf,file_name=f"{well_name}_PDHA_Report_Rev{revision}.pdf",mime="application/pdf",use_container_width=True)

st.caption("Preliminary engineering assessment only. Hydraulic equations and hole-cleaning correlations should be verified against licensed API RP 13D and applicable field/vendor data before operational use.")
