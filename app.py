from pathlib import Path
import base64

import streamlit as st


st.set_page_config(page_title="점심 메뉴 룰렛", page_icon="🍽️", layout="wide")
st.title("점심 메뉴 룰렛")
st.caption("오늘 점심 고민은 여기까지. 8가지 메뉴 중 하나를 골라보세요.")

# 실행 위치와 관계없이 app.py 옆의 이미지 폴더를 사용합니다.
BASE_DIR = Path(__file__).resolve().parent
MENUS = [
    ("김치찌개", "img/01_gimchi.jpg"),
    ("제육볶음", "img/02_jeyuk.jpg"),
    ("돈가스", "img/03_dongas.jpg"),
    ("라면김밥", "img/04_lamen.jpg"),
    ("햄버거", "img/05_hamberger.jpg"),
    ("뼈해장국", "img/06_hejang.jpg"),
    ("카레", "img/07_curry.jpg"),
    ("비빔밥", "img/08_bibim.jpg"),
]


def load_menus():
    """사진이 없어도 메뉴 선택은 계속 사용할 수 있습니다."""
    items = []
    for name, relative_path in MENUS:
        try:
            encoded = base64.b64encode((BASE_DIR / relative_path).read_bytes()).decode("ascii")
            photo = f"data:image/jpeg;base64,{encoded}"
        except OSError:
            photo = None
        items.append({"name": name, "path": relative_path, "photo": photo})
    return items


