#!/usr/bin/env python3
"""
Paradiso moonshot — anagram animation fix
실행: python3 fix_anagram.py
(index.html 이 있는 폴더에서 실행)
"""
import sys, pathlib

TARGET = pathlib.Path('index.html')
if not TARGET.exists():
    sys.exit('❌  index.html not found. Run this from the repo root.')

c = TARGET.read_text(encoding='utf-8')
ok = []

# ────────────────────────────────────────────────────────────────
# 1. CSS — ag-line: stroke-dashoffset draw animation
# ────────────────────────────────────────────────────────────────
OLD = """.ag-line {
    fill: none;
    stroke: #0099ff;
    stroke-width: 2.2;
    opacity: 0;
    stroke-linecap: round;
}
.ag-line.drawn   { opacity: 0.55; }
.ag-line.active  { opacity: 1; stroke-width: 3.2; }"""

NEW = """.ag-line {
    fill: none;
    stroke: rgba(255,255,255,0.45);
    stroke-width: 1.6;
    opacity: 0;
    stroke-linecap: round;
}
.ag-line.drawn  { opacity: 1; }
.ag-line.active { opacity: 1 !important; stroke-width: 2.6; stroke: rgba(255,255,255,0.9); }"""

if OLD in c:
    c = c.replace(OLD, NEW); ok.append('✅  CSS ag-line')
else:
    ok.append('⚠️   CSS ag-line — not found (already patched?)')

# ────────────────────────────────────────────────────────────────
# 2. CSS — 상단 초록 / 하단 코럴 + lit 글로우
# ────────────────────────────────────────────────────────────────
OLD2 = """.anagram-row .al {
    font-family: var(--ff-display);
    font-size: clamp(1.3rem, 2.8vw, 1.8rem);
    font-weight: 900;
    letter-spacing: 0.18em;
    width: 1.75em; text-align: center;
    padding: 0.2em 0;
    cursor: default;
    color: #ffffff;
    transition: color 0.2s, text-shadow 0.2s;
}
.anagram-row .al.lit {
    color: #0099ff;
    text-shadow: 0 0 12px rgba(0,153,255,0.6);
}"""

NEW2 = """.anagram-row .al {
    font-family: var(--ff-display);
    font-size: clamp(1.3rem, 2.8vw, 1.8rem);
    font-weight: 900;
    letter-spacing: 0.18em;
    width: 1.75em; text-align: center;
    padding: 0.2em 0;
    cursor: default;
    color: #fff;
    transition: color 0.25s, text-shadow 0.25s;
}
/* 상단 → 초록 / 하단 → 코럴 */
.top-row .al { color: #34D4A8; }
.bot-row .al { color: #FF8B7A; }
/* hover / active glow */
.top-row .al.lit {
    color: #7FFFD4;
    text-shadow: 0 0 16px rgba(52,212,168,0.85);
}
.bot-row .al.lit {
    color: #FFB3A7;
    text-shadow: 0 0 16px rgba(255,107,91,0.85);
}"""

if OLD2 in c:
    c = c.replace(OLD2, NEW2); ok.append('✅  CSS letter colors')
else:
    ok.append('⚠️   CSS letter colors — not found (already patched?)')

# ────────────────────────────────────────────────────────────────
# 3. JS — buildLines(): SVG marker + stroke-dashoffset
# ────────────────────────────────────────────────────────────────
OLD3 = """    function buildLines() {
        svg.innerHTML = '';
        lineEls = [];
        const sRect = stage.getBoundingClientRect();
        svg.setAttribute('viewBox', `0 0 ${sRect.width} ${sRect.height}`);

        MAP.forEach((bIdx, tIdx) => {
            const tR = topEls[tIdx].getBoundingClientRect();
            const bR = botEls[bIdx].getBoundingClientRect();
            const x1 = tR.left + tR.width / 2 - sRect.left;
            const y1 = tR.bottom - sRect.top;
            const x2 = bR.left + bR.width / 2 - sRect.left + WOBBLE[tIdx];
            const y2 = bR.top - sRect.top;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1); line.setAttribute('y1', y1);
            line.setAttribute('x2', x2); line.setAttribute('y2', y2);
            line.setAttribute('class', 'ag-line');
            svg.appendChild(line);
            lineEls.push(line);
        });

        animateDraw();
    }"""

NEW3 = """    function buildLines() {
        svg.innerHTML = '';
        lineEls = [];
        const sRect = stage.getBoundingClientRect();
        svg.setAttribute('viewBox', `0 0 ${sRect.width} ${sRect.height}`);
        svg.style.width  = sRect.width  + 'px';
        svg.style.height = sRect.height + 'px';

        // ── 화살표 마커 (하단 코럴 색) ──────────────────────
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        defs.innerHTML = `
            <marker id="ag-arr" markerWidth="7" markerHeight="7"
                    refX="6" refY="3.5" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0.5 L0,6.5 L6,3.5 z"
                      fill="rgba(255,255,255,0.55)"/>
            </marker>`;
        svg.appendChild(defs);

        MAP.forEach((bIdx, tIdx) => {
            const tR = topEls[tIdx].getBoundingClientRect();
            const bR = botEls[bIdx].getBoundingClientRect();
            const x1 = tR.left + tR.width / 2 - sRect.left;
            const y1 = tR.bottom - sRect.top + 1;
            const x2 = bR.left  + bR.width  / 2 - sRect.left;
            const y2 = bR.top   - sRect.top  - 1;
            const len = Math.hypot(x2 - x1, y2 - y1);

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1); line.setAttribute('y1', y1);
            line.setAttribute('x2', x2); line.setAttribute('y2', y2);
            line.setAttribute('class', 'ag-line');
            line.setAttribute('marker-end', 'url(#ag-arr)');
            line.style.strokeDasharray  = len;
            line.style.strokeDashoffset = len;   // 완전히 숨긴 상태로 시작
            svg.appendChild(line);
            lineEls.push({ line, len });          // {line, len} 객체로 저장
        });

        animateDraw();
    }"""

