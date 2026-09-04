"""Generate the four presentation-critical GlobalPay diagrams as editable SVG files."""

from html import escape
from pathlib import Path

OUT = Path(__file__).parent
W, H = 1600, 900
NAVY, BLUE, PURPLE = "#1e2761", "#1677d2", "#7952b3"
TEAL, PEACH, GOLD = "#dff5f1", "#fde7df", "#fff2cc"
INK, MUTED, LINE = "#172033", "#596579", "#738096"


def start(title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<rect width="1600" height="900" fill="white"/>',
        '<rect width="14" height="900" fill="#1e2761"/>',
        f'<text x="55" y="66" font-family="Arial" font-size="34" font-weight="700" fill="{NAVY}">{escape(title)}</text>',
        f'<text x="56" y="98" font-family="Arial" font-size="17" fill="{MUTED}">{escape(subtitle)}</text>',
        '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#596579"/></marker></defs>',
    ]


def box(parts, x, y, w, h, title, lines=(), fill="#f6f7fb", stroke=PURPLE, title_size=20, body_size=15):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    parts.append(f'<text x="{x+w/2}" y="{y+30}" text-anchor="middle" font-family="Arial" font-size="{title_size}" font-weight="700" fill="{NAVY}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x+16}" y="{y+58+i*23}" font-family="Arial" font-size="{body_size}" fill="{INK}">{escape(line)}</text>')


def arrow(parts, x1, y1, x2, y2, label="", dashed=False, label_y=-8):
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"{dash}/>')
    if label:
        parts.append(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2+label_y}" text-anchor="middle" font-family="Arial" font-size="14" fill="{MUTED}">{escape(label)}</text>')


def finish(parts, name):
    parts.append('</svg>')
    (OUT / name).write_text('\n'.join(parts), encoding='utf-8')


def dfd0():
    p = start("Data Flow Diagram — Level 0", "Context view: GlobalPay is one process; only external actors and exchanged information are shown")
    box(p, 610, 330, 380, 190, "0 · GlobalPay Platform", ["Wallets · Payments · Fraud", "Open Banking · CBDC · Reporting"], TEAL, BLUE, 26, 19)
    actors = [(90,170,"Customer",["registration / login","wallet and payment requests"]),(90,610,"Merchant",["merchant payment status","settlement report"]),(1230,150,"Third-party app",["consent-based AIS/PIS","API requests"]),(1230,600,"Fraud analyst",["alert review","decision and notes"]),(620,680,"Executive",["KPI and report request","read-only results"])]
    for x,y,t,ls in actors: box(p,x,y,280,115,t,ls,"#f7f7f8","#a8b0bd",20,15)
    arrow(p,370,225,610,375,"requests") ; arrow(p,610,440,370,250,"balances / confirmations")
    arrow(p,370,665,610,470,"report request") ; arrow(p,610,500,370,700,"receipts / settlement view")
    arrow(p,1230,210,990,375,"AIS / PIS / CBDC") ; arrow(p,990,410,1230,245,"API response")
    arrow(p,1230,655,990,455,"review decision") ; arrow(p,990,485,1230,690,"alerts / cases")
    arrow(p,800,680,800,520,"KPI query") ; arrow(p,850,520,850,680,"report")
    p.append(f'<text x="800" y="845" text-anchor="middle" font-family="Arial" font-size="15" fill="{MUTED}">Boundary rule: databases and internal services do not appear in a Level 0 context diagram.</text>')
    finish(p,"dfd-level-0.svg")


