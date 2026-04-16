import re
import sys

try:
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 정규표현식으로 기존 initStars() IIFE 블록을 정확히 탐색
    pattern = re.compile(r"// ── 별 시스템 ──\s*\(async function initStars\(\) \{.*?\}\(\);", re.DOTALL)

    if not pattern.search(content):
        print("❌ 에러: index.html에서 기존 '별 시스템' 코드를 찾을 수 없다. 파일 상태를 확인해라.")
        sys.exit(1)

    # 덮어씌울 새로운 IP 기반 별지도 로직
    new_code = """// ── 별 시스템 ──
(async function initStars() {
  const canvas = document.getElementById('starCanvas');
  const ctx = canvas.getContext('2d');
  let stars = [];
  let skyOpacity = 0.8; // 기본값

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // 1. 별 데이터 생성
  function generateStars(count = 150) {
    stars = Array.from({ length: count }, () => ({
      x: Math.random(), y: Math.random(),
      r: Math.random() * 1.2 + 0.2,
      d: Math.random() * 4 + 2,
      phase: Math.random() * Math.PI * 2
    }));
  }
  generateStars();

  // 2. IP 기반 위경도 및 태양 고도 계산 핵심 로직
  async function updateStarOpacity() {
    try {
      // IP로 위치 파악 (실패 시 제주도 33.4, 126.5)
      const res = await fetch('https://ip-api.com/json/?fields=lat,lon,status');
      const { lat, lon, status } = await res.json();
      const targetLat = status === 'success' ? lat : 33.4;
      const targetLon = status === 'success' ? lon : 126.5;

      // 태양 고도 계산
      const now = new Date();
      const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
      const utcH = now.getUTCHours() + now.getUTCMinutes() / 60;
      
      const declination = 23.45 * Math.sin((360 / 365 * (dayOfYear - 81)) * Math.PI / 180) * Math.PI / 180;
      const hourAngle = (utcH + targetLon / 15 - 12) * 15 * Math.PI / 180;
      const latRad = targetLat * Math.PI / 180;
      
      const sinAlt = Math.sin(latRad) * Math.sin(declination) + Math.cos(latRad) * Math.cos(declination) * Math.cos(hourAngle);
      const altitude = Math.asin(sinAlt) * 180 / Math.PI;

      // 3. 고도에 따른 투명도 맵핑
      if (altitude > 6) {
        skyOpacity = 0.04; // 낮
      } else if (altitude > -6) {
        // 시민 박명 (~±6도): 0.04에서 0.5까지 부드럽게 변화
        skyOpacity = 0.04 + (0.46 * (6 - altitude) / 12);
      } else {
        skyOpacity = 0.85; // 밤
      }
      
      console.log(`[Moonshot] 위치: ${targetLat}, ${targetLon} | 태양 고도: ${altitude.toFixed(2)}° | 별 투명도: ${skyOpacity.toFixed(2)}`);
    } catch (e) {
      skyOpacity = 0.7; // 에러 시 기본 밤 설정
    }
  }

  await updateStarOpacity();

  // 4. 애니메이션 루프
  function draw(ts) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const theme = document.documentElement.getAttribute('data-theme');
    const color = theme === 'dark' ? '232,230,225' : '15,23,42';

    stars.forEach(s => {
      const twinkle = 0.6 + 0.4 * Math.sin(ts / 1000 / s.d * Math.PI * 2 + s.phase);
      ctx.beginPath();
      ctx.arc(s.x * canvas.width, s.y * canvas.height, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${color}, ${skyOpacity * twinkle})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);

  // 테마 변경 시 즉시 반영 (기존 toggleTheme 함수 래핑 유지)
  const _origToggle = window.toggleTheme;
  window.toggleTheme = function() {
    _origToggle && _origToggle();
  };
})();"""

    # 정규식 치환 및 파일 저장
    new_content = pattern.sub(new_code, content)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 성공: index.html의 별지도 로직이 한 글자의 오차도 없이 완벽하게 교체되었다.")

except Exception as e:
    print(f"❌ 치명적 오류 발생: {e}")