# 애니메이션과 완료 시점을 함께 관리하는 Streamlit v2 컴포넌트입니다.
ROULETTE = st.components.v2.component(
    "lunch_roulette",
    html="""
    <main class="layout">
      <section class="play" aria-label="점심 메뉴 룰렛">
        <div class="wheel-wrap">
          <div class="pointer" aria-label="선택 화살표"></div>
          <svg class="wheel" viewBox="0 0 400 400" role="img" aria-label="8가지 음식 룰렛"></svg>
          <div class="hub" aria-hidden="true"></div>
        </div>
        <button type="button" class="spin">메뉴 고르기</button>
        <p class="status" role="status">모든 메뉴의 당첨 확률은 12.5%예요.</p>
      </section>
      <section class="result" aria-live="polite" aria-atomic="true">
        <span class="eyebrow">오늘의 점심</span>
        <div class="placeholder"><span class="plate">🍽️</span><h2>어떤 메뉴가 나올까요?</h2>
        <p>메뉴 고르기를 누르면<br>룰렛이 멈춘 뒤 결과가 나타나요.</p></div>
        <div class="winner" hidden><h2 class="menu-name"></h2><p>오늘은 이 메뉴, 맛있게 드세요!</p>
          <img class="photo" alt="" hidden><p class="missing" hidden></p>
        </div>
      </section>
    </main>
    """,
    css="""
    * { box-sizing: border-box; }
    [hidden] { display: none !important; }
    .layout { display:grid; grid-template-columns:1.15fr 1fr; gap:40px; align-items:center;
      max-width:1100px; margin:20px auto; color:var(--st-text-color); font-family:var(--st-font); }
    .play { text-align:center; min-width:0; }
    .wheel-wrap { position:relative; width:min(100%,460px); margin:22px auto 28px; }
    .wheel { display:block; width:100%; overflow:visible; border-radius:50%;
      border:8px solid #fff8ed; box-shadow:0 12px 35px #37231320; }
    .pointer { position:absolute; z-index:2; top:-14px; left:50%; transform:translateX(-50%);
      width:0; height:0; border-left:17px solid transparent; border-right:17px solid transparent;
      border-top:36px solid #a83e28; filter:drop-shadow(0 3px 2px #0002); }
    .hub { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
      width:34px; height:34px; background:#fff8ed; border:7px solid #a83e28; border-radius:50%; }
    .spin { width:min(100%,310px); padding:17px 24px; border:0; border-radius:14px;
      background:#a83e28; color:white; font:700 19px var(--st-font); cursor:pointer; }
    .spin:hover:enabled { background:#8c3020; }
    .spin:focus-visible { outline:3px solid #eaa23a; outline-offset:4px; }
    .spin:disabled { opacity:.55; cursor:wait; }
    .status { font-size:14px; opacity:.7; min-height:22px; }
    .result { padding:30px; border:1px solid #c78e5738; border-radius:24px;
      background:var(--st-secondary-background-color); min-width:0; }
    .eyebrow { color:#b45b35; font-size:13px; font-weight:700; letter-spacing:2px; }
    .placeholder { text-align:center; padding:48px 0; }
    .plate { font-size:48px; }
    h2 { font-size:26px; margin:18px 0 10px; }
    p { line-height:1.7; }
    .placeholder p,.winner p { opacity:.75; }
    .menu-name { font-size:38px; }
    .photo { width:100%; height:280px; object-fit:cover; border-radius:16px; margin-top:10px; }
    .missing { overflow-wrap:anywhere; padding:18px; border:1px dashed #b45b35; border-radius:12px; }
    @media(max-width:720px) { .layout { grid-template-columns:1fr; gap:20px; }
      .wheel-wrap { max-width:390px; } .result { padding:24px; } .photo { height:auto; max-height:360px; }
      .placeholder { padding:16px 0; } }
    """,
    js="""
    export default function(component) {
      const {data, parentElement} = component;
      const root = parentElement.querySelector('.layout');
      const wheel = root.querySelector('.wheel');
      const button = root.querySelector('.spin');
      const status = root.querySelector('.status');
      const winner = root.querySelector('.winner');
      const placeholder = root.querySelector('.placeholder');
      const photo = root.querySelector('.photo');
      const missing = root.querySelector('.missing');
      const colors = ['#f4b888','#f8d58e','#b7d5bd','#a8ced3','#c6bce0','#edbac7','#dfcf9e','#b8d4df'];
      const ns = 'http://www.w3.org/2000/svg';
      // 첫 칸의 중앙을 위쪽에 놓고 각 칸을 시계 방향으로 45도씩 배치합니다.
      const point = (deg,r) => [200+r*Math.sin(deg*Math.PI/180),200-r*Math.cos(deg*Math.PI/180)];
      data.menus.forEach((menu,i) => {
        const a=point(i*45-22.5,198), b=point(i*45+22.5,198);
        const path=document.createElementNS(ns,'path');
        path.setAttribute('d',`M200 200 L${a} A198 198 0 0 1 ${b} Z`);
        path.setAttribute('fill',colors[i]); path.setAttribute('stroke','#fff8ed');
        path.setAttribute('stroke-width','2'); wheel.appendChild(path);
        const text=document.createElementNS(ns,'text'); const p=point(i*45,133);
        text.setAttribute('x',p[0]); text.setAttribute('y',p[1]);
        text.setAttribute('text-anchor','middle'); text.setAttribute('dominant-baseline','middle');
        text.setAttribute('fill','#352c25'); text.setAttribute('font-size','18');
        text.setAttribute('font-weight','700'); text.textContent=menu.name; wheel.appendChild(text);
      });
      let rotation=0, busy=false, animation=null;
      // 2^32는 8로 나누어 떨어지므로 나머지 연산에도 확률 편향이 없습니다.
      button.onclick=async () => {
        if(busy) return;
        busy=true; button.disabled=true;
        winner.hidden=true; photo.hidden=true; photo.removeAttribute('src'); missing.hidden=true;
        placeholder.hidden=false; placeholder.querySelector('h2').textContent='오늘의 메뉴를 고르고 있어요';
        status.textContent='룰렛이 멈출 때까지 기다려주세요…';
        const index=crypto.getRandomValues(new Uint32Array(1))[0]%8;
        // 선택 칸 중앙(45*i) + 최종 회전각이 360의 배수가 되도록 맞춥니다.
        const target=(360-index*45)%360;
        const end=rotation+360*6+((target-rotation%360+360)%360);
        animation=wheel.animate([{transform:`rotate(${rotation}deg)`},{transform:`rotate(${end}deg)`}],
          {duration:5200,easing:'cubic-bezier(0.12,0.7,0.12,1)',fill:'forwards'});
        try { await animation.finished; } catch { return; }
        wheel.style.transform=`rotate(${end}deg)`; animation.cancel(); rotation=end;
        // 회전 완료 후에만 메뉴 이름과 사진을 공개합니다.
        const selected=data.menus[index];
        root.querySelector('.menu-name').textContent=selected.name;
        placeholder.hidden=true; winner.hidden=false;
        if(selected.photo) { photo.alt=selected.name+' 음식 사진'; photo.src=selected.photo; photo.hidden=false; }
        else { missing.textContent='이미지가 없습니다. 필요한 파일: '+selected.path; missing.hidden=false; }
        photo.onerror=() => { photo.hidden=true; missing.textContent='이미지를 읽을 수 없습니다. 확인할 파일: '+selected.path; missing.hidden=false; };
        status.textContent='선택 완료! 다시 돌려도 좋아요.';
        busy=false; button.disabled=false;
      };
      return () => { if(animation) animation.cancel(); button.onclick=null; };
    }
    """,
)

ROULETTE(data={"menus": load_menus()}, key="lunch-wheel")