def dfd1():
    p = start("Data Flow Diagram — Level 1", "GlobalPay decomposed into five processes with external actors, named flows and persistent data stores")
    processes=[(70,"1.0 Identity & Wallets"),(370,"2.0 Payments"),(670,"3.0 Fraud Review"),(970,"4.0 Open Banking / CBDC"),(1270,"5.0 Reporting")]
    for x,t in processes: box(p,x,245,250,105,t,(),"#eee7f8",PURPLE,18)
    stores=[(70,"D1 Users / Wallets"),(370,"D2 Transactions / Ledger"),(670,"D3 Alerts / Cases"),(970,"D4 Consents / API / CBDC"),(1270,"D5 Audit / Model Data")]
    for x,t in stores: box(p,x,520,250,78,t,(),PEACH,"#d98c72",17)
    box(p,55,680,280,95,"Customer / Merchant",["requests and views"],"#f7f7f8","#a8b0bd",19)
    box(p,655,680,280,95,"Fraud analyst",["review decisions"],"#f7f7f8","#a8b0bd",19)
    box(p,1260,680,280,95,"Executive",["read-only reports"],"#f7f7f8","#a8b0bd",19)
    for x,_ in processes: arrow(p,x+125,350,x+125,520,"read / write")
    arrow(p,320,298,370,298,"wallet / payer") ; arrow(p,620,298,670,298,"transaction") ; arrow(p,920,298,970,298,"decision") ; arrow(p,1220,298,1270,298,"activity")
    arrow(p,195,680,195,598,"register / pay") ; arrow(p,795,680,795,598,"review") ; arrow(p,1400,680,1400,598,"query")
    arrow(p,1270,430,320,430,"on-demand KPI reads from D1–D4",True)
    finish(p,"dfd-level-1.svg")


def erd():
    p = start("Database Entity Relationship Diagram", "Core operational relationships; crow's-foot labels show one-to-one, one-to-many and optional links")
    entities={
      "User":(45,160,["PK id","email · role"]), "Customer":(285,125,["PK id","FK user_id"]), "Merchant":(285,275,["PK id","FK user_id"]),
      "Wallet":(555,190,["PK id","FK customer_id?","FK merchant_id?"]), "Transaction":(825,190,["PK id","FK sender_wallet_id?","FK receiver_wallet_id?"]),
      "LedgerEntry":(1095,120,["PK id","FK transaction_id","FK wallet_id"]), "FraudAlert":(1095,320,["PK id","FK transaction_id"]),
      "Investigation":(1365,320,["PK id","FK alert_id","FK analyst_user_id"]), "Consent":(555,500,["PK id","FK customer_id"]),
      "ApiCall":(825,500,["PK id","FK consent_id?"]), "CbdcWallet":(555,680,["PK id","FK customer_id?"]), "CbdcOperation":(825,680,["PK id","FK source/destination"]),
      "AuditLog":(1095,680,["PK id","FK actor_user_id?"]), "ModelRegistry":(1365,680,["PK id","version · metrics"]),
    }
    sizes={name:(205,112 if len(lines)<=2 else 135) for name,(_,_,lines) in entities.items()}
    for name,(x,y,lines) in entities.items(): box(p,x,y,*sizes[name],name,lines,"#fbf9ff",PURPLE,18,14)
    def rel(a,b,ca,cb,label=""):
        ax,ay,_=entities[a]; aw,ah=sizes[a]; bx,by,_=entities[b]; bw,bh=sizes[b]
        x1,y1=ax+aw,ay+ah/2; x2,y2=bx,by+bh/2
        arrow(p,x1,y1,x2,y2,label,label_y=-6)
        p.append(f'<text x="{x1+7}" y="{y1-8}" font-family="Arial" font-size="13" fill="{NAVY}">{ca}</text><text x="{x2-35}" y="{y2-8}" font-family="Arial" font-size="13" fill="{NAVY}">{cb}</text>')
    rel("User","Customer","1","0..1"); rel("User","Merchant","1","0..1"); rel("Customer","Wallet","1","0..1"); rel("Merchant","Wallet","1","0..1")
    rel("Wallet","Transaction","1","0..*",""); rel("Transaction","LedgerEntry","1","2..*",""); rel("Transaction","FraudAlert","1","0..1",""); rel("FraudAlert","Investigation","1","0..*","")
    rel("Customer","Consent","1","0..*",""); rel("Consent","ApiCall","1","0..*",""); rel("Customer","CbdcWallet","1","0..*",""); rel("CbdcWallet","CbdcOperation","1","0..*","")
    p.append(f'<rect x="1095" y="825" width="475" height="45" rx="10" fill="{GOLD}" stroke="#d4aa35"/><text x="1112" y="853" font-family="Arial" font-size="14" fill="{INK}">AuditLog and ModelRegistry are supporting governance records.</text>')
    finish(p,"database-erd.svg")