if OLD3 in c:
    c = c.replace(OLD3, NEW3); ok.append('✅  JS buildLines')
else:
    ok.append('⚠️   JS buildLines — not found')

# ────────────────────────────────────────────────────────────────
# 4. JS — animateDraw(): 르세라핌 영상의 타격감과 날카로운 타이밍 적용
# ────────────────────────────────────────────────────────────────
OLD4 = """    function animateDraw(startDelay) {
        const base = startDelay || 80;
        // 선을 하나씩 빠르게 순차 등장 (LE SSERAFIM 영상 느낌)
        lineEls.forEach(ln => { ln.classList.remove('drawn'); ln.style.opacity = 0; });
        lineEls.forEach((ln, i) => {
            setTimeout(() => {
                ln.style.transition = 'opacity 0.18s ease';
                ln.classList.add('drawn');
            }, base + i * 60);
        });
        // 화살표 회전 (선 등장 중간 타이밍)
        setTimeout(() => {
            if (arrow) arrow.classList.toggle('rotated');
        }, base + 3 * 60);
    }"""

NEW4 = """    function animateDraw(startDelay) {
        const base = (startDelay !== undefined) ? startDelay : 100;
        // 리셋
        lineEls.forEach(({ line, len }) => {
            line.style.transition       = 'none';
            line.style.opacity          = '0';
            line.style.strokeDashoffset = len;
            line.classList.remove('drawn');
        });
        // 영상 0:20 부근의 날카롭고 빠른 사선 베기 연출 이식
        requestAnimationFrame(() => {
            lineEls.forEach(({ line, len }, i) => {
                setTimeout(() => {
                    line.style.opacity    = '1';
                    // 베지어 곡선(0.85, 0, 0.15, 1)을 사용해 정지 상태에서 순식간에 내리꽂히는 타격감 구현
                    line.style.transition =
                        `stroke-dashoffset 0.25s cubic-bezier(0.85, 0, 0.15, 1)`;
                    line.style.strokeDashoffset = '0';
                    line.classList.add('drawn');
                }, base + i * 35); // 간격을 극도로 좁혀 다발적으로 꽂히는 속도감 부여
            });
        });
        // 화살표 회전 속도 동기화
        setTimeout(() => {
            if (arrow) arrow.classList.toggle('rotated');
        }, base + 4 * 35);
    }"""

if OLD4 in c:
    c = c.replace(OLD4, NEW4); ok.append('✅  JS animateDraw')
else:
    # 이미 이전 버전의 NEW4가 적용되어 있을 수 있으므로 이전 NEW4도 체크
    PREV_NEW4 = """    function animateDraw(startDelay) {
        const base = (startDelay !== undefined) ? startDelay : 120;
        // 리셋
        lineEls.forEach(({ line, len }) => {
            line.style.transition       = 'none';
            line.style.opacity          = '0';
            line.style.strokeDashoffset = len;
            line.classList.remove('drawn');
        });
        // 한 프레임 후 순차 드로우 (위→아래로 선이 그려지는 효과)
        requestAnimationFrame(() => {
            lineEls.forEach(({ line, len }, i) => {
                setTimeout(() => {
                    line.style.opacity    = '1';
                    line.style.transition =
                        `stroke-dashoffset 0.38s cubic-bezier(0.4,0,0.15,1)`;
                    line.style.strokeDashoffset = '0';
                    line.classList.add('drawn');
                }, base + i * 75);
            });
        });
        // 중간 타이밍에 ⇅ 회전
        setTimeout(() => {
            if (arrow) arrow.classList.toggle('rotated');
        }, base + 3 * 75);
    }"""
    if PREV_NEW4 in c:
        c = c.replace(PREV_NEW4, NEW4); ok.append('✅  JS animateDraw (Updated to sharp timing)')
    else:
        ok.append('⚠️   JS animateDraw — not found')


# ────────────────────────────────────────────────────────────────
# 5. JS — highlight(): lineEls 구조 변경 반영 ({line,len} → line)
# ────────────────────────────────────────────────────────────────
OLD5 = """    function highlight(tIdx, bIdx, on) {
        lineEls.forEach((l, i) => l.classList.toggle('active', on && i === tIdx));
        topEls.forEach((l, i) => l.classList.toggle('lit', on && i === tIdx));
        botEls.forEach((l, i) => l.classList.toggle('lit', on && i === bIdx));
    }"""

NEW5 = """    function highlight(tIdx, bIdx, on) {
        lineEls.forEach(({ line }, i) =>
            line.classList.toggle('active', on && i === tIdx));
        topEls.forEach((l, i) => l.classList.toggle('lit', on && i === tIdx));
        botEls.forEach((l, i) => l.classList.toggle('lit', on && i === bIdx));
    }"""

if OLD5 in c:
    c = c.replace(OLD5, NEW5); ok.append('✅  JS highlight')
else:
    ok.append('⚠️   JS highlight — not found')

# ────────────────────────────────────────────────────────────────
# Write output
# ────────────────────────────────────────────────────────────────
TARGET.write_text(c, encoding='utf-8')
print('\n'.join(ok))
print(f'\n✅  index.html saved ({len(c):,} bytes)')