def network():
    p=start("Enterprise Network Architecture","Laptop deployment: zones, exposed ports, protocols and trust boundaries derived from compose.yaml")
    p.append('<rect x="45" y="130" width="1510" height="130" rx="14" fill="#f3f5f8" stroke="#aab3c2" stroke-width="2"/><text x="65" y="158" font-family="Arial" font-size="17" font-weight="700" fill="#596579">EXTERNAL / HOST ZONE</text>')
    box(p,90,175,260,65,"User web browser",(),"white","#a8b0bd",20); box(p,1240,175,260,65,"Operations browser",(),"white","#a8b0bd",20)
    p.append(f'<text x="800" y="278" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="{MUTED}">HOST FIREWALL / DOCKER PORT-PUBLISHING BOUNDARY</text>')
    p.append('<rect x="45" y="285" width="1510" height="155" rx="14" fill="#fff6dd" stroke="#d4aa35" stroke-width="2"/><text x="65" y="315" font-family="Arial" font-size="17" font-weight="700" fill="#8a6710">EDGE / EXPOSED SERVICES</text>')
    box(p,310,335,330,75,"Nginx frontend",["host :3000 → container :80"],"white","#d4aa35",20); box(p,960,335,330,75,"Monitoring UI",["Grafana :3001 · Prometheus :9090"],"white","#d4aa35",20)
    p.append('<rect x="45" y="465" width="1510" height="155" rx="14" fill="#e7f7f3" stroke="#3b9f8c" stroke-width="2"/><text x="65" y="495" font-family="Arial" font-size="17" font-weight="700" fill="#237667">PRIVATE APPLICATION ZONE · globalpay-net</text>')
    box(p,310,520,330,75,"FastAPI backend",["container :8000 · 9 routers"],"white","#3b9f8c",20); box(p,960,520,330,75,"Metrics endpoint",["Prometheus scrapes /metrics"],"white","#3b9f8c",20)
    p.append('<rect x="45" y="645" width="1510" height="155" rx="14" fill="#fcebe5" stroke="#d98c72" stroke-width="2"/><text x="65" y="675" font-family="Arial" font-size="17" font-weight="700" fill="#9a513a">PRIVATE DATA ZONE · NOT HOST-EXPOSED</text>')
    box(p,245,700,330,75,"PostgreSQL 16",["TCP 5432 · authoritative data"],"white","#d98c72",20); box(p,675,700,300,75,"Redis 7",["TCP 6379 · cache / rate limit"],"white","#d98c72",20); box(p,1075,700,300,75,"Persistent volumes",["database · model · metrics"],"white","#d98c72",20)
    arrow(p,350,207,475,335,"HTTP :3000") ; arrow(p,475,410,475,520,"HTTP /api") ; arrow(p,475,595,410,700,"SQL/TCP 5432") ; arrow(p,580,595,825,700,"Redis/TCP 6379")
    arrow(p,1240,207,1125,335,"HTTP dashboards") ; arrow(p,1125,520,1125,410,"metrics / dashboards") ; arrow(p,960,557,640,557,"HTTP scrape")
    p.append(f'<text x="800" y="850" text-anchor="middle" font-family="Arial" font-size="15" fill="{MUTED}">Security boundary: only host-mapped ports are externally reachable; PostgreSQL and Redis remain inside the Docker bridge network.</text>')
    finish(p,"network-architecture.svg")


dfd0(); dfd1(); erd(); network()
