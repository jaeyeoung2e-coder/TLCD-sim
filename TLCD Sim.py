"""TLCD 실험실. 실행 방법은 python TLCD_3D.py 입니다.

[코드를 읽는 순서]
1. Building, Damper: 건물과 관의 입력값 및 단위.
2. lab() 안의 calculate(): 화면 문자열 → SI 단위 → 검증 → 모델 생성.
3. laboratory_input()/quake_wave(): 시간 t와 지반 가속도 ag(t) 생성.
4. network(): 관 형상 → 유체 질량·강성·유량 변환·건물 결합행렬.
5. simulate_space() → network_response(): 유체-구조 연성 시간 이력 계산.
6. metrics(): 계산 완료 여부 확인 → 같은 시간 구간의 최대값·RMS·저감률.
7. search_designs(): 같은 건물·가진·물 질량으로 설계 조합을 비교.
8. lab()의 draw_scene()/draw_chart(): 계산된 결과를 표시. 그림 자체가 물리 계산은 아님.
9. snapshot()/restore(): 이름 있는 설정과 마지막 적용 설정을 JSON에 보관.

[단위와 좌표]
내부 단위는 m, kg, s, N, rad/s. 화면의 cm는 calculate()에서 100으로 나눈다.
Hz는 초당 진동 횟수이며 각진동수는 omega=2*pi*f이다.
층별 건물 변위는 지반 기준 상대 변위, 그래프의 절대가속도는 상대가속도+지반가속도.
세계 X·Y 방향의 층별 강성은 독립 입력. 가진 방향 좌표로 회전하여 적분한다.
기본 U형 B는 양 수직관 중심선 사이 거리, h는 수평관 중심선부터 정지 수면까지 높이.
L=B+2h는 중심선 기반의 이상화된 물기둥 길이. 둥근 곡관의 실제 체적 보정은 미포함.
leg_length는 기둥의 관 축을 따라 관 끝까지 잰 길이. V형의 수직 높이는 leg_length*sin(tilt).
관 길이는 물 질량과 독립이며 관 끝·넘침 한계에 반영한다. 빈 관 자체 질량은 자동 추정하지 않는다.

[입력 우선순위 / 별도 계산]
주 실험실은 화면의 층별 값과 물 질량·안지름을 사용한다. h는 이 값에서 자동 계산한다.
TLCD 목표 각진동수 설정을 켜면 h와 안지름을 함께 조절해 입력 물 질량을 유지한다.
건물 강성 '직접 입력' 모드에서는 목표 건물 omega 입력이 사용되지 않는다.
단방향 실험실 가진은 Hz와 진폭을 사용한다. 진원 위치·지진 세기는 이 모드에서 사용하지 않는다.
아래 N, MASSES, REFERENCE 등의 상수는 별도 U형 설계·모드 분석의 기본값이다.
이 별도 분석은 한 방향 모델이며 3D 장치의 임의 형상을 그대로 계산하지 않는다.

[병합한 램프 기능]
cosine 포락선과 공통 램프 주기 설정 파일을 지원한다. 기본은 기존 quintic/OFF를 유지한다.
변위 제어는 변위를 두 번 미분, 가속도 제어는 가속도에 포락선을 적용한다.
자동 감쇠 맞춤·수면 한계 해제는 사용하지 않는다.

[추가 입력과 논문 비교]
감쇠·램프 탭에서 층간 c_i 또는 기존 감쇠비, 직접 비선형 xi 또는 beta를 선택한다.
램프 OFF는 기존 입력과 동일하다. 변위 제어는 포락선을 포함한 변위를 해석적으로 두 번 미분한다.
CSV는 명시한 단위만 변환하며 기록 크기·불규칙 시간표본을 보존한다.
주파수 응답 도구는 동일 simulate_space()의 독립 고정 주파수 실험이며 사인 스윕과 다르다.
Tanveer 예제는 알려진 구조·기하만 입력한다. 손실·가진·측정 조건이 미확인이면 재현 계산을 금지한다.
오차를 줄이기 위한 자동 물리 보정이나 논문 결과에 맞춘 계수 조정은 수행하지 않는다.

[Claude 작업분 병합 (TLCD_Sim_10 → 11)]
추가 국부 손실계수 pipe_loss(기본 0, 사용자가 지정한 추가 국부 손실): 개구비 모드에서 오리피스 손실에 더한다.
  기본값은 0이며, 사용자가 명시한 저장값은 유지한다. 관벽 마찰을 임의로 추가하지 않는다.
  직접 ξ는 total(추가 벽면항 대체) 또는 local(벽면항 별도)로 구분한다.
물 출렁임 처리 air_mode: 'stop'(기본) / 'slug'(물기둥 미끄럼 근사) / 'off'(참고).
  stop 기준은 모든 형상 공통: 어느 기둥이든 수면이 수평관 천장 높이(중심선 위 D/2)에 닿으면 중단하며,
  시작할 때 정지 수면이 이 높이 이하이면 계산하지 않는다(초기 충수 조건 미달). 기울어진 관은 축 길이로 환산.
  slug는 U형·V형·비대칭 U형(물길 하나·기둥 둘)에 적용한다. 빈 기둥의 복원력 제거, 수평관 물 길이 감소에 따른
  결합 감소(V형 경사관 몫은 유지), 기둥·수평관 단면 차이에 따른 유체 질량 변화를 라그랑주 방정식에서 유도했다.
  보정력은 고정점 반복(암시적 중점법)으로 평가한다. 감쇠 없는 자유진동에서 SciPy 해와 1% 이내, 에너지 변화 0.3% 이내 확인.
  맞춤 계수 없음. 기둥 3개 이상(일렬형·방사형)은 근사를 선택해도 정밀 기준(stop)으로 계산한다.
'장치 없음'·'물 고정' 비교 건물의 절대가속도가 0으로 남던 원본 누락(baseline_blocks)을 수정했다.

[공정 비교 도구 (분석 메뉴·오른쪽 버튼 '공정 비교 (모양별)')]
같은 건물·물 질량·손실 설정·수면 처리·가진에서 모양마다 조율비 r·개구비 β·수평 길이 B를 따로 탐색한다.
search_trial()로 모든 후보를 같은 r에 다시 조율하고 물 질량은 단면 조정으로 유지한다.
최적화 가진 순위대로 확인하며 가진 4종(공진 사인·엘센트로·고베·멕시코시티)을 모두 끝까지 견디는 첫 설계를 고른다.
그 설계를 가진 4종과 건물 진동수 ±10% 공진 사인으로 평가하여 U형 대비 차이를 표로 보인다.
U형 외 모양은 실험 검증 전이며, 분기·꺾임 손실은 모양별로 따로 반영하지 않는다.

[U형 기둥 기울기]
화면에서 V형을 따로 고르지 않는다. U형의 '기둥 기울기'(90°=수직)를 90° 미만으로 두면 내부적으로 V형 연결망을 쓴다.
기둥별 안지름·높이를 지정한 U형에는 기울기를 함께 쓸 수 없다. 예전 설정의 V형은 U형 + 기울기로 불러오고,
예전 설정의 다른 형상에 남아 있던 V형 전용 경사각은 무시하고 90°로 불러온다.

[지진 방향과 Y축 강성]
지진 기록은 수평 한 성분이며, 진원 → 건물 방향으로 흔든다. 기본 진원(서쪽)은 X축과 나란하여 Y축 강성이
결과에 영향을 주지 않는다. 진원을 대각선·남북 쪽에 두면 X·Y 강성이 모두 반영된다. 두 수평 성분 동시 입력은 미구현.

[꺾임 각도 손실 · 장치 크기]
기울인 U형(내부 V형)은 엘보가 기울기만큼만 꺾이므로 관 기본 손실 중 엘보 몫(82%)을 Idelchik 곡관 각도 계수
비율로 줄인다(60°: 0.82배, 45°: 0.70배). 수직 U형은 입력값 그대로. 실험 검증 전의 교과서 기반 추정.
요약 창과 최적 설계 탐색 표에 장치 가로(관 축)·높이를 표시한다. 관 두께는 포함하지 않는다.

[관 모양 (v19)]
모양 = 배치 × 기둥 수 × 기둥 기울기.
  U형: 기둥 2개. 기울기를 90°가 아닌 값으로 두면 기울인 U형(내부 이름 V형)이 된다.
  다기둥형(일렬형): 기둥 n개가 한 줄. 기울기는 양 끝 기둥에만, 가운데 기둥은 수직.
  피자 거치대(방사형): 가운데에서 n개(3개 이상) 가지가 같은 간격으로 퍼지고 모든 기둥이 기울어진다.
  기울기: 90°=수직, 90° 미만=바깥쪽, 90° 초과=안쪽(가운데 쪽). 안쪽 기둥이 이웃 기둥·가운데와 부딪히면 입력 오류.
  기울기가 섞인 일렬형은 정지 수면 높이가 같도록 기둥별 물 길이(관 축)를 나눈다.
  공기 유입 근사(slug)는 기둥 2개(U형·기울인 U형·비대칭 U형·2기둥 일렬형)에만, 그 밖은 stop으로 계산한다.
  '독립 U관 3개'는 v19에서 뺐다. 예전 설정은 U형으로 불러온다.

[건물 감쇠 방식]
강성비례: C=(2ζ/ω₁)K. 1차 모드 감쇠비가 ζ이고 i차는 ζ·ω_i/ω₁ (층이 많으면 높은 모드를 과하게 줄임).
모드 감쇠: 모든 모드 감쇠비 ζ. C=MΦ·diag(2ζω_i)·ΦᵀM, 구조 질량·층 강성 기준. 층이 많은 건물의 가속도 비교에 권장.
직접 계수: 층간 dashpot c_i.

[아직 반영하지 못한 물리]
1차원 연속 물기둥과 선형 전단 건물의 근사이다. 공기 유입 이후·부분 충수·기포,
유체의 3차원 접합부 흐름, 진동수에 따라 변하는 관 손실, 건물 비틀림·소성·기초 상호작용은 미포함.
오리피스 개구비 경험식의 분기관·비대칭 관 적용은 실험 검증이 필요하다.
수평관 천장 기준의 수면 제한은 보수적인 모델 적용 경계이며 실제 공기 유입 판정식이 아니다.
NumPy·Matplotlib 및 Python 기본 Tkinter를 사용한다.
"""
from dataclasses import dataclass, replace, asdict
from pathlib import Path
from functools import lru_cache
import itertools
import argparse
import csv
import json
import math
from time import perf_counter
import numpy as np

G = 9.80665
# 결합계의 가장 짧은 고유주기를 충분히 나누어 공진 부근 위상 오차를 줄인다.
INTERNAL_POINTS_PER_PERIOD = 200

# 아래 설정은 해석 메뉴의 다층 U형 실험에 적용합니다.
# ── 실험 설정: 이 부분에서 조건을 바꾸세요. 길이 m, 시간 s, 질량 kg, 힘 N ──
N = 3
MASSES = [16., 14., 12.]                 # 1층부터 위로 각 층의 질량
STIFFNESSES = [3200., 2800., 2200.]     # 지면–1층, 1층–2층, 2층–3층의 수평 강성(N/m)
HEIGHTS = [.40, .38, .36]                # 각 층 사이의 높이(m). 층간변위비 계산용
RAYLEIGH_A, RAYLEIGH_B = .12, .0015     # 각각 1/s, s. C = a M + b K
CUSTOM_C = None                          # 직접 지정하려면 n×n 대칭 행렬(N·s/m)
INSTALL_FLOOR = 3                        # 기준 U형 설치 층. 화면은 1층부터 시작
REFERENCE = dict(L=.50, B=.30, A=.002, rho=1000., beta=.4)
# 설계별로 아래 목록의 모든 조합을 계산한다. 층은 1부터 입력한다.
FLOORS = [1, 3]
L_VALUES = [.42, .60]
B_VALUES = [.28]

BETA_VALUES = [.3,.5]
KEEP_WATER_MASS = True                   # True: L이 달라지면 A를 바꿔 기준 물 질량 유지
CUSTOM_AREA = .002                       # False일 때 쓰는 단면적(m²)
CUSTOM_DENSITY = 1000.                    # kg/m³
TUNE_TO_MODES = []                       # 예: [1,2]. 해당 모드에 맞는 L을 계산한 설계도 추가
# 자동 조율 설계는 B/L과 Ao/A를 기준 설계와 같게 둔다.
FREEBOARD = .12                          # 정지 수면부터 열린 관 끝까지의 여유 높이(m)

HARMONIC_ON = True
GROUND_CSV = None                        # 예: "ground.csv", 첫 줄 time_s,accel_m_s2
HARMONIC_HZ, AMPLITUDE = 1.05, .055     # Hz, 지반 가속도 진폭(m/s²)
DURATION, DT = 12., .01                  # 해석 시간과 결과 저장 간격(s)
# CSV와 조화 가진을 모두 켜면 더한다. CSV 범위 밖은 자동 연장하지 않는다.
U0 = None                                # n개 층의 지반 기준 초기 변위(m), None이면 0
V0 = None                                # n개 층 초기 속도(m/s)
WATER_Y0, WATER_V0 = 0., 0.              # 관 기준 초기 수면 변화(m), 속도(m/s)
MAX_INTERNAL_DT = .01                    # 내부 적분 간격의 상한(s)
SWEEP_HZ = [.60, .85, 1.05, 1.30, 1.60] # []이면 주파수 비교 생략
SWEEP_CYCLES, MEASURE_CYCLES = 14, 4     # 총 가진 주기와 끝에서 측정하는 주기 수
SWEEP_AMPLITUDE = .055                   # 별도 주파수 실험의 공통 가속도 진폭(m/s²)
SAVE_CSV = True
# 시간 이력 그림에서 비교할 사용자 설계. 전체 설계 결과는 표/설계 비교 그림에 수록.
PLOT_CUSTOM_ID = 'D01'





# 건물 입력 묶음. GUI의 m/k/y/h 목록이 masses/stories/stories_y/heights로 전달된다.
# width·depth는 외형 치수이며, 크기 연동을 켠 경우에만 기준 면적비로 질량을 바꾼다. 강성은 독립 입력이다.
@dataclass(frozen=True)
class Building:
    mass: float = 20.0       # 물과 관을 제외한 모형 구조물 질량 [kg]
    frequency: float = 1.0   # 장치가 없는 구조물의 고유진동수 [Hz]
    # 강성비례 모드에서만 C=(2*zeta/omega_X1)*K. X 1차 모드가 이 감쇠비를 갖고 다른 모드의 감쇠비는 달라진다.
    damping: float = 0.02    # 구조물 감쇠비: 0.02 = 2%
    container_mass: float = 0.0  # 관 자체 질량 [kg], 실제 측정값으로 변경

    width: float = .56  # 건물 가로(m)
    depth: float = .44  # 건물 앞뒤(m)
    # 두 방식은 합산하지 않는다. 직접 계수는 각 층간 dashpot의 c_i [N·s/m]이다.
    damping_mode: str = '강성비례'
    story_c: tuple = ()  # 직접 층간 점성감쇠 N·s/m
    story_cy: tuple = ()
    stories_y: tuple = ()
    bearing: float = 0.
    # 비어 있는 목록 대신 비어 있는 튜플이면 기본 2층 모형. 값이 있으면 층별 목록을 우선한다.
    masses: tuple = ()
    stories: tuple = ()
    heights: tuple = ()
    mount: int = 0  # 0이면 지붕

    def __post_init__(self):
        for key in ('masses','stories','stories_y','heights','story_c','story_cy'):
            object.__setattr__(self,key,tuple(getattr(self,key)))
        if self.masses or self.stories or self.heights:
            n=len(self.masses)
            if not n or len(self.stories)!=n or len(self.heights)!=n:
                raise ValueError('질량·강성·높이는 층마다 하나씩 입력하세요.')
            if not all(np.isfinite(x) and x>0 for x in self.masses+self.stories+self.heights):
                raise ValueError('층별 질량·강성·높이는 유한한 양수여야 합니다.')
            if not isinstance(self.mount,int) or not 0<=self.mount<=n:
                raise ValueError('설치 층이 건물 층수 범위를 벗어났습니다.')

    def floor_data(self):
        if self.masses:
            return np.array(self.masses),np.array(self.stories),np.array(self.heights),self.mount or len(self.masses)
        k=self.mass*(2*np.pi*self.frequency)**2/(3-np.sqrt(5))
        return np.full(2,self.mass/2),np.full(2,k),np.array([.21,.21]),2

    @property
    def stiffness(self):
        return self.mass * (2 * np.pi * self.frequency) ** 2

    @property
    def viscous(self):
        return 2 * self.damping * self.mass * 2 * np.pi * self.frequency


# 관 입력 묶음. B,h,diameter는 m, angle·tilt는 도 단위이다.
# 물 밀도는 주 계산에서 1000 kg/m³로 고정. beta는 면적비이며 유체 손실계수는 내부 계산한다.
@dataclass(frozen=True)
class Damper:
    B: float = 0.30          # 바닥 수평 관의 중심선 길이 [m]
    h: float = 0.10          # 물량 파라미터[m]. 수직부 물 부피=2*A*h. 실제 수면은 형상별 계산.
    diameter: float = 0.05   # 원형 관의 안지름 [m], 모든 구간 일정
    angle: float = 0.0       # 지진 방향과 관의 수평축 사이 각도 [도]
    # 논문 TLCBD의 c_L=2*m_l*xi_l*omega_d는 선형 감쇠 정의이므로 이 xi로 자동 변환하지 않는다.
    xi: float | None = None  # None이면 beta 경험식, 수치면 관 평균속도 기준 비선형 손실계수
    beta: float = .4         # 오리피스 면적 / 유로 단면적
    # 오리피스와 무관한 관 자체 손실(엘보·벽 마찰). 개구비 모드에서 오리피스 손실에 더한다.
    # 오리피스 없는 U관 실측 2.3~2.5 (Serbes 등 2024, Buildings 14:2782),
    # 기본 추가 손실은 0이다. 실측 등 별도 근거가 있는 국부 손실만 명시적으로 입력한다.
    xi_scope: str = 'total'  # 기존 저장 ξ는 총손실 의미를 유지. local은 오리피스 등 국부 손실.
    pipe_loss: float = 0.0
    leg_length: float | None = None  # 각 기둥의 관 축 길이[m]. None은 기존 h+여유높이 방식.
    freeboard: float = 0.12  # 정지 수면 위 여유 높이 [m]

    shape: str = 'U형'
    tilt: float = 90.0  # 기둥과 수평면 사이 각도. 90=수직, 90 미만=바깥쪽, 90 초과=안쪽으로 기울임
    reverse: bool = False
    columns: int = 4
    bores: tuple = ()  # 각 수직 기둥의 안지름(m). 빈 목록이면 공통 안지름.
    tops: tuple = ()   # 각 바닥 관 중심부터 열린 끝까지의 높이(m).

    def __post_init__(self):
        for name in ('bores','tops'):
            object.__setattr__(self,name,tuple(getattr(self,name)))

    @property
    def separate_u(self):
        return self.shape=='U형' and bool(self.bores or self.tops)


    @property
    def loss(self):
        if self.xi is not None:
            if not np.isfinite(self.xi) or self.xi<0:raise ValueError('직접 ξ는 유한한 0 이상 값이어야 합니다.')
            return float(self.xi)+(self.effective_pipe_loss if self.xi_scope=='local' else 0.)  # 총손실은 추가 손실을 중복 합산하지 않는다.
        return orifice_loss(self.beta)+self.effective_pipe_loss

    @property
    def effective_pipe_loss(self):
        # 기울인 기둥은 엘보가 tilt°만 꺾인다(안쪽 기울기는 90° 초과). 수직(90°)이면 입력값 그대로.
        return self.pipe_loss*bend_loss_factor(self.tilt) if is_tilted(self) else self.pipe_loss

    @property
    def rho(self):
        return 1000.  # 물 밀도 [kg/m³]

    @property
    def area(self):
        return np.pi * self.diameter ** 2 / 4

    @property
    def length(self):
        return self.B + 2 * self.h

    @property
    def mass(self):
        return self.rho * self.area * self.length  # 물의 밀도 1000 kg/m³

    @property
    def coupling(self):
        # 설치 방향은 관 자체 길이/진동수를 바꾸지 않고 힘의 결합을 바꾼다.
        return self.rho * self.area * self.B * math.cos(math.radians(self.angle))

    @property
    def frequency(self):
        # 같은 불변 설계의 미리보기·표·탐색에서 고유치 계산을 반복하지 않는다.
        return damper_frequency(self,G)

    @property
    def limit(self):
        # 기존 API의 스칼라 값은 모든 기둥에서 허용되는 최소 대칭 변위 여유이다.
        rest,lower,upper=column_water_heights(self)
        return max(0.,float(min(np.min(rest-lower),np.min(upper-rest))))


def is_tilted(d):
    """기둥이 수직(90°)이 아닌가. U형은 화면에서 기울이면 내부적으로 V형이 된다."""
    return d.shape in ('V형','다기둥형','피자 거치대') and not math.isclose(d.tilt,90.,abs_tol=1e-12)


def column_count(d):
    """연결된 기둥 수. 다기둥형(일렬형)·피자 거치대(방사형)는 기둥 수 입력을 따른다."""
    return d.columns if d.shape in ('다기둥형','피자 거치대') else 2


def equivalent_u(d):
    """동일 B,h,D를 가진 두 수직 물기둥. 형상 이름과 무관하게 같은 모델·경계를 사용한다."""
    return not d.separate_u and (d.shape=='U형' or
        (d.shape=='다기둥형' and d.columns==2 and not is_tilted(d)) or
        (d.shape=='V형' and not is_tilted(d)))


@lru_cache(maxsize=256)
def damper_frequency(d,gravity):
    geometry=replace(d,beta=1.,xi=None,xi_scope='total',pipe_loss=0.,angle=0.,reverse=False)
    return _geometry_frequency(geometry,gravity)


@lru_cache(maxsize=256)
def _geometry_frequency(d,gravity):
    # 캐시는 스칼라 결과만 저장한다. 네트워크 행렬/시간 이력 배열은 캐싱하지 않는다.
    if equivalent_u(d):return math.sqrt(2*gravity/d.length)/(2*np.pi)
    mass,stiffness=network(d)[7:9]
    root=np.linalg.cholesky(mass)
    normalized=np.linalg.solve(root,stiffness)
    normalized=np.linalg.solve(root,normalized.T).T
    squared=np.linalg.eigvalsh(normalized)
    if squared[0]<=0:raise ValueError('유체 고유진동수가 양수가 아닙니다. 형상을 확인하세요.')
    return math.sqrt(squared[0])/(2*np.pi)


# beta=Ao/A → xi. xi는 무차원이며 힘은 0.5*rho*A*xi*v*abs(v) [N].
# 분기관의 유속은 network()의 T 변환을 사용한다. 관벽/곡관 저항을 추가한 식은 아니다.
def structural_damping(b):
    m,k,_,_=b.floor_data();n=len(m)
    D=np.eye(n)-np.eye(n,k=-1)
    kx=D.T@(k[:,None]*D)
    ky=D.T@((np.asarray(b.stories_y) if b.stories_y else k)[:,None]*D)
    if b.damping_mode=='강성비례':
        omega=tuning_frequency(b)*2*np.pi
        return 2*b.damping/omega*kx,2*b.damping/omega*ky
    if b.damping_mode=='모드 감쇠':
        # 모든 진동 모드가 같은 감쇠비 ζ를 갖도록 C = MΦ·diag(2ζω_i)·ΦᵀM (Φ는 질량 정규화 모드).
        # 강성비례는 i차 모드 감쇠비가 ζ·ω_i/ω_1로 커져 층이 많을수록 높은 모드를 지나치게 줄인다.
        # 구조 질량(관·물 제외)과 층 강성으로 정의하며, 다른 비교 건물에도 같은 행렬을 쓴다.
        if not np.isfinite(b.damping) or b.damping<0:raise ValueError('감쇠비는 0 이상이어야 합니다.')
        root=np.sqrt(m);matrices=[]
        for K in (kx,ky):
            w2,vectors=np.linalg.eigh(K/np.outer(root,root))
            omega=np.sqrt(np.maximum(w2,0.))
            shape=root[:,None]*vectors          # = M·Φ (Φ = vectors/√m)
            matrices.append(shape@np.diag(2*b.damping*omega)@shape.T)
        return tuple(matrices)
    if b.damping_mode!='직접 계수':raise ValueError('감쇠 입력 방식을 확인하세요.')
    matrices=[]
    for name,values in [('X',b.story_c),('Y',b.story_cy or b.story_c)]:
        values=np.asarray(values,float)
        if values.shape!=(n,) or not np.isfinite(values).all() or np.any(values<0):
            raise ValueError(f'{name} 층별 c는 층수만큼 유한한 0 이상 값(N·s/m)을 입력하세요.')
        C=D.T@(values[:,None]*D)
        if not np.allclose(C,C.T) or np.linalg.eigvalsh(C).min() < -1e-10:
            raise ValueError('감쇠행렬의 대칭성/비음수 소산 조건 위반')
        matrices.append(C)
    return tuple(matrices)





# 관 기본 손실 중 벽 마찰 몫. Serbes(2024) 관에서 교과서 추정 마찰 약 0.2 / (마찰 0.2 + 90° 엘보 2개 0.9) ≈ 0.18.
PIPE_FRICTION_SHARE = .18


def bend_angle_coefficient(angle):
    """Idelchik 곡관 각도 계수 A(δ): δ≤70° 0.9·sinδ, δ=90° 1.0, δ≥100° 0.7+0.35·δ/90. 70~90°는 선형 보간."""
    if not 0 < angle <= 180: raise ValueError('꺾임 각도는 0° 초과 180° 이하입니다.')
    if angle <= 70: return .9*math.sin(math.radians(angle))
    if angle <= 90:
        low = .9*math.sin(math.radians(70)); return low+(1-low)*(angle-70)/20
    if angle < 100: return 1.+(.7+.35*100/90-1.)*(angle-90)/10
    return .7+.35*angle/90


def bend_loss_factor(tilt):
    """수직 기둥(90° 엘보) 대비 관 기본 손실 배율. 벽 마찰 몫은 그대로, 엘보 몫만 각도 계수 비율로 바꾼다.
    실험 검증 전의 교과서 기반 추정이다."""
    return PIPE_FRICTION_SHARE+(1-PIPE_FRICTION_SHARE)*bend_angle_coefficient(tilt)/bend_angle_coefficient(90.)


def orifice_loss(beta):
    if not np.isfinite(beta) or not 0<beta<=1:
        raise ValueError('오리피스 개구비 β는 0 초과, 1 이하여야 합니다.')
    psi=1-beta
    return (psi+.707*psi**.375)**2/beta**2

def column_water_heights(d):
    """수평관 중심선 기준 기둥별 정지 수면·중단 하한·관 끝 높이[m]."""
    feet,up,leg,*_=network(d)
    legs=np.broadcast_to(np.asarray(leg,float),len(up))
    rest=legs*up[:,2]
    if d.separate_u:
        tops=np.asarray(u_dimensions(d)[4],float)*up[:,2]
    elif d.leg_length is not None:
        tops=d.leg_length*up[:,2]
    else:
        tops=rest+d.freeboard
    return rest,np.full(len(up),d.diameter/2),tops


def column_surface_text(d,b):
    rest,lower,upper=column_water_heights(d)
    low,high=1000*np.min(rest),1000*np.max(rest)
    height=f'{low:.3g}' if np.isclose(low,high) else f'{low:.3g}~{high:.3g}'
    return (f'현재 조율비 r={d.frequency/tuning_frequency(b):.5g} (X 1차)'
        f'\n실제 정지 수면 {height} mm · 수평관 중심선 기준'
        f'\n최소 하향 여유 {1000*np.min(rest-lower):.3g} mm')


@lru_cache(maxsize=512)
def validate_column_spacing(d):
    geometry=replace(d,beta=1.,xi=None,xi_scope='total',pipe_loss=0.,angle=0.,reverse=False)
    return _geometry_spacing(geometry)


@lru_cache(maxsize=512)
def _geometry_spacing(d):
    """수직·경사 기둥 축 선분 사이 거리를 안지름 합으로 검사한다.
    관벽 두께를 입력받지 않으므로 안지름 기준의 최소 간섭 검사다.
    의도된 바닥 유로 접합부는 검사 대상인 기둥 축에 포함하지 않는다.
    """
    feet,up,leg,*_=network(d)
    legs=np.broadcast_to(np.asarray(leg,float),len(up))
    if d.separate_u:
        _,bores,_,_,tops=u_dimensions(d)
    else:
        bores=np.full(len(up),d.diameter)
        tops=np.full(len(up),d.leg_length) if d.leg_length is not None else legs+d.freeboard/up[:,2]
    axes=up*np.asarray(tops)[:,None]
    def point_distance(point,start,vector):
        fraction=np.clip(np.dot(point-start,vector)/np.dot(vector,vector),0.,1.)
        return float(np.linalg.norm(point-start-fraction*vector))
    for i in range(len(feet)):
        for j in range(i+1,len(feet)):
            a,u=feet[i],axes[i];b,v=feet[j],axes[j]
            distance=min(point_distance(a,b,v),point_distance(a+u,b,v),
                point_distance(b,a,u),point_distance(b+v,a,u))
            w=a-b;uu=u@u;vv=v@v;uv=u@v;det=uu*vv-uv*uv
            if det>1e-14*uu*vv:
                x=(uv*(v@w)-vv*(u@w))/det
                y=(uu*(v@w)-uv*(u@w))/det
                if 0<=x<=1 and 0<=y<=1:
                    distance=min(distance,float(np.linalg.norm(w+x*u-y*v)))
            minimum=(bores[i]+bores[j])/2
            if distance<minimum-1e-10:
                raise ValueError(f'{i+1}·{j+1}번 기둥 간섭: 최소 축 간격 {distance*1000:.3f} mm, '
                    f'필요 최소 {minimum*1000:.3f} mm (안지름 기준, 관벽 두께 미포함). '
                    'B를 늘리거나 기둥 수·지름·기울기를 조정하세요.')


def validate(b, d):
    if d.xi_scope not in ('total','local'):raise ValueError('직접 ξ의 총손실/국부손실 구분을 확인하세요.')
    _=d.loss
    structural_damping(b)
    if b.stories_y and (len(b.stories_y)!=len(b.floor_data()[0]) or any(not np.isfinite(x) or x<=0 for x in b.stories_y)):
        raise ValueError('Y방향 강성은 층마다 양수를 하나씩 입력하세요.')

    if not all(np.isfinite([b.mass,b.frequency,b.damping,b.container_mass])) or not all(np.isfinite([v for k,v in asdict(d).items() if k not in ("shape","bores","tops","leg_length","xi","xi_scope")])):
        raise ValueError('모든 매개변수는 유한한 수여야 합니다.')
    if not all(np.isfinite(x) and x>0 for x in (b.width,b.depth)):
        raise ValueError('건물 가로와 세로는 양수여야 합니다.')
    if not isinstance(d.columns,int) or not 2<=d.columns<=24:
        raise ValueError('기둥 수는 2~24 사이 정수로 입력하세요(방사형은 3 이상).')
    if d.shape not in SHAPES or not 0<d.tilt<180: raise ValueError('관 종류와 기둥 기울기(0° 초과 180° 미만, 90°=수직)를 확인하세요.')
    if d.shape=='피자 거치대' and d.columns<3: raise ValueError('피자 거치대(방사형)는 기둥이 3개 이상이어야 합니다.')
    if min(b.mass, b.frequency, d.B, d.h, d.diameter, d.freeboard) <= 0:
        raise ValueError('질량, 진동수, 길이와 지름은 양수여야 합니다.')
    if d.separate_u and min(d.B,d.h,d.diameter)>0:
        u_dimensions(d)
    if d.leg_length is not None:
        if not np.isfinite(d.leg_length) or d.leg_length<=0:raise ValueError('기둥 관 길이는 유한한 양수여야 합니다.')
    if d.leg_length is not None:
        if not np.isfinite(d.leg_length) or d.leg_length<=0:raise ValueError('기둥 관 길이는 유한한 양수여야 합니다.')
        if not d.separate_u:
            legs=np.broadcast_to(np.asarray(network(d)[2],float),column_count(d))
            if np.any(d.leg_length<=legs):raise ValueError('관 끝이 정지 수면보다 낮습니다. 관 길이를 늘리거나 물 질량을 줄이세요.')
    validate_column_spacing(d)
    if not (math.isfinite(d.pipe_loss) and d.pipe_loss >= 0):
        raise ValueError('추가 국부 손실계수는 0 이상이어야 합니다.')
    if min(b.damping, b.container_mass, d.loss) < 0 or not 0 <= d.angle <= 180:
        raise ValueError('감쇠와 관 질량은 0 이상, 각도는 0~180도여야 합니다.')


def demo_input(duration=20.0, dt=0.005, pga=0.03, seed=7):
    """재현 가능한 합성 진동. 실제 지진 기록/설계 지진이 아니다. pga 단위는 g."""
    t = np.linspace(0, duration, round(duration / dt) + 1)
    rng = np.random.default_rng(seed)
    frequencies = np.linspace(0.4, 4.0, 45)
    weights = np.exp(-((frequencies - 1.2) / 0.9) ** 2)
    raw = np.sum(weights[:, None] * np.sin(2 * np.pi * frequencies[:, None] * t
                 + rng.uniform(0, 2*np.pi, (45, 1))), axis=0)
    raw *= np.sin(np.pi * t / duration) ** 2
    return t, raw / np.max(np.abs(raw)) * pga * G


def recorded_input():
    """1940 El Centro N-S, Peknold판. 원본의 0.02초 간격과 소수점 5자리 g 보존.
    https://github.com/OpenSees/OpenSees/blob/master/EXAMPLES/ExampleScripts/elCentro.AT2
    기본 재생은 파형을 보존하고 최대 가속도만 0.03 g로 맞춘다.
    """
    import base64, zlib
    packed = (
        'c-k%4dAyHh`Umh^C$eNogsj<$(#e*}c0$X9${-ny?1O1&LoZ8NDr)>F5=SGUL}gMaN+C;QnaGl*Le>!HWOs1x-}{+we_XF;x'
        'v%AOeXi?Xo@d|{Av}>Mgzh1Pk6h1sZhB=1AGntEJUqtuq-&S75FXAO!glXF(|y;wpIu9mrHQ@qg2q3|7sA}!7~eS?W2H;3#)'
        '`2S;QfyUL&zu^!s`V>*iU~2d7BI+*RxrCKE_8*#rWgN7~eY*;{zvRJmLNY?~0v{aR#Y#CdS{gVw`<6#x4hAynb(t&0PC<e$D'
        '&8k{aYi@%LPg@h+GqT^&O9wIQ@D8^Y|$^1LR51#mB+w`_NeYyKPKhNUsS;o8abT|dWI`llGr?(*(OG2Q35U%4~JsdUQii*Y*'
        'tHxvqCR>csi*9&3J{UOx+YY0c$hw%P`A@sa2gsK@K?7Jg`qD@0+d`}3|>xPg={2s+ZSR>z?j>q^a|Hs$H_|W1QKbak4iAgaI'
        '92H~6+c6eg662OFF;2t7-*8sDY6usbgs{3}2;-j(VcK8RNsPtS`IF;TT<zNtWA@iEUVb;mLjRPHI3GTx#vMYqwQ&ep;?K_?!'
        'c%<Kyh<J5e+$NTZ9*vjKnMq$g|MuC2$?s9@C?3M7YX4;HOzzijrjZ*o4)vKQ6_{6H-vDG-c_YSD23-6)#>(M@B>GhnjXRVnY'
        '5Jc)dz68HO8u|V*E}{&+U(~GX3>>qt4+NGuOu$=EvA%V~j&!TT)mr-V#E+Rv{F=ErdgSEjt(E6ntgsfw%P0v>G^V9>TTsMwb'
        'ZTl772M@3vEy5yeB82jf9_E2vcm@z1FD#Ebe;KJ)ZrL!4dDXAaCeH|W35>3pl+IPCW;-t^<IxGKl*!)&L~J!U@K;a%&T7`y!'
        'z;~@Pqc9Y)xCdSVe%0~?=s@pU2`Bop5&5p6Z99O|t`bKrQQ%v>x4}1gpD(U?~9JW=PQ))1wm;O+L+be`nK#U)^#W?Si7@ybU'
        '56NdV+{^HGPT!}0r!T(Li*sV!u5U`h&=z+St`A|;z2>gE-c~b&U)1q+e120cgwx_wdnAPC^yfO`<&5_?z5*8)_^%CPAN|}Fr'
        'jF%8XrovEgwwl|xvB0?&>w;G`NsF~Ss0c^_?oGn`Ek?_=B;|66#b6o<iE_F-EiKpBF63u^!1t;%bQ0R5cz}N>_YF@?=cSW`~'
        'myj{LR%b1Jrnno<Azz_we1t+A&Mr4${97r+xLzcy(PU)=nG_rCW)=m3nWBKHbOWeZ2oe?dsCI!1veIl-=xe^~4&!#_5F`YOs'
        'o4w&(K16bMJz|I=6>&-c--CeJkew^v_%g^Q`i2l4s1*eyLb(BoD3xW%=;=T^qM8y_s@>-uPp{`%Vbu?*(ra$C;t3iIl?+{%c'
        '5kG_iT7hlJ>_e0%xmP-a7mDTfz@%d~9iGNniA~02#Um5WV(Yq|CEWB-W{aEbru+(6?QoeO@HPd}@??=!d&d&?NJ@0v_99QGH'
        '2%QdUbyBRc{A@5+a@p2~zX!Z;UWjq6IG5Ppis!B{PQ=HH?g#MIi;wljZ-Z%)9?8*v|0kD9dVB%y%9GLh>v#A+b$!-zeLh;q<'
        '<IKVRm_&+9B~~(4)B*DmuY(Gg7FTni*Rs?ejT-b(i--$HQ~6m@XI<Oj4_|ui&>e^tURf`sUs;&cH@7(`8mS+dd9V{y!LqCj{'
        'aJ<iz<aMgI#lT;Go`bu776O3mUJBao2Whv3XY<rWJbhNjzP|+spE}#$0);dTQ;jYW=$b#){^9`Q>;JvxRw6G}-fTJe%!PYTw'
        'xSIy`rf+X1;eg~MF&r@Lm*{l)u{=0O!}%6M^etS`Or@;x7o(^7lJn_~AW9l~{ZUqh!BOmB#tqwlKG*<^eOj?$Ao7S<{9X(e_'
        'Z^Kg;;bNRm4zB8WB9dvHsYpJ#LQ9adL?ViKK80*B8^bo!?mRBz|glPi~I;%yNI3v_=i#k@jI@OcY*?o(Htn%i)J*uDDuTIuY'
        'G3KzZYwj+iQ$>z1!+KPowYFaLg?%)P?;2muzP&me<^KhCCE)I4Y$iWP@l)GAl?K~3zTekZgXy+n_qFHRRn#2b_Ud<4#ne3NW'
        '4x?*8~Au$Kc&lgufCpuhvxR7xH-lzzE@wI)UoG`T^8fvkFBNF&<@tzqH6dptS`v5ff`LIpX%$!a8gnK?Z4Ss!ag}(+~@2=U1'
        '4~DPD}Ay*%w=T&Y)X|eKj1E(!Wd9zL}iY!t+p)qk8XD-)ZX8NWMSf_ail5tzY(-vpc+-OJ|6>x57(#`Oeli>H2pu-Hon?<ak'
        '*PO5k?@u6~eOgJhq?@j8Ak^PkQ~H}Rg~^Cj;li;>Sf7@&U+TASMGiIvu;p>W(zKg$|82kvw}7wM(m>ReX*jeLyM2le&C7j!c'
        '4yh7hJvp#$yw^qit!_w8ham=24kLz^L=kd5SsjHfN#qUM_8nb%={zu3Vc;8W<)q3Kny`iX@jN0S;C5Jw8|C!ChxLw6(NBiOl'
        '{W^+WIr14CgTx-HC;kR&TbP>Qy{1}~6#sRc6^8E>x#dO9aOaQj?MIcxc}Bcd;+DiuFE#ocu1@Aqr2nou-OnbUd{@ITil2|<u'
        '+{xT;;y52PqG)|e2}@GF6Lpip9E_QJnWbA2+|8z#m=Vq>Vb<Q@GaI)yVzb-heLATd_{_vY`t1l&K=ZalV1H3+i%pXA$$wPt)'
        '=#}`DhKtDfOSKkN(Rh@KqPLz4-1Rhx_@vgG~dyP~TXfyCJE&eA>zP8aXWx`;kL2p2zc8_mwWB_R{<D_!ExD6;G{6C%vD_Pjh'
        '3(aPWp)8zu8wya(0L68XP9yghsmz}1vaJv!x$<xAEpv7Z*ZwOBjg?ZHo$It@<FviuCQ2Ib;wxV%@pF5qhhz43bgPP`ouf1Dh'
        'P^79%#H|I_D`e=OB!Try29b>#MyXby{_ie~_JUm9a^WRq<Kd4u;<lG0-RCa%--_RVt+S#S!FRAZ|(|Ea?uW|IJ!atkd0`}Lq'
        'zn%L|YIT(TbH?+@f0B=%D*Cda+PAYtJ>gw{dgtKF(xZpq_*uPb7D@HUN}LvB)0Xa=bav1wYpgSzN&oeSX%HTUtNobdya3l37'
        ';n*w-Neomd!zi1C;NV~$1Cl9-u1*yC)^dr&vHJVrdz|iy~ZcgPx>|g<<wY3*JR%9_P&W)o#*RQ@19^Y8ul4-{SvN%aCemF9J'
        ';Ic0VU>&m3*f)px>7NC&e5qW=%Ev5Bpx~m8Nzx@Yq!SCOSVH)>~!Vw=_PC&By%h<98kWpYoN-zA`KyidoN`-HM}U#lBWAEui'
        '0)zf*d49-qC%sSL+Y#)iON2B)9na}oYNmB)O(dXq|I2i@`Fk77Rv&cBQMxZK*R$<6fB#OO)BB{e+1XgpbS?}E34em#CBwf@f'
        '#Z*cNWp$}@QRVnv*yg$bGHtXkHb95N}Kg+K=UUKC1oxYhxcZQtaf$=T1o-D5k>b}B#w)c$+rOxtO#I3+?tT;LDd-MN;_q9Ba'
        ';&W$K>OAqX^Zq=2vCaJ@7^{ex2Jb#tRwQ*}Hyp+;;x-lMZT>Ig<S`sBwWgQF;b3^LNWM8e7f;rY<lIW{L)fOUeMy~@-g#UPw'
        'xT;uoK1Kyj=y&DnnY*2e9GwePS(0<&Oh~>gVyuWO)bys)A9RLXWoh8Ogfo5+ub7GdGaisY&E!3o+EQoXNr>aI$Ik~<MCBFRT'
        '6&@Y%Rt6h3>2BTsN6VIC~k+boJioxj&8`Ax%hia*V#u$2fqkPx1flS0~u7fNc`nH`z>fpDBkl_3nqKopNc8tAF!ZT23d`VFU'
        'ab*2zWIgPM4l4%1BX9+^YRCVj<!ni>z}_oy}OK!Pu+8=f}Fd9A&*FWW-$n<t+KFQxX>+u(azj0N;g^YgIlJYxm$(#zONI(3t'
        'OEAIRA*RVipo!Kn!Y0gJ|>}M6_u#N3l9M@H!UHW50ay})=clO<6iFsaIoVj?eoUCOyEM7FV7vBPR1%8VaOwEBa<kw{1GY6CJ'
        '`(}EoOEOpam@3Za>U1rf{YVG6?$$HOe}ik;U4rcpZ11`DD406m?GtkbKV8_KmfINll#|PRHZ9oXm+N|cvP+yJ#?Pr+K6qBTj'
        '_};X`%7|Kg2O3t86;-=WKU6}w1f*W-bwg@uZemj=c;UWYuP7f#UXUs*<Wf|OY+%g3(GCp-^-ahRh%mt*<0KHmikT|P5+%_Ke'
        'iWrUnjK|_Y}8@o-D<8w)pGV&PwKx=dJqmu-?eQeG&a}pX+e%exv`W^<pKx^yK?cp3THPN+#%yyZGI0-j9^Sjmdmb$NsRD^nN'
        'K`yNNl6j}v0lOTHUnE2WPXdf&#v+eOU&#)ql#*gy8;WbP(=R1zywZ8P<8rXI<3M$R-hGw2+a>lk_0gmnW>A2!Ff!TT5guXg('
        'u>Fx~lw0S;K+}G7?hB|x#<8tTMO|`6t{#6um)@^|Q?(n>3Pin#6d00NedsnqCDgIh~->k0V;LOHxX?`={?hXHId@qK1Z?XsR'
        'bDMs7RBeXyJIB9-O?W@$dY$v~ov?S3$87mz^V?8;UdHFua-G256b)~SQx(<^E~fgciRUrNaX#rYJ+Q*Np0E{wcb+=8f$0I)='
        '5RE^ZGCpPhE$(U=C`H3PrkhuiuH`=I{f{v=JRn~F4+^+B3TzY(_afqeR|W_<fYp$q`v+0uwS1)_3v{sondfvq0`K}s`9u>os'
        'U>+M(TyKI9Nch6}yAUcR0KwU0-7J3Y&9k+OuHl`|55ye5`L8u>ab-dyRd^&hMMB9<B^Mw@6*DbZzT-CO_GKoWZ7wahlJEyqh'
        'cME9LZfvNo7|1MyH-+~l9fyySl#T=`&~Nxz9)cgcI;$<%+grR?^wzapmgnc-qLWtU41C*PaNzaCe=KEo`w$$37%cVF`N4>?q'
        'l_e6NE@@_Eu6MCU59NVmq2h`;B=@hmSVpPR_UG~l8u!GMh(vpSN`VH4+?~20ON{_yR(={;f<u}K>5`52vcdYmmNhX<2W|NOd'
        'a=uwYmXX!T8c#Np9hX!8h!2wAE~n~zo<x!tmgL_`aZ;L8Ak|3H=e5ZlxvAc3L0XbFqytI*+w>rP$x~zy8Ae_tuaeiuWHOD+A'
        '|H_X<TLVB^8YF~^{-`9ZtDNoPh>wiLbAx&<UdSqsvZSM(c~W@DHl^`qnk*2a_%P$Ni%Xkc`#W=lQS&oMtYNe$$m+OkP$I8kH'
        '(QV$XhXW_IaQDoA|XEzxbmE{34BhgU94E+L93WCTk6`EW}gEIfkfQ_<wX)j-&'
    )
    raw=np.frombuffer(zlib.decompress(base64.b85decode(packed)),dtype='<i4').astype(float)*1e-5
    return np.arange(len(raw))*.02, raw*(.03*G/np.max(np.abs(raw)))


# Hz와 선택한 진폭(g 또는 cm) → 같은 사인 지반운동의 가속도/변위.
# 변위 진폭을 고정하고 Hz를 높이면 가속도 진폭은 omega²에 비례해 커진다.
def ramp_envelope(t, duration, ramp_s):
    """처음과 끝 ramp_s초 동안 0→1→0으로 부드럽게 변하는 코사인 포락선과 1·2차 미분."""
    e=np.ones_like(t);de=np.zeros_like(t);dde=np.zeros_like(t)
    if ramp_s>0:
        for mask,tau,sign in ((t<ramp_s,t,1.),(t>duration-ramp_s,duration-t,-1.)):
            k=np.pi/ramp_s
            e[mask]=.5-.5*np.cos(k*tau[mask])
            de[mask]=sign*.5*k*np.sin(k*tau[mask])
            dde[mask]=.5*k*k*np.cos(k*tau[mask])
    return e,de,dde

def smooth_envelope(t,duration,start,end,profile="quintic"):
    # quintic은 E,E',E'' 연속. cosine은 E,E' 연속이며 E''는 접속점에서 불연속일 수 있다. 해석 미분을 사용한다.
    E=np.ones_like(t);dE=np.zeros_like(t);ddE=np.zeros_like(t)
    for length,ending in ((start,False),(end,True)):
        if length<=0:continue
        mask=t>duration-length if ending else t<length
        z=(duration-t[mask])/length if ending else t[mask]/length
        if profile=='cosine':
            E[mask]=.5-.5*np.cos(np.pi*z)
            dE[mask]=.5*np.pi*np.sin(np.pi*z)/length*(-1 if ending else 1)
            ddE[mask]=.5*np.pi**2*np.cos(np.pi*z)/length**2
        elif profile=='quintic':
            E[mask]=10*z**3-15*z**4+6*z**5
            dE[mask]=(30*z**2-60*z**3+30*z**4)/length*(-1 if ending else 1)
            ddE[mask]=(60*z-180*z**2+120*z**3)/length**2
        else:raise ValueError('램프 방식은 quintic 또는 cosine이어야 합니다.')
    return E,dE,ddE

def ground_motion(t,ag,initial_velocity=0.):
    dt=np.diff(t)
    v=initial_velocity+np.r_[0,np.cumsum(dt*(ag[:-1]+ag[1:])/2)]
    return np.r_[0,np.cumsum(dt*v[:-1]+dt**2*(2*ag[:-1]+ag[1:])/6)]


def laboratory_input(hz, amplitude, mode='가속도 진폭 (g)', cycles=None,ramp_cycles=None,*,ramp_start=0.,ramp_end=0.,ramp_profile='quintic'):
    """변위 x=A sin(ωt)에 대응하는 가속도 -ω²A sin(ωt)를 만든다.
    cycles를 주면 실험 시간 = 가진 횟수 / 진동수, 없으면 기존처럼 30초."""
    if not math.isfinite(hz) or hz <= 0:
        raise ValueError('진동수는 유한한 양수 Hz로 입력하세요.')
    if not math.isfinite(amplitude) or amplitude < 0:
        raise ValueError('진폭은 유한한 0 이상 값으로 입력하세요.')
    if hz >= 25:
        raise ValueError('현재 시간 간격에서 진동수는 25 Hz 미만이어야 합니다.')
    if cycles is None:
        duration = 30.
    else:
        if not math.isfinite(cycles) or cycles != int(cycles) or not 1 <= cycles <= 1000:
            raise ValueError('가진 횟수는 1~1000 사이의 정수로 입력하세요.')
        duration = cycles/hz
        if duration > 600:
            raise ValueError(f'실험 시간이 {duration:.0f}초로 너무 깁니다. 600초 이하가 되도록 가진 횟수를 줄이세요.')
    if ramp_cycles is not None:
        if ramp_start or ramp_end:raise ValueError('공통 램프 주기와 개별 램프 시간을 동시에 지정할 수 없습니다.')
        if not np.isfinite(ramp_cycles) or ramp_cycles<0:raise ValueError('램프 주기 수는 유한한 0 이상이어야 합니다.')
        ramp_start=ramp_end=float(ramp_cycles)/hz
        ramp_profile='cosine'
    if ramp_profile not in ('quintic','cosine'):raise ValueError('램프 방식을 확인하세요.')
    omega = 2*np.pi*hz
    if mode == '가속도 진폭 (g)':
        accel = amplitude*G
        displacement = accel/omega**2
    elif mode == '변위 진폭 (cm)':
        displacement = amplitude/100
        accel = omega**2*displacement
    else:
        raise ValueError('진폭 입력 방식을 선택하세요.')
    if not math.isfinite(accel) or not math.isfinite(displacement):
        raise ValueError('진동수 또는 진폭이 너무 큽니다.')
    # 조화 입력의 선형 보간 오차를 줄이도록 한 주기당 최소 100개 표본을 둔다.
    dt=min(.02,1/(100*hz))
    t=np.linspace(0.,duration,int(math.ceil(duration/dt))+1)
    signal = -accel*np.sin(omega*t)
    meta = dict(wave='단방향', harmonic_hz=hz, amplitude_mode=mode,
        amplitude_value=amplitude, displacement_amplitude_m=displacement,
        site_pga_g=accel/G, bearing_deg=0., cycles=cycles if cycles is not None else duration*hz, duration_s=duration,
        initial_ground_velocity_m_s=omega*displacement,
        phase='x=A sin(2πft), a=-(2πf)² A sin(2πft)')
    if ramp_start or ramp_end:
        if not all(np.isfinite([ramp_start,ramp_end])) or min(ramp_start,ramp_end)<0 or ramp_start+ramp_end>duration:
            raise ValueError('램프 시간은 0 이상이며 합이 해석 시간 이하여야 합니다.')
        envelope,first,second=smooth_envelope(t,duration,ramp_start,ramp_end,ramp_profile)
        phase=omega*t
        if mode=='변위 진폭 (cm)':
            ground=displacement*envelope*np.sin(phase)
            signal=displacement*((second-omega**2*envelope)*np.sin(phase)+2*omega*first*np.cos(phase))
            velocity=displacement*(first*np.sin(phase)+omega*envelope*np.cos(phase))
            initial_velocity=float(velocity[0])
        else:
            signal=-accel*envelope*np.sin(phase)
            initial_velocity=omega*displacement if ramp_start==0 else 0.
            ground=ground_motion(t,signal,initial_velocity)
        meta.update(ground_displacement_m=ground.tolist(),initial_ground_velocity_m_s=initial_velocity,
            site_pga_g=float(np.max(abs(signal))/G),max_displacement_m=float(np.max(abs(ground))))
    else:meta['max_displacement_m']=displacement
    meta.update(ramp_start_s=float(ramp_start),ramp_end_s=float(ramp_end),ramp_profile=ramp_profile,
        ramp_cycles=ramp_cycles,ramp_scope='코사인 포락선은 2차 미분이 접속부에서 불연속일 수 있음' if ramp_profile=='cosine' else 'quintic 포락선 2차 미분 연속',
        max_acceleration_m_s2=float(np.max(abs(signal))),input_scope='사용자 조화 가진; 논문 실제 진동대 기록 아님')
    return t, signal, meta


QUAKE_NOTES={
    '단방향':'실험실 조화 가진 · 세계 X방향. 진동수와 진폭을 직접 지정합니다. 기본 0.01 g는 실행용 가정값입니다. 건물의 초기 상대 변위·속도는 0입니다.',
    '고베지진':'1995년 JMA 고베 남북 실측. 가까운 관측소에서 기록된 급격한 흔들림입니다. 첫 40초를 사용합니다.',
    '멕시코시티 지진':'1985년 호수 퇴적층 관측 특성을 본뜬 합성파입니다. 약 2초 주기 성분을 증폭해 길게 흔들립니다.',
    '엘센트로 지진':'1940년 엘센트로 남북 실측. 기존에 사용한 31.16초 기록입니다.'}
# JMA Kobe: https://www.data.jma.go.jp/eqev/data/kyoshin/jishin/hyogo_nanbu/index.html
# Mexico City: USGS OFR 85-731 그림 3. 관측 지반의 장주기 성분을 설명하는 교육용 모델.
# 지진 종류 → 시간과 지반 가속도 배열. 고베·엘센트로는 내장 기록, 멕시코시티는 특성 모사 합성파.
# 실측 지진의 모든 방향 성분·지반 특성을 재현하지 않는다.
def quake_wave(kind, hz=1.):
    if kind=='엘센트로 지진':return recorded_input()
    if kind=='고베지진':
        import base64,zlib
        packed=(
            'c-qZa33N_p8h*Ze|38Zo6jg@Qn#7t2At7Q3=IF6kEScIFI_MD7TGCo;pOgk;Xe_Z+Z4pbT(kdfo(pUyzXceOlHPo8*|L?uey'
            'qR>)nd6j1{y(_qyyxEk-tT+A_df6QKJRybpy2Q=#0oo#G6qFh%hmbM8go(SJdb!E_jiqCzCFob_%HUX@jTC5xEr5e^IzO`+{'
            'F!7xcR>vKb~uM;OY*}KMh}3@hlFe;U$z4SNz~5th>Ur#McG=b7c%(65V!Jzj_+h?yTve=!mPj`grVx`3o;Z)7)8uMH%nwg1)'
            '(n6Rzk$No(ix)+l%H*WhALEv%Q66bIa?bI;0^lH9+QgpR+6n2W>Za5wEmUPQlg_kJ8N!FQWGVku57J!#B~*msnqh8KrhMcqf'
            'ZT90tEc0K7R&YtFJdqa2Xd`Z@~?-Q^nsoeVhiq3`?(&t@W|9NO;Q7|kiy$vs<XBG9ECEShsgXhujQH1}F++AnBC8Wu&euMhD'
            ';lIeD`uhKQe-jH7+h>t0#0LCw?#crDgV;P4-19WZdJZz(NlugN7&*6*`*$?pq*%U>H*?9fOfoF5z-Rure4htP18HS|hVnf8r'
            'p&oTIv<eL?~_5<<Y|egri^?0uFU_w;Q3u|pzo`|sPaISI>4|HphgYgUKL<-Szyx*@_GjOjRG3C1U7mB$yX%?8Sfnd^d1CQ9|'
            'QB30c*Meb|3jI>*r&T5(e~?c$N&4^&`lB6Ueq($m!pat0d;x;&Wyad15wsdo|fRjT|KNuhs|7=8(I-B3m3Lqfe4i7YpKUCGX'
            'Nl;tozHZ!IVD=hqtucuH12+adAmfKMv9rW$bSeV|V>pyO$>$vU#uCuDP3WA1sf@@+C+o=y8LP<<>=c?MvM1%eZRxi!T$2=1d'
            'ueI@Dfj^Ne{h!TA2ivY|JjLr>}_mwpw4w8G<lgT^C-4bWo;sUF6lx%&BoFq67?F&ro4RjE^Dw<@9yhr}^jUhl?S-)F5;Cx%4'
            'spMqF8q%Icz9X0(94GnwoZK@+@cNcqUJlTY3kN?H|3N_31|V8+4y;73yKAwojF}}^Ocv}~UnZON1HRb_yfP7pJ0dyUPTo%f#'
            '`ad&p9)Nu7-oGAn4=UPbX16HEx$LBUkU#b#ZOElz~c_NAOIM0LgGzQ2wtHfv7wImc{<MMHpG2sL&yaiCPdm%&c}{3!*#^9S6'
            'KU@@a-=qQ<RhCD&=wim|Pz3k;`eJxg2>hhx5wjaPp{Z9+{oPJDVNMzG1S;Lvp+YBzbA5o2(&lkA_Q08ln@#LNy$jq;PREFhR'
            'I5HWWy`50sUAA9-p>pQ<79M-7Xb>j;~sV}n!2+)Fl8$hPCeB@ZlV;fWamp6FH16Q$%lIm8p|CVC)YwhhKPh1Ip>J%2XXe}$8'
            'Js)HSL2S>Ke<A~<DOv%dTgPmEdHawGSKYGMv>mRXnr!0o}$oqWhU}}cJh`AOw?IHao*Y@%X|BloUJ6gx-2pgt8v|(@^I|hGd'
            '!}UBJKl$mnpRO=fiX`K<#o<#drZlxUG{a=|H75Tt$7Dc9ldse^IiZiq(l(2+!o|34Qmc&>ayKe?-&go+l;ANKc;j+GeZRII='
            '=CRst^ZPZGe|?i0S&su(5}1<YPt=>XW8K4Wy8JRI{NI>5cax;A;T0lUKD<(0E>?b7nTD7(}4!Jfq7jOYRDS3a)B=n2_J$Kd{'
            '!!aP+wt0CXilPAx`RhzzB=wZkgP%(4zBqWRG3sDbc31@iH$4a0vf~Cn$v0(eb{aBkxNcjkaspl&COHVqP#`^zSzokG~~2u5x'
            'fuWFBK$<kF*Y4#(fi;=mi39Pm~afA7qpUoC^zCjfqfb)@gsB_<ml-L)hBV>^z0prihJg+1HIb3;vzS>xpDpB+R6Ikz(SZJ5P'
            'uspZ;}G<+RsLqv|uY37O0E1odpys+||7eXVw{>zh?Gj>#sv0>|LI)Z~0n#{3Sv7^Cji<~^%*<gFaVC)uyF$<lnDSVka%*ho&'
            'lCyeb=Pm`c{i?*-QZ%T)Xl$Hl!W@6HVv@zGGcBqqWd8_>b(V%79K!SII{MLu*i9bT+szZL26(_>ikMYXDAV2ICnucr+n>k8?'
            'jo)Yav2bp$2*mr46a}>)x+fMiWaAPlUpSpBb!R@k}Wn#H|T%T$tBSSw;VIs^Mb{E4QuSH;e1mYJQMBktK@-2eje!f$d0a`+H'
            's(@9XJ1OgW27NBU5#>xS|j!Jz$WR#n52}lS?}pGRQ&wii4gV3{IVC(m%oCkHWw0$ALo`z`7`)i)hq$|Fr1a(4zg2Nw2;pZAT'
            '4mYiclYfs?&PJDCfE*~td`3E%B4EmoUvG2)EH(eY%dUDEGvC?wc*1YOmU*~Nw$6{Mcq>4+GwA+3UjH?AveU!`#VJq5323ITf'
            '+cvj(yhf)I$g_JTHRG@}GHq<al>aDxzh0jvyH+M`%%rIE{mXoD>864<uGTty5b;#mo=~KRY$#HF@k6sgvj8-_=Lu%~-P%0hR'
            'FSQUIq7W(T{kfWk>d~TymlgK?1PneaeI><W=QNWGLQO7yXz*cWlbQFVo`cEboq(!#(T1f84ru5UtYK7T4I_6egc-ow(s%a{B'
            '71&qabTpyb+=8%E;V_riOC;C3%0E^>C;I3@3we(wB%a!-M5><fo2*OW@y;$t>f?o4LJ=oTxqUw_+5!#_5>XsNp5yZJ(iN5In'
            '<)JhsCu=#MgT!*G@F~y1&JY=451J>3=t+Z@;S$@x6i(rXhZehLkoMnq5$s60R^!^ycy@a=zp!X$;xEEBPN#@=r|'
        )
        a=np.frombuffer(zlib.decompress(base64.b85decode(packed)),dtype='<i4')*1e-5
        t=np.arange(len(a))*.02
    elif kind=='단방향':
        t, a, _ = laboratory_input(hz, .01)
        return t, a
    elif kind=='멕시코시티 지진':
        t=np.arange(3001)*.02
        rng=np.random.default_rng(1985)
        freq=np.linspace(.18,3.2,96)
        gain=1+7*np.exp(-.5*((freq-.50)/.075)**2)
        phase=rng.uniform(0,2*np.pi,len(freq))
        a=(gain[:,None]*np.sin(2*np.pi*freq[:,None]*t+phase[:,None])).sum(axis=0)*np.sin(np.pi*t/t[-1])**2
    else:raise ValueError('알 수 없는 지진 유형입니다.')
    # 재생 시 지면의 누적 표류를 줄인다. 상수와 직선 추세를 제거해 종료 속도·변위를 0으로 둔다.
    def end_motion(acc):
        dt=np.diff(t)
        v=np.r_[0,np.cumsum(dt*(acc[:-1]+acc[1:])/2)]
        return [v[-1],np.sum(dt*v[:-1]+dt**2*(2*acc[:-1]+acc[1:])/6)]
    basis=np.stack([np.ones_like(t),t],axis=1)
    a=a-basis@np.linalg.solve(np.array([end_motion(col) for col in basis.T]).T,end_motion(a))
    return t,a*(.03*G/max(abs(a)))


# ── 논문 검증 예제 ────────────────────────────────────────────────
# 4층 철골 모형 + 4층 꼭대기 U형 TLCD, 단방향 진동대 조화 가진.
# 관 안지름은 논문에 없어 물 965 g과 물기둥 길이 30.53 cm에서 역산했다.
# 관 자체 질량은 논문에 없다(0으로 둠).




AIR_MODE_LABELS={'stop':'정밀(공기 유입 시 중단)','slug':'근사(물기둥 미끄럼)','off':'판정 끔(참고 계산)'}
AIR_MODE_KEYS={v:k for k,v in AIR_MODE_LABELS.items()}


# 논문에는 진동대 시작 방식이 없다. 실제 진동대의 일반적인 서서히 시작·끝을 가정한 값.








def load_input(path, unit,*,metadata=False):
    """헤더 time_s,accel의 CSV를 읽는다. 단위는 명시적으로 선택한다."""
    data = np.genfromtxt(path, delimiter=',', names=True, encoding='utf-8-sig')
    if data.dtype.names not in (('time_s','accel'),('time_s','accel_m_s2')):
        raise ValueError('CSV 헤더는 time_s,accel 또는 time_s,accel_m_s2 이어야 합니다.')
    t, a = np.atleast_1d(data['time_s']), np.atleast_1d(data[data.dtype.names[1]])
    if len(t) < 3 or not np.all(np.isfinite(t)) or not np.all(np.isfinite(a)):
        raise ValueError('CSV에 유효한 숫자 행이 3개 이상 필요합니다.')
    if np.any(np.diff(t) <= 0):
        raise ValueError('시간은 중복 없이 증가해야 합니다.')
    factor = {'m/s2': 1.0, 'g': G, 'cm/s2': 0.01}[unit]
    signal=a*factor
    if metadata:
        return t-t[0],signal,dict(wave='CSV 기록',csv_file=str(Path(path).resolve()),unit=unit,
            original_start_s=float(t[0]),original_end_s=float(t[-1]),samples=len(t),
            min_dt_s=float(np.diff(t).min()),max_dt_s=float(np.diff(t).max()),
            site_pga_g=float(np.max(abs(signal))/G),bearing_deg=0.,distance_km=0.,strength=float(np.max(abs(signal))/G),
            east=0.,north=0.,depth=0.,harmonic_hz=None,input_scope='CSV 가속도 직접 입력; 거리 배율/정규화/합성/램프 없음')
    return t-t[0],signal


# state의 열 4,6,0은 각각 장치 없음/같은 질량 고정/유체가 움직이는 건물의 지붕 변위.
# valid=False이면 전체 구간 저감률을 반환하지 않는다. 부분 결과는 partial_metrics()에서 별도 표시한다.
def metrics(result):
    # 넘침/바닥 도달 후에는 전체 기록의 저감률을 보고하지 않는다.
    if not result['valid']:
        return None
    # 세 비교 대상의 지붕 상대 변위를 같은 시간 구간으로 꺼낸다.
    x = result['state'][:, [4, 6, 0]]
    peak = np.max(np.abs(x), axis=0)
    # 제곱 변위를 시간 적분하고 전체 시간으로 나눈 뒤 제곱근을 취한다. 표본이 등간격이 아니어도 사용 가능하다.
    rms = np.sqrt(np.trapezoid(x*x, result['t'], axis=0) / np.ptp(result['t']))
    acc = np.max(np.abs(result['acc']), axis=0)
    acc_rms=np.sqrt(np.trapezoid(result['acc']**2,result['t'],axis=0)/np.ptp(result['t']))
    def reduction(values, base):
        # 양수는 응답 감소, 음수는 증가. 기준 응답이 거의 0이면 나눗셈 대신 None을 반환한다.
        return float(100 * (1-values[2]/values[base])) if values[base] > 1e-12 else None
    return {'peak_displacement_m': peak.tolist(), 'rms_displacement_m': rms.tolist(),
            'peak_absolute_acceleration_m_s2': acc.tolist(),
            'rms_absolute_acceleration_m_s2':acc_rms.tolist(),
            'peak_reduction_vs_bare_pct': reduction(peak, 0),
            'peak_reduction_vs_fixed_pct': reduction(peak, 1),
            'rms_reduction_vs_bare_pct': reduction(rms, 0),
            'acceleration_reduction_vs_bare_pct': reduction(acc, 0),
            'peak_water_displacement_m': float(np.max(np.abs(result.get('levels',result['state'][:,2]))))}



def partial_metrics(r):
    if r['valid']:return dict(scope='전체 입력 구간',metrics=metrics(r))
    end=r['n_valid']
    if end<2 or r['t'][end-1]<=r['t'][0]:
        return dict(scope='유효 동적 구간 없음',metrics=None)
    clipped=dict(r)
    for key in ('t','state','acc','levels'):
        if key in clipped:clipped[key]=clipped[key][:end]
    clipped['valid']=True
    return dict(scope='모델 적용 가능 구간만; 전체 지진 성능 아님',
        start_s=float(r['t'][0]),end_s=float(r['t'][end-1]),metrics=metrics(clipped))


def setup_plot():
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    for name in ['Malgun Gothic', 'AppleGothic', 'NanumGothic']:
        if name in names:
            plt.rcParams['font.family'] = name
            break
    plt.rcParams['axes.unicode_minus'] = False
    return plt


def draw_geometry(ax, d):
    ax.clear()
    top = d.leg_length if d.leg_length is not None else d.h + d.freeboard
    ax.plot([-d.B/2, -d.B/2, d.B/2, d.B/2], [top, 0, 0, top],
            lw=12, color='#cbd5e1', solid_capstyle='butt')
    ax.plot([-d.B/2, -d.B/2, d.B/2, d.B/2], [d.h, 0, 0, d.h],
            lw=6, color='#0284c7', solid_capstyle='butt')
    ax.plot([-d.B/2,d.B/2],[0,0],color='#111827',ls='--',lw=1)
    ax.annotate('',xy=(d.B/2,-.04),xytext=(-d.B/2,-.04),arrowprops=dict(arrowstyle='<->',color='#111827'))
    ax.text(0,-.045,f'B = {d.B*100:.3f} cm',ha='center',va='top',fontsize=8)
    xh=d.B/2+.045
    ax.annotate('',xy=(xh,d.h),xytext=(xh,0),arrowprops=dict(arrowstyle='<->',color='#111827'))
    ax.text(xh+.005,d.h/2,f'h = {d.h*100:.3f} cm',va='center',fontsize=8)
    ax.axhline(d.h, color='#0284c7', ls=':', lw=1)
    ax.text(0, top, f'B={d.B:.2f} m | h={d.h:.2f} m\nD_i={1000*d.diameter:.2f} mm | L=B+2h={d.length:.5f} m', ha='center', va='bottom', fontsize=9)
    ax.set(xlim=(-d.B/2-0.12, d.B/2+0.12), ylim=(-0.06, top+0.13),
           title='U자 관 측면 · 파란색 = 정지 상태의 물', xlabel='수평 거리 [m]', ylabel='높이 [m]')
    ax.set_aspect('equal', adjustable='box')


def draw_result(fig, axes, b, d, r, title):
    geometry, plan, disp, accel, water, info = axes
    for ax in axes:
        ax.clear()
    if d.shape=='U형' and not d.separate_u:draw_geometry(geometry,d)
    else:
        feet,up,leg,starts,ends=network(d)[:5]
        geometry.remove();geometry=fig.add_subplot(3,2,1,projection='3d')
        for start,end in zip(starts,ends):
            geometry.plot(*np.stack((start,end)).T,color='#258aae',lw=5)
        for i,(start,direction) in enumerate(zip(feet,up)):
            wet=np.broadcast_to(leg,len(feet))[i]
            top=start+direction*(u_dimensions(d)[4][i] if d.separate_u else d.leg_length if d.leg_length is not None else wet+d.freeboard/direction[2])
            geometry.plot(*np.stack((start,top)).T,color='#9bb2bf',lw=5)
            geometry.plot(*np.stack((start,start+direction*wet)).T,color='#258aae',lw=3)
            geometry.text(*top,str(i+1))
        geometry.set_title(shape_label(d)+' · 기둥 번호');geometry.set_axis_off()
    theta = math.radians(d.angle)
    plan.annotate('', xy=(1, 0), xytext=(-1, 0), arrowprops=dict(arrowstyle='->', color='#ef4444', lw=2))
    plan.plot([-math.cos(theta), math.cos(theta)], [-math.sin(theta), math.sin(theta)], color='#0284c7', lw=5)
    plan.set(xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), title=f'위에서 본 설치 방향: θ={d.angle:.0f}°')
    plan.text(0, -1.18, '빨강: 지진 방향 / 파랑: 관 수평축', ha='center', fontsize=9)
    plan.set_aspect('equal'); plan.axis('off')
    labels = ['장치 없음', '동일 질량 고정', 'TLCD']
    colors = ['#64748b', '#f59e0b', '#0284c7']
    for j, column in enumerate([4, 6, 0]):
        disp.plot(r['t'], 1000*r['state'][:, column], label=labels[j], color=colors[j], lw=1.1)
        accel.plot(r['t'], r['acc'][:, j]/G, color=colors[j], lw=1.0)
    disp.set(title='건물의 지면 대비 변위', ylabel='변위 [mm]'); disp.legend(fontsize=8, ncol=3)
    accel.set(title='건물 절대가속도', ylabel='가속도 [g]')
    if 'levels' in r:
        for j,level in enumerate(r['levels'].T):water.plot(r['t'],1000*(level+np.broadcast_to(r['rest_height'],r['levels'].shape[1])[j]),label=f'기둥 {j+1}')
        for bound in np.unique(r['lower_water']+r['rest_height']):water.axhline(bound*1000,color='red',ls='--')
        for bound in np.unique(r['upper_water']+r['rest_height']):water.axhline(bound*1000,color='red',ls=':')
        water.legend(fontsize=8);water.set(title='수면 높이 기준: 바닥 관 중심선',ylabel='실제 높이 [mm]')
    else:
        water.plot(r['t'], 1000*r['state'][:, 2], color='#0284c7')
        rest,lower,upper=column_water_heights(d)
        for bound in (lower[-1]-rest[-1],upper[-1]-rest[-1]):
            water.axhline(1000*bound, color='#dc2626', ls='--')
        water.set(title='오른쪽 수면 변화(왼쪽은 반대가 됨)', ylabel='수면 변화 [mm]')
    for ax in [disp, accel, water]:
        ax.set_xlabel('시간 [s]'); ax.grid(alpha=0.2)
        if not r['valid']:
            ax.axvline(r['failure_time'], color='red', ls=':')
    info.axis('off')
    m = metrics(r)
    text = (f'물 질량: {d.mass:.3f} kg ({100*d.mass/b.mass:.1f}%)\n'
            f'관 질량: {b.container_mass:.3f} kg\n'
            f'건물 / 액체 고유진동수: {b.frequency:.3f} / {d.frequency:.3f} Hz\n'
            f'전체 물기둥 길이 L: {d.length:.3f} m\n')
    if m is None:
        text += f"\n{r['failure_time']:.3f}초: 수면 한계 도달\n계산 중단 · 전체 저감률 산출 불가"
    else:
        fmt = lambda v: '정의 불가' if v is None else f'{v:+.1f}%'
        text += '\n최대 변위 [mm] (없음 / 고정 / TLCD)\n' + ' / '.join(f'{v*1000:.2f}' for v in m['peak_displacement_m'])
        text += f"\n\n최대 변위 저감 (장치 없음 대비): {fmt(m['peak_reduction_vs_bare_pct'])}"
        text += f"\n최대 변위 저감 (고정 질량 대비): {fmt(m['peak_reduction_vs_fixed_pct'])}"
        text += f"\nRMS 변위 저감 (장치 없음 대비): {fmt(m['rms_reduction_vs_bare_pct'])}"
        text += f"\n최대 가속도 저감 (장치 없음 대비): {fmt(m['acceleration_reduction_vs_bare_pct'])}"
        text += '\n\n양수 = 감소 / 음수 = 악화'
    info.text(0, 1, text, va='top', fontsize=9)
    fig.suptitle('TLCD 형상·방향 실험 | '+title, fontsize=13)


def save_result(folder, b, d, r, fig, title):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder/'response.png', dpi=160)
    np.savetxt(folder/'time_history.csv', np.column_stack([r['t'], r['ag'], r['state'], r['acc']]),
               delimiter=',', header='time_s,ground_accel_m_s2,x_tlcd_m,v_tlcd_m_s,water_y_m,water_v_m_s,x_bare_m,v_bare_m_s,x_fixed_m,v_fixed_m_s,acc_bare_m_s2,acc_fixed_m_s2,acc_tlcd_m_s2', comments='')
    payload = {'building': asdict(b), 'damper': asdict(d), 'input': title,
               'valid': r['valid'], 'failure_time_s': r['failure_time'],
               'metric_array_order': ['bare', 'fixed_mass', 'tlcd'], 'metrics': metrics(r)}
    payload['orifice']=dict(mode='직접 ξ' if d.xi is not None else '개구비',xi_scope=d.xi_scope,beta_applied=d.xi is None,beta=d.beta,xi=d.loss,pipe_loss=d.pipe_loss if d.xi is None or d.xi_scope=='local' else None,velocity_basis='mean conduit velocity',model='orifice + explicit additional local loss; branching applicability unvalidated')
    payload['installed']=r.get('installed',True)
    if not payload['installed']: payload['damper']=None
    payload['source'] = r.get('source')
    payload['failure_detail']=r.get('failure_detail')
    payload['fluid_model']=r.get('fluid_model')
    payload['fluid_properties']=r.get('fluid_properties')
    payload['fluid_scope']=r.get('fluid_scope')
    payload['computational_work']=r.get('computational_work')
    payload['physics_limits']=[
        '선형 전단 건물: 비틀림·전도 회전·소성·지반-기초 상호작용 미포함',
        '1차원 물기둥 근사: 접합부 3차원 흐름·기포·부분 충수·슬로싱 미해석',
        '오리피스와 명시한 추가 관 손실 사용; 비정상 점성 이력·분기점 흐름 미해석',
        '수평관 천장 경계는 보수적 적용 제한이며 공기 유입 확정 조건 아님']
    payload['geometry_scope']=r.get('geometry_scope')
    rest,lower,upper=column_water_heights(d)
    payload['water_geometry']=dict(h_definition='volume parameter: vertical liquid volume = 2*A*h',h_m=d.h,rest_heights_m=rest.tolist(),lower_heights_m=lower.tolist(),upper_heights_m=upper.tolist(),column_spacing_basis='inner diameter; wall thickness excluded',tuning_ratio_x=d.frequency/tuning_frequency(b))
    payload['valid_interval_metrics']=partial_metrics(r)
    payload['building_summary']=building_summary(b,r)
    payload['input_application']=dict(
        h='물 질량·안지름·B로 계산된 값; 독립 직접 입력으로 사용하지 않음',
        source='단방향 모드는 실험실 진폭/Hz를 사용하며 진원 좌표/strength를 사용하지 않음' if r.get('source',{}).get('wave')=='단방향' else 'CSV 원본 직접 입력; 배율 없음' if r.get('source',{}).get('wave')=='CSV 기록' else '진원 방향과 가상 거리 배율로 기록 조정',
        damping=b.damping_mode,structural_C_X=structural_damping(b)[0].tolist(),structural_C_Y=structural_damping(b)[1].tolist(),
        density_kg_m3=d.rho)
    (folder/'summary.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


# 형상×각도 비교. 총 L과 단면적을 유지하면서 B를 바꾸고 h=(L-B)/2로 조정한다.
# 최적 설계 창의 탐색은 search_designs()를 사용하므로 변수 조합 규칙이 다르다.
def sweep(b, d, t, ag, folder=None, metric="peak_reduction_vs_bare_pct"):
    """총 물 길이와 지름을 유지하면서 B/L과 설치 각도를 비교한다."""
    plt = setup_plot()
    ratios = np.array([0.35, 0.50, 0.65, 0.80])
    angles = np.arange(0, 91, 15)
    values = np.full((len(ratios), len(angles)), np.nan)
    rows = []
    for i, ratio in enumerate(ratios):
        for j, angle in enumerate(angles):
            test = replace(d, B=d.length*ratio, h=d.length*(1-ratio)/2, angle=float(angle))
            reason=''
            try:
                r=simulate_space(b,test,t,ag);m=metrics(r)
                tuning=test.frequency/tuning_frequency(b)
            except ValueError as error:
                r={'valid':False};m=None;tuning=None;reason=str(error)
            if m is not None and m['peak_reduction_vs_bare_pct'] is not None:
                values[i, j] = m[metric]
            rows.append({'B_over_L': ratio, 'angle_deg': angle, 'B_m': test.B, 'h_m': test.h, 'tuning_ratio_x':tuning,'reason':reason,
                         'water_mass_kg': test.mass, 'valid': r['valid'],
                         'peak_reduction_vs_bare_pct': m['peak_reduction_vs_bare_pct'] if m else '',
                         'rms_reduction_vs_bare_pct': m['rms_reduction_vs_bare_pct'] if m else '',
                         'peak_reduction_vs_fixed_pct': m['peak_reduction_vs_fixed_pct'] if m else '',
                         'acceleration_reduction_vs_bare_pct': m['acceleration_reduction_vs_bare_pct'] if m else ''})
    if folder is not None:
        folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
        with (folder/'sweep.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    fig, ax = plt.subplots(figsize=(10, 4.5), layout='constrained')
    pizza = d.shape=='피자 거치대'
    finite = np.abs(values[np.isfinite(values)])
    bound = max(float(np.max(finite)) if len(finite) else 1, 1)
    cmap = plt.get_cmap('RdBu').copy(); cmap.set_bad('#dddddd')
    im = ax.imshow(values, cmap=cmap, vmin=-bound, vmax=bound, aspect='auto')
    for i in range(len(ratios)):
        for j in range(len(angles)):
            valid_run=rows[i*len(angles)+j]['valid']
            label=f'{values[i,j]:+.{3 if pizza else 1}f}%' if np.isfinite(values[i,j]) else ('기준값 0' if valid_run else '치수 오류' if rows[i*len(angles)+j]['reason'] else '한계 초과')
            ax.text(j, i, label, ha='center', va='center', fontsize=9)
    ax.set(xticks=range(len(angles)), xticklabels=angles, yticks=range(len(ratios)), yticklabels=[f'{ratio:g} | r='+ (f"{rows[i*len(angles)]['tuning_ratio_x']:.4g}" if rows[i*len(angles)]['tuning_ratio_x'] is not None else '—') for i,ratio in enumerate(ratios)],
           xlabel='지진 방향과 1번 가지 사이 각도 [도]' if pizza else '지진 방향과 설치 방향 사이 각도 [도]',
           ylabel='B/L · 현재 조율비 r (X 1차 기준)',
           title=('RMS' if metric.startswith('rms') else '최대')+' 건물 변위 저감률 · 장치 없음 대비\n총 물 길이·물 질량 일정 · 자동 재조율 없음 / 양수: 감소, 음수: 악화')
    fig.colorbar(im, ax=ax, label='저감률 [%]')
    if folder is not None: fig.savefig(folder/'sweep.png', dpi=160)
    plt.close(fig)
    return fig




@lru_cache(maxsize=128)
def tuning_frequency(b):
    mass,k,_,_=b.floor_data()
    D=np.eye(len(mass))-np.eye(len(mass),k=-1)
    return float(modes(np.diag(mass),D.T@(k[:,None]*D))[0][0]/(2*np.pi))

# 탐색 B·조율비·설치 층 → 계산 가능한 Building/Damper 한 쌍.
# 주 화면의 조율비를 기본 고정값으로 사용하며, 최적 탐색에서는 r 범위로 변경할 수 있다.
def search_trial(b,d,B,ratio,floor):
    floor_value=float(floor)
    if not floor_value.is_integer() or not 1<=floor_value<=len(b.floor_data()[0]):
        raise ValueError('설치 층은 건물 범위 안의 정수여야 합니다.')
    if ratio is None:
        test=replace(d,B=float(B),h=(d.length-B)/2)
    elif equivalent_u(d):
        if not np.isfinite(ratio) or ratio<=0:raise ValueError('조율비는 양수여야 합니다.')
        L=2*G/(2*np.pi*tuning_frequency(b)*ratio)**2
        if B<=0 or B>=L:raise ValueError('B < L이어야 합니다. 조율비 또는 B를 줄이세요.')
        area=d.mass/(d.rho*L)
        test=replace(d,B=float(B),h=(L-B)/2,diameter=math.sqrt(4*area/np.pi))
    else:
        if not np.isfinite(ratio) or ratio<=0 or not np.isfinite(B) or B<=0:
            raise ValueError('조율비와 B는 유한한 양수여야 합니다.')
        # U형 공식을 다른 형상에 대입하지 않고 기존 유체 M,K의 최저 고유진동수를 사용한다.
        # 모든 단면을 같은 비율로 확대하면 고유진동수는 유지되고 물 질량만 비례한다.
        target=ratio*tuning_frequency(b)
        def frequency(height):
            trial=replace(d,B=float(B),h=height,tops=(),leg_length=None)
            return trial.frequency
        lo=1e-10;hi=max(d.h,.1)
        if frequency(lo)<target:
            raise ValueError('이 B에서 목표 유체 진동수까지 높일 수 없습니다. B 또는 조율비를 줄이세요.')
        for _ in range(80):
            if frequency(hi)<=target:break
            hi*=2
        else:raise ValueError('물높이 조율의 해를 찾지 못했습니다.')
        for _ in range(48):
            if hi-lo<=1e-11*max(1.,hi):break
            mid=(lo+hi)/2
            if frequency(mid)>target:lo=mid
            else:hi=mid
        trial=replace(d,B=float(B),h=(lo+hi)/2)
        factor=math.sqrt(d.mass/trial.mass)
        test=replace(trial,diameter=trial.diameter*factor,
            bores=tuple(None if x is None else x*factor for x in trial.bores))
        # 사용자 지정 관 끝 높이는 유지하므로 넘침 여유가 없으면 validate에서 제외한다.
        if not np.isclose(test.frequency,target,rtol=1e-7):
            raise ValueError('조율비 수치해가 요청 진동수와 일치하지 않습니다.')
    model=replace(b,mount=int(floor_value))
    # 기본 2층 모델도 설치 층 변경을 그대로 결합행렬에 전달한다.
    if not model.masses:
        m,k,h,_=b.floor_data()
        model=replace(model,masses=tuple(m),stories=tuple(k),heights=tuple(h))
    validate(model,test)
    return model,test

# 물리 계산을 순서대로 수행하는 탐색 엔진. cache는 같은 건물·장치·가진을 고정한 창에서만 재사용한다.
# 초기 충수 부족은 적분 전에 제외하고, 중지 요청은 한 설계의 계산이 끝난 뒤 반영한다.
def optimization_input(t,ag,laboratory,amplitude):
    if amplitude is None:return t,ag,None
    if laboratory is None or laboratory.get('wave')!='단방향' or laboratory.get('amplitude_mode')!='가속도 진폭 (g)':
        raise ValueError('가속도 진폭 탐색은 단방향/가속도 진폭(g) 모드에서만 가능합니다.')
    if not np.isfinite(amplitude) or amplitude<0:raise ValueError('가속도 진폭은 유한한 0 이상 값이어야 합니다.')
    return laboratory_input(laboratory['harmonic_hz'],float(amplitude),'가속도 진폭 (g)',
        laboratory.get('cycles'),ramp_start=laboratory.get('ramp_start_s',0.),
        ramp_end=laboratory.get('ramp_end_s',0.),ramp_profile=laboratory.get('ramp_profile','quintic'))


def design_variant(d,tilt,columns):
    """탐색할 기울기·기둥 수를 기존 연결망 계산에 전달한다."""
    if not float(columns).is_integer():raise ValueError('기둥 수는 정수로 입력하세요.')
    if d.shape=='다기둥형' and not math.isclose(float(tilt),d.tilt):
        raise ValueError('일렬형에서는 기울기를 탐색하지 않습니다.')
    shape=d.shape
    if shape=='U형' and not d.separate_u:shape=internal_shape(shape,float(tilt))
    return replace(d,shape=shape,tilt=float(tilt),columns=int(columns))


def search_designs(b,d,t,ag,betas,angles,lengths,require_peak=True,ratios=None,floors=None,cache=None,stop=None,progress=None,air_mode='stop',amplitudes=None,laboratory=None,tilts=None,column_counts=None):
    tilts=[d.tilt] if tilts is None else list(tilts)
    column_counts=[d.columns] if column_counts is None else list(column_counts)
    rows=[];trial_cache={};baseline_cache={};signals={}
    amplitudes=[None] if amplitudes is None else list(amplitudes)
    if any(x is not None for x in amplitudes) and (laboratory is None or laboratory.get('wave')!='단방향' or laboratory.get('amplitude_mode')!='가속도 진폭 (g)'):
        raise ValueError('가속도 진폭 탐색에는 단방향 가속도 입력 조건이 필요합니다.')
    import hashlib
    input_key=hashlib.sha256(np.asarray(t).tobytes()+np.asarray(ag).tobytes()+repr(laboratory).encode()).digest()
    reused=0
    total=len(betas)*len(angles)*len(lengths)*(1 if ratios is None else len(ratios))*(1 if floors is None else len(floors))*len(amplitudes)*len(tilts)*len(column_counts)
    def report():
        if progress is not None:progress.update(total=total,completed=len(rows),reused=reused)
    report()
    for beta,angle,B,ratio,floor,amplitude,tilt,columns in itertools.product(betas,angles,lengths,
            [None] if ratios is None else ratios,[b.floor_data()[3]] if floors is None else floors,amplitudes,tilts,column_counts):
        if stop is not None and stop.is_set():break
        key=(float(beta),float(angle),float(B),None if ratio is None else float(ratio),float(floor),amplitude,air_mode,input_key,float(tilt),float(columns))
        # cache는 동일 건물·장치·가진을 고정한 한 탐색 창에서만 공유한다.
        row=dict(cache[key]) if cache is not None and key in cache else None
        if row is not None:reused+=1
        if row is None:
            row=dict(tilt=float(tilt),columns=float(columns),width_cm=None,depth_cm=None,height_cm=None,amplitude_g=amplitude,actual_peak_g=None,air_mode=air_mode,beta=float(beta),angle=float(angle),B=float(B),r=ratio,n=float(floor),fluid_scope='물 모델',internal_steps=None,peak_displacement_m=None,rms_displacement_m=None,peak_acceleration_m_s2=None,rms_acceleration_m_s2=None,peak_acceleration_reduction_pct=None,peak_water_m=None,
                h=None,diameter_m=None,area_m2=None,orifice_m2=None,mass_kg=d.mass,
                rms_pct=None,peak_pct=None,status='',reason='',eligible=False,failure_time_s=None,completion_pct=0.,initial_h_m=None,initial_D_m=None,B_limit_m=None)
            try:
                # 같은 B·조율비·설치 층에서는 형상 조율을 재사용한다. 개구비와 각도는 이후에 별도로 적용한다.
                if not float(floor).is_integer() or not 1<=float(floor)<=len(b.floor_data()[0]):
                    raise ValueError('설치 층은 건물 범위 안의 정수여야 합니다.')
                variant=design_variant(d,tilt,columns)
                geometry_key=(float(B),None if ratio is None else float(ratio),float(tilt),float(columns))
                if geometry_key not in trial_cache:
                    try:
                        trial_cache[geometry_key]=search_trial(b,variant,float(B),ratio,floor)
                    except ValueError as error:
                        # 같은 치수에서 확정된 기하·조율 오류도 재사용한다. 각 후보 행에는 원인을 계속 기록한다.
                        trial_cache[geometry_key]=error
                cached_geometry=trial_cache[geometry_key]
                if isinstance(cached_geometry,ValueError):
                    raise ValueError(str(cached_geometry))
                model,test=cached_geometry
                model=replace(model,mount=int(floor))
                test=replace(test,beta=float(beta),angle=float(angle))
                validate(model,test)
                row.update(r=test.frequency/tuning_frequency(b) if ratio is None else float(ratio),h=test.h,diameter_m=test.diameter,
                    area_m2=test.area,orifice_m2=test.area*test.beta if test.xi is None else None,initial_h_m=test.h,initial_D_m=test.diameter,
                    B_limit_m=test.length-test.diameter if equivalent_u(test) else None)
                extent=device_extent(test)   # 같은 공간 비교용: 장치 가로·세로·높이 (cm)
                row.update(width_cm=100*extent[0],depth_cm=100*extent[1],height_cm=100*extent[2])
                # 초기 물높이가 현재 충수 적용 경계보다 낮으면 적분 전에 별도 상태로 기록한다. 실제 공기 유입을 확정하는 판정은 아니다.
                if air_mode in ('stop','slug') and not initially_full(test):
                    row.update(status='초기 충수 조건 미달',reason=f'정지 수면이 수평관 천장(D/2={test.diameter/2:.6g} m) 이하; 시작부터 공기가 있어 제외',failure_time_s=float(t[0]),completion_pct=0.)
                    if cache is not None:cache[key]=dict(row)
                    rows.append(row);report()
                    continue
                # 모든 후보가 동일한 시간 배열과 지반 가속도를 받는 실제 계산 호출이다.
                if amplitude not in signals:signals[amplitude]=optimization_input(t,ag,laboratory,amplitude)
                tt,aa,excitation=signals[amplitude]
                row['actual_peak_g']=float(np.max(abs(aa))/G)
                if row['amplitude_g'] is None and laboratory is not None and laboratory.get('amplitude_mode')=='가속도 진폭 (g)':
                    row['amplitude_g']=laboratory.get('amplitude_value')
                result=simulate_space(model,test,tt,aa,_baseline_cache=baseline_cache,air_mode=air_mode)
                if result['air_mode']!=air_mode:raise ValueError('선택한 수면 처리 모드는 이 형상에서 지원하지 않습니다.')

                # 전체 기록을 완료한 경우에만 RMS·최대값을 성능 점수로 사용한다.
                m=metrics(result)
                row['internal_steps']=result['computational_work']['internal_steps']
                if m is None:
                    row.update(status='초기 충수 조건 미달' if result['failure_time']<=t[0] else result.get('failure_kind','수면 한계'),
                        reason=result.get('failure_detail','수면 한계'),failure_time_s=float(result['failure_time']),
                        completion_pct=100*(result['failure_time']-t[0])/(t[-1]-t[0]))
                else:
                    peak=m['peak_reduction_vs_bare_pct'];score=m['rms_reduction_vs_bare_pct']
                    row.update(peak_displacement_m=m['peak_displacement_m'][2],rms_displacement_m=m['rms_displacement_m'][2],peak_acceleration_m_s2=m['peak_absolute_acceleration_m_s2'][2],rms_acceleration_m_s2=m['rms_absolute_acceleration_m_s2'][2],peak_acceleration_reduction_pct=m['acceleration_reduction_vs_bare_pct'],peak_water_m=m['peak_water_displacement_m'],completion_pct=100.,rms_pct=score,peak_pct=peak,status='기준 응답 0' if score is None else '최대 변위 악화' if peak is not None and peak<0 else '정상')
            except ValueError as error:
                row.update(status='계산 오류' if '수렴' in str(error) else '잘못된 설계',reason=str(error))
            except (np.linalg.LinAlgError,FloatingPointError) as error:
                row.update(status='계산 오류',reason=str(error))
            if cache is not None:cache[key]=dict(row)
        # 성능값 표시와 최적 선정은 별개이다. 최대 변위가 악화되어도 RMS 값은 지도에 남긴다.
        row['eligible']=air_mode!='off' and row['rms_pct'] is not None and row['peak_pct'] is not None and (not require_peak or row['peak_pct']>=-1e-8)
        rows.append(row);report()
    return sorted(rows,key=lambda r:(r['eligible'],r['rms_pct'] if r['rms_pct'] is not None else -np.inf),reverse=True)

def quick_verify_best(b,d,t,ag,rows,air_mode='stop',stop=None,memo=None):
    """선정 가능 1위 한 개만 내부 간격 1/2로 확인한다. 추가 예산 1초, 원래 점수는 보존.
    두 간격 비교는 오차 민감도 확인이며 수렴을 증명하거나 순위를 재선정하지 않는다.
    시간 제한은 출력 표본 경계에서 검사하므로 한 계산 구간의 비용만큼 초과할 수 있다.
    """
    for row in rows:
        row.update(check_status='미대상',check_rms_delta_pp=None,check_peak_delta_pp=None)
    best=next((row for row in rows if row['eligible']),None)
    if best is None:return
    key=tuple(best[k] for k in ('beta','angle','B','r','n','amplitude_g','tilt','columns'))
    if memo is not None and key in memo:
        best.update(memo[key]);return
    deadline=perf_counter()+1.
    try:
        if stop is not None and stop.is_set():raise TimeoutError('중지 요청')
        model,trial=search_trial(b,design_variant(d,best['tilt'],best['columns']),best['B'],best['r'],best['n'])
        trial=replace(trial,beta=best['beta'],angle=best['angle'])
        result=simulate_space(model,trial,t,ag,air_mode=air_mode,_step_scale=.5,_deadline=deadline,_cancel=stop)
        if perf_counter()>=deadline:raise TimeoutError('추가 확인 시간 제한')
        measure=metrics(result)
        if measure is None:
            best['check_status']='간격 1/2에서 수면 한계: '+result.get('failure_detail','')
        elif measure['rms_reduction_vs_bare_pct'] is None:
            best['check_status']='기준 응답 0: 비교 불가'
        else:
            best.update(check_status='간격 1/2 비교 완료',
                check_rms_delta_pp=measure['rms_reduction_vs_bare_pct']-best['rms_pct'],
                check_peak_delta_pp=measure['peak_reduction_vs_bare_pct']-best['peak_pct'])
    except TimeoutError as error:best['check_status']=str(error)+' · 확인 미완료'
    except (ValueError,np.linalg.LinAlgError,FloatingPointError) as error:best['check_status']='확인 오류: '+str(error)
    if memo is not None and '미완료' not in best['check_status']:
        memo[key]={k:best[k] for k in ('check_status','check_rms_delta_pp','check_peak_delta_pp')}


# 표시할 행만 선택하는 함수. 시뮬레이션이나 보간을 수행하지 않는다.
# 투영도는 각 칸의 최고 RMS 실제 행을 선택한다. 최대 변위 조건의 선정 가능 여부는 별도이다.
def select_performance_rows(rows,xkey,ykey,fixed,projection=False):
    """지도 선택만 수행한다. 값의 보간이나 재계산 없이 실제 행을 반환한다."""
    if not rows:return [],dict(fixed)
    others=[key for key in ('r','beta','angle','B','n','amplitude_g','tilt','columns') if key in fixed and key not in (xkey,ykey)]
    if projection:
        grouped={}
        for row in rows:
            point=(row[xkey],row[ykey])
            previous=grouped.get(point)
            score=row['rms_pct']
            if previous is None or (score is not None and (previous['rms_pct'] is None or score>previous['rms_pct'])):
                grouped[point]=row
        return list(grouped.values()),dict(fixed)
    selected=list(rows);snapped=dict(fixed)
    # 단계마다 실제 남아 있는 조합에서 선택하여 드문/중단 격자에서도 존재하는 단면을 보장한다.
    for key in others:
        available=sorted(set(float(row[key]) for row in selected if row[key] is not None))
        if not available:continue
        target=float(fixed[key])
        nearest=min(available,key=lambda value:abs(value-target))
        snapped[key]=nearest
        selected=[row for row in selected if row[key] is not None and np.isclose(float(row[key]),nearest,rtol=1e-9,atol=1e-12)]
    return selected,snapped


def building_summary(b,r):
    mass,kx,heights,_=b.floor_data()
    D=np.eye(len(mass))-np.eye(len(mass),k=-1)
    ky=np.array(b.stories_y) if b.stories_y else kx
    return dict(total_mass=float(sum(mass)),width=b.width,depth=b.depth,
        fx=float(modes(np.diag(mass),D.T@(kx[:,None]*D))[0][0]/(2*np.pi)),
        fy=float(modes(np.diag(mass),D.T@(ky[:,None]*D))[0][0]/(2*np.pi)),
        peak_m=float(np.nanmax(abs(r['state'][:,0]))),
        rms_m=float(rms(r['state'][:,0],r['t'])) if r['valid'] else None)


SHAPES=('U형','피자 거치대','V형','다기둥형')
# 화면에서는 V형을 따로 고르지 않고 U형의 '기둥 기울기'로 다룬다. 내부 계산은 기울기<90°일 때 V형 연결망을 그대로 쓴다.
GUI_SHAPES=tuple(x for x in SHAPES if x!='V형')
# 화면 표시 이름 ↔ 내부 이름. 저장 파일과 계산은 내부 이름을 그대로 쓴다.
SHAPE_DISPLAY={'U형':'U형 (기둥 2개)','다기둥형':'일렬형 (기둥 여러 개)','피자 거치대':'방사형 (피자 거치대)'}
SHAPE_INTERNAL={v:k for k,v in SHAPE_DISPLAY.items()}


def internal_shape(shape, tilt, bores=(), tops=()):
    """화면 형상 + 기울기 → 내부 형상. U형이고 기울기가 90° 미만이면 V형 연결망."""
    if shape == 'U형' and not math.isclose(tilt, 90., abs_tol=1e-12):
        if bores or tops:
            raise ValueError('기둥별 안지름·높이를 지정한 U형에는 기울기를 함께 쓸 수 없습니다. 기울기를 90°로 두거나 기둥 설정을 비우세요.')
        return 'V형'
    return shape


def shape_label(d):
    """결과 표시용 이름. 내부 V형은 'U형 (기울기 θ°)'로 보인다."""
    side = '안쪽' if d.tilt > 90 else '바깥쪽'
    if d.shape == 'V형' and is_tilted(d):
        return f'U형 (기둥 기울기 {d.tilt:g}°, {side})'
    if d.shape == '다기둥형':
        return f'일렬형 {d.columns}기둥' + (f' (양 끝 기울기 {d.tilt:g}°, {side})' if is_tilted(d) else '')
    if d.shape == '피자 거치대':
        return f'방사형(피자) {d.columns}기둥' + (f' (기울기 {d.tilt:g}°, {side})' if is_tilted(d) else '')
    if d.separate_u and d.shape == 'U형' and d.bores:
        return 'U형 (기둥별 안지름 지정)'
    return d.shape

# 비대칭 U관의 단면적·정지 수면·관 끝 높이.
# 관 끝 높이는 넘침 여유에만 사용한다. 물의 양은 물 질량 입력이 정하며 정지 시 같은 U관의 좌우 수면은 수평이다.
def u_dimensions(d):
    # 같은 물 질량으로 비교한다. 바닥 관 길이 합은 B, 수직 부분 물 부피 합은 2Ah.
    spans=d.B*np.ones(1)
    count=2*len(spans)
    bores=np.array([d.diameter if x is None else x for x in d.bores] if d.bores else [d.diameter]*count,float)
    if len(bores)!=count or not np.isfinite(bores).all() or min(bores)<=0:
        raise ValueError(f'기둥 안지름은 양수 {count}개가 필요합니다.')
    areas=np.pi*bores**2/4
    # 각 독립 U관에 수직부 물 부피를 균등 배분. 연결된 좌우 수면은 정지 시 같은 높이.
    rest=np.repeat(2*d.h*d.area/len(spans)/areas.reshape(-1,2).sum(axis=1),2)
    if d.tops and len(d.tops)!=count:raise ValueError('기둥 높이 개수를 확인하세요.')
    default_tops=np.full(count,d.leg_length) if d.leg_length is not None else rest+d.freeboard
    tops=np.array([default_tops[i] if x is None else x for i,x in enumerate(d.tops)]) if d.tops else default_tops
    if len(tops)!=count or not np.isfinite(tops).all() or np.any(tops<=rest):
        raise ValueError('각 기둥 끝은 정지 수면보다 높아야 합니다. 높이를 늘리거나 물을 줄이세요.')
    return spans,bores,areas,rest,tops

# 비대칭 U관(기둥별 안지름·높이 지정). 물길 하나·기둥 둘이며 기둥 단면이 다를 수 있다.
# 건물 자유도를 공유하므로 건물에 전달하는 힘을 통해 간접적으로 상호작용한다.
def independent_network(d):
    spans,bores,areas,rest,tops=u_dimensions(d)
    count=len(spans)
    centers=np.zeros(count)
    base_z=np.zeros(count)
    starts=np.column_stack([centers-spans/2,np.zeros(count),base_z])
    ends=starts.copy();ends[:,0]+=spans
    feet=np.stack([starts,ends],axis=1).reshape(-1,3)
    up=np.tile([0.,0.,1.],(2*count,1))
    # 각 자유도는 별도 U관의 바닥 물 이동거리. 좌우 체적 변화는 정확히 상쇄된다.
    S=np.repeat(np.eye(count),2,axis=0)*(np.tile([-1,1],count)*d.area/areas)[:,None]
    inertia=d.rho*(np.diag(d.area*spans)+S.T@((areas*rest)[:,None]*S))
    spring=d.rho*G*S.T@(areas[:,None]*S)
    coupling=d.rho*d.area*(ends-starts)[:,:2].T
    return feet,up,rest,starts,ends,S,np.eye(count),inertia,spring,coupling


# 관 형상 → feet/up/leg/starts/ends, S/T, 유체 M/K, 건물 결합항.
# S@유체좌표는 각 기둥의 수면 변화, T@유체속도는 각 바닥 유로의 평균 유속. 각 연결망의 체적 보존을 만족한다.
def initially_full(d):
    """정지 상태에서 모든 기둥의 수면이 수평관 천장(중심선 위 D/2)보다 높은가. 모든 형상 공통 기준."""
    feet, up, leg, *_ = network(d)
    legs = np.broadcast_to(np.asarray(leg, float), up.shape[0])
    return bool(np.all(legs*up[:, 2] > d.diameter/2))


def slug_supported(d):
    """물기둥 미끄럼 근사를 유도한 형상: 물길 하나·기둥 둘 (U형, 바깥/안쪽 기울인 U형, 비대칭 U형, 기둥 2개 일렬형)."""
    if d.separate_u: return d.shape == 'U형'
    return equivalent_u(d) or d.shape == 'V형' or (d.shape == '다기둥형' and d.columns == 2)


def device_extent(d):
    """관 장치가 차지하는 가로(관 축 X)·세로(Y)·높이(Z) [m]. 관 바깥지름 대신 안지름을 쓴다(관 두께 미포함).
    기둥 끝은 '각 기둥 관 길이' 입력값, 없으면 정지 수면 + 여유 높이(freeboard)까지로 본다.
    기울인 기둥은 바깥(또는 안쪽)으로 나간 만큼 가로에 포함된다. 높이는 수평관 바닥부터 기둥 끝까지."""
    feet, up, leg, starts, ends, *_ = network(d)
    n = up.shape[0]
    legs = np.broadcast_to(np.asarray(leg, float), n)
    if d.separate_u:
        dims = u_dimensions(d); axis_top = np.asarray(dims[4], float); radii = np.asarray(dims[1], float)/2
    else:
        axis_top = np.full(n, d.leg_length) if d.leg_length is not None else legs+d.freeboard/up[:, 2]
        radii = np.full(n, d.diameter/2)
    tops = feet+up*axis_top[:, None]
    pipe = np.vstack([starts, ends]); rp = d.diameter/2
    lo = np.minimum.reduce([pipe.min(0)-rp, (feet-radii[:, None]).min(0), (tops-radii[:, None]).min(0)])
    hi = np.maximum.reduce([pipe.max(0)+rp, (feet+radii[:, None]).max(0), (tops+radii[:, None]).max(0)])
    lo[2] = min(pipe[:, 2].min(), feet[:, 2].min())-rp
    hi[2] = tops[:, 2].max()
    width, depth, height = hi-lo
    return float(width), float(depth), float(height)


def extent_text(d):
    """요약 창에 붙일 장치 크기 문자열."""
    try:
        w, dpt, h = device_extent(d)
        return f'\n장치 크기 가로 {100*w:.1f} · 세로 {100*dpt:.1f} · 높이 {100*h:.1f} cm'
    except (ValueError, ZeroDivisionError, np.linalg.LinAlgError):
        return ''


def network(d):
    """각 가지의 물속 길이와 방향. 분기점에서 들어온 부피와 나간 부피가 같다."""
    if d.separate_u:return independent_network(d)
    n=column_count(d)
    # 마지막 기둥의 수면을 나머지 기둥의 반대로 정해 같은 단면에서 총 물 체적을 보존한다.
    surface=np.vstack([np.eye(n-1),-np.ones(n-1)])
    # 세 바닥 가지의 중심선 길이 합을 B로 나눈다. 방위는 120도 간격이다.
    if d.shape=='피자 거치대':
        az=np.arange(n)*2*np.pi/n  # 방사형: 가운데에서 n개 가지가 같은 간격으로 퍼진다
        feet=d.B/n*np.column_stack((np.cos(az),np.sin(az),np.zeros(n)))
        starts=np.zeros_like(feet); ends=feet.copy(); paths=surface
    else:
        feet=np.column_stack((np.linspace(-d.B/2,d.B/2,n),np.zeros((n,2))))
        # 일렬 연결관에서는 누적 체적 이동으로 각 바닥 구간의 유속을 결정한다.
        starts=feet[:-1];ends=feet[1:];paths=-np.cumsum(surface,axis=0)[:-1]
    up=np.tile([0.,0.,1.],(n,1))
    if is_tilted(d):
        tilt=np.radians(d.tilt)   # 90° 미만은 바깥쪽, 90° 초과는 안쪽(가운데 쪽)으로 눕는다
        if d.shape=='피자 거치대':
            outward=feet[:,:2]/np.linalg.norm(feet[:,:2],axis=1)[:,None]
            up[:,:2]=np.cos(tilt)*outward;up[:,2]=np.sin(tilt)
        else:
            # 일렬형(U·V 포함): 양 끝 기둥만 바깥(안쪽)으로 기울이고 가운데 기둥은 수직.
            up[0]=[-np.cos(tilt),0.,np.sin(tilt)];up[-1]=[np.cos(tilt),0.,np.sin(tilt)]
    # 기둥 물 길이(관 축 방향). 정지 상태에서 모든 수면 높이가 같고 물 총량이 2Ah이다.
    if np.allclose(up[:,2],up[0,2],rtol=0,atol=0):
        leg=2*d.h/n
    else:
        rest=2*d.h/np.sum(1/up[:,2])
        leg=rest/up[:,2]
    delta=ends-starts
    length=np.linalg.norm(delta,axis=1)
    rhoA=d.rho*d.area
    # 관 길이별 유체 운동에너지에서 유체 질량행렬을 만든다.
    if np.ndim(leg)==0:
        inertia=rhoA*(leg*surface.T@surface+paths.T@(length[:,None]*paths))
    else:
        inertia=rhoA*(surface.T@(leg[:,None]*surface)+paths.T@(length[:,None]*paths))
    # 수면 높이 차의 중력 위치에너지에서 복원 강성을 만든다. V형의 수직 성분도 반영한다.
    spring=rhoA*G*surface.T@(up[:,2,None]*surface)
    if np.ndim(leg)==0:
        coupling=rhoA*(delta[:,:2].T@paths+leg*up[:,:2].T@surface)
    else:
        coupling=rhoA*(delta[:,:2].T@paths+up[:,:2].T@(leg[:,None]*surface))
    return feet,up,leg,starts,ends,surface,paths,inertia,spring,coupling



# 실제 연성 적분기. 좌표와 결과 배열의 열 순서를 아래 주석과 함께 확인한다.
# 여기서의 모델 적용 경계는 모든 현실 유체 현상의 계산을 대체하지 않는다.
def network_response(b,d,t,ag,installed=True,baseline_cache=None,air_check=True,air_mode=None,_step_scale=1.,_deadline=None,_cancel=None):
    """수평 두 축의 다층 건물과 연결된 물기둥들의 결합 운동을 적분한다.

    air_mode: 'stop'  수면이 수평관 천장에 닿으면 계산 중단(기본, 보수적)
              'slug'  물기둥 미끄럼 근사(U형·V형·비대칭 U형). 한쪽 기둥이 비면 물기둥 끝이
                      수평관 안으로 들어간다고 보고, 빈 기둥의 복원력 제거·수평 물 길이 감소·
                      기둥과 수평관 단면 차이에 따른 질량 변화를 라그랑주 방정식에서 유도해 보정력으로 넣는다.
                      맞춤 계수 없음.
    정밀(stop) 기준은 모든 형상 공통: 어느 기둥이든 수면이 수평관 천장 높이(중심선 위 D/2)에 닿으면 중단.
              'off'   판정 없이 선형 연속 물기둥 그대로(참고 계산)
    air_mode가 없으면 air_check=True → 'stop', False → 'off'."""
    # network()가 선택한 형상을 수면 변환 S, 유속 변환 T 및 유체 행렬로 바꾸어 반환하는 지점.
    feet,up,leg,starts,ends,S,T,fluid_mass,fluid_k,coupling=network(d)
    modes=S.shape[1]
    # Building의 층별 값이다. mount는 화면과 같은 1부터 시작하며 배열 접근 때만 1을 뺀다.
    masses,stiffness,story_height,mount=b.floor_data()
    # q 구간: [장치 X(n), 장치 Y(n), 맨건물 X(n), 고정질량 X(n), 맨건물 Y(n), 고정질량 Y(n), 유체].
    # 비교용 건물 좌표는 장치 유체와 결합하지 않으며 별도로 끝까지 적분한다.
    n=len(masses); fluid=6*n; size=fluid+modes
    # 관과 물의 질량은 장치 설치 층의 구조 질량 대각항에 추가된다.
    added=d.mass+b.container_mass if installed else 0.
    # M 질량[kg], K 강성[N/m], C 점성감쇠[N·s/m]. 유체와 비교 건물을 함께 보관할 배열이다.
    M=np.eye(size);K=np.zeros_like(M);C=K.copy()
    # difference@u = [u1, u2-u1, ...]. 각 층간 스프링 힘을 양쪽 층에 조립한다.
    difference=np.eye(n)-np.eye(n,k=-1)
    # 각 층의 스프링을 전단 건물 강성행렬로 조립한다. X 입력 k_i가 들어오는 지점이다.
    story=difference.T@(stiffness[:,None]*difference)
    omega=float(np.sqrt(np.linalg.eigvalsh(story/np.sqrt(masses[:,None]*masses[None,:]))[0]))
    for j,extra in ((0,added),(n,added),(2*n,0),(3*n,added)):
        M[j:j+n,j:j+n]=np.diag(masses)
        M[j+mount-1,j+mount-1]+=extra
        K[j:j+n,j:j+n]=story
        C[j:j+n,j:j+n]=2*b.damping/omega*story
    # Y 강성 목록이 있으면 독립적으로 사용한다. 없을 때만 X와 같은 강성을 가정한다.
    ky=np.array(b.stories_y) if b.stories_y else stiffness
    story_y=difference.T@(ky[:,None]*difference)
    # 세계 좌표의 건물 강성을 입력 지진의 진행 방향 좌표로 회전하기 위한 각도.
    theta=np.radians(b.bearing);co,si=np.cos(theta),np.sin(theta)
    xx=co*co*story+si*si*story_y
    yy=si*si*story+co*co*story_y
    # X·Y 강성이 다르면 가진 좌표에서 비대각 결합항이 생긴다. 비틀림 자유도를 추가한 항은 아니다.
    xy=co*si*(story_y-story)
    for ix,iy,extra in ((0,n,added),(2*n,4*n,0),(3*n,5*n,added)):
        M[iy:iy+n,iy:iy+n]=np.diag(masses)
        M[iy+mount-1,iy+mount-1]+=extra
        K[ix:ix+n,ix:ix+n]=xx;K[iy:iy+n,iy:iy+n]=yy
        K[ix:ix+n,iy:iy+n]=xy;K[iy:iy+n,ix:ix+n]=xy
    # 감쇠는 구조물 자유도에만 둔다. 유체의 비선형 오리피스 저항은 뒤에서 별도로 처리한다.
    cx,cy=structural_damping(b)
    cxx=co*co*cx+si*si*cy;cyy=si*si*cx+co*co*cy;cxy=co*si*(cy-cx)
    for ix,iy in ((0,n),(2*n,4*n),(3*n,5*n)):
        C[ix:ix+n,ix:ix+n]=cxx;C[iy:iy+n,iy:iy+n]=cyy
        C[ix:ix+n,iy:iy+n]=cxy;C[iy:iy+n,ix:ix+n]=cxy
    a=np.radians(d.angle+180*d.reverse)
    rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
    # 관 설치 상대각이 건물-유체 질량 결합에 반영된다. 관 없음이면 결합항이 0이다.
    cross=rot@coupling if installed else np.zeros_like(coupling)
    # 선택한 설치 층의 X·Y 자유도 두 개에 유체를 연결한다. 다른 층에 직접 연결하지 않는다.
    attached=[mount-1,n+mount-1]
    # 구조→유체와 유체→구조 항을 서로 전치로 넣어 질량행렬의 대칭성을 유지한다.
    M[attached,fluid:]=cross;M[fluid:,attached]=cross.T
    M[fluid:,fluid:]=fluid_mass;K[fluid:,fluid:]=fluid_k
    # 좌표는 지반 상대변위. 가진 하중은 -M@[1(X건물),0(Y건물),...,0(유체)]*ag.
    # M의 결합항 때문에 유체 행에도 올바른 지반 관성력이 생긴다.
    excitation=np.ones(size);excitation[n:2*n]=0;excitation[4*n:6*n]=0;excitation[fluid:]=0
    # 실제 지반 관성하중은 뒤의 force*gm에서 -load*ag가 된다.
    load=M@excitation
    # 실제 연성 부분만 중점법으로 풀고 비교 건물은 별도 계산하여 반복 행렬 크기를 줄인다.
    active=np.r_[np.arange(2*n),np.arange(fluid,size)]
    Ma=M[np.ix_(active,active)];Ka=K[np.ix_(active,active)];Ca=C[np.ix_(active,active)]
    la=load[active]
    full_mid=np.zeros(size)
    # 각 바닥 유로 평균속도에 동일한 개구비 경험식을 적용한다. 분기관 실측 보정은 미포함.
    # 개구비 beta가 만든 xi를 사용한다. T가 반환한 각 유로 평균 유속에 같은 오리피스 기준을 적용한다.
    weights=np.full(len(starts),.5*d.rho*d.area*d.loss)
    flow_eye=np.eye(len(starts))
    # 정지 수면에서 관 끝까지의 상승 여유. 비대칭 관은 기둥마다 값이 다를 수 있다.
    clearance=u_dimensions(d)[4]-leg if d.separate_u else d.leg_length-leg if d.leg_length is not None else (d.freeboard/up[0,2] if np.ndim(leg)==0 else d.freeboard/up[:,2])
    # 일반 원형 U관의 보수적인 전단면 충수 적용 경계.
    # 수평 관 중심선 z=0, 내측 천장 z=D/2. 접합부/자유수면의 3차원 형상은 미해석.
    # 이는 공기 유입을 확정하는 실험식이 아니라 고전 물기둥 모델의 적용 제한이다.
    standard_u=installed and equivalent_u(d)
    mode=air_mode or ('stop' if air_check else 'off')
    if mode not in ('stop','slug','off'):raise ValueError('air_mode는 stop, slug, off 중 하나입니다.')
    if mode=='slug' and not (installed and modes==1 and S.shape[0]==2 and slug_supported(d)):mode='stop'   # 유도한 형상만 근사
    # 수면 변화량(관 축 방향)의 하한. 기준이 정지 수면이므로 아래 방향은 음수이다.
    # 모든 형상 공통: 수면 높이가 수평관 천장(중심선 위 D/2)에 닿는 지점. 기울어진 관은 축 길이로 환산한다.
    legs=np.broadcast_to(np.asarray(leg,float),S.shape[0]).copy()
    stop_lower=-legs+(d.diameter/2)/up[:,2]
    lower_rise=stop_lower.copy()
    slug=mode=='slug'
    if slug:
        # 기둥 단면 A_j, 수평관 단면 A_h. 빠져나간 기둥 길이 over_j가 수평관에 A_j/A_h배 길이로 들어간다.
        column_area=u_dimensions(d)[2] if d.separate_u else np.full(2,d.area)
        A_h=d.area;s_up=up[:,2].astype(float);sl=S[:,0].astype(float)
        vol_ratio=column_area/A_h
        gravity_coef=d.rho*G*column_area*s_up                      # 기둥별 ρgA_j sinθ_j
        mass_coef=d.rho*(A_h**2-column_area**2)/column_area         # 수평관 유입에 따른 유체 질량 변화율
        # 물기둥 뒤끝이 수평관 가운데(오리피스)에 닿으면 근사 범위를 벗어난다.
        lower_rise=-legs-(d.B/2)/vol_ratio
        # 건물-유체 결합 중 수평관 물 몫만 줄어든다. V형 경사관 몫은 그대로 둔다.
        horizontal_coupling=d.rho*d.area*((ends-starts)[:,:2].T@T)
        cross_h=(rot@horizontal_coupling)[:,0] if installed else np.zeros(2)
        fpos=2*n
        exc_att=excitation[attached].astype(float)
        attach0,attach1=attached
        a_prev=np.zeros(len(active));gm_prev=0.
        def slug_terms(yf):
            over=np.maximum(-(legs+sl*yf),0.)
            if not over.any():return None
            on=over>0
            e=float(vol_ratio@over);de=-float((vol_ratio*sl)@on)
            dm=float(mass_coef@over);dmd=-float((mass_coef*sl)@on)
            grav=-float(sl@(gravity_coef*over))
            return e,de,dm,dmd,grav
    q=np.zeros(size);v=np.zeros(size)
    # 시간별 좌표 Q와 속도 V. 계산하지 못한 구간은 NaN으로 남겨 정상 결과와 구분한다.
    Q=np.full((len(t),size),np.nan);V=Q.copy();Q[0]=q;V[0]=v
    try:
        chol=np.linalg.cholesky(Ma)
    except np.linalg.LinAlgError as error:
        raise ValueError('유체-구조 결합 질량행렬이 양의 정부호가 아닙니다. 형상과 질량을 확인하세요.') from error
    transformed=np.linalg.solve(chol,Ka)
    transformed=np.linalg.solve(chol,transformed.T).T
    fmax=np.sqrt(np.linalg.eigvalsh(transformed).max())
    # 유체-구조 연성계의 가장 빠른 진동을 충분히 나누는 내부 간격. 입력 기록의 표본 간격과 다르다.
    stepmax=min(.01,2*np.pi/(INTERNAL_POINTS_PER_PERIOD*fmax))*_step_scale
    internal_steps=0
    nvalid=1;failure=None;failure_kind=None;failure_detail="";last_h=None
    original_t=t;original_ag=ag
    import hashlib
    excitation_key=hashlib.sha256(original_t.tobytes()+original_ag.tobytes()).digest()
    t=t.copy();ag=ag.copy()
    # 정밀·근사 모두 시작할 때 관이 물로 꽉 차 있어야 한다(모든 형상 공통). 정지 수면이 수평관 천장 이하면 계산하지 않는다.
    if installed and mode in ('stop','slug') and np.any(stop_lower>=0):
        failure=float(t[0]);failure_kind='모델 적용 범위 초과'
        failure_detail=(f'초기 상태 · 정지 수면 높이 {float(np.min(legs*up[:,2]))*1000:.3f} mm ≤ 수평관 천장 D/2={d.diameter*500:.3f} mm. '
            '시작부터 수평관에 공기가 있어 물기둥 모델을 적용할 수 없음(초기 충수 조건 미달).')

    # 단일 유로 물 모델에서는 중점법의 선형 부분을 한 번의 행렬곱으로 묶는다.
    fast_water=installed and modes==1 and len(weights)==1 and not slug
    if fast_water:
        dimension=len(active)
        packed=np.zeros(2*dimension)
        slopes=S[:,0]
        upper=np.broadcast_to(clearance,slopes.shape)
        lower_y=-np.inf
        upper_y=np.inf
        for slope,low,high in zip(slopes,lower_rise,upper):
            if slope:
                left,right=sorted((low/slope,high/slope))
                lower_y=max(lower_y,left)
                upper_y=min(upper_y,right)
        if mode=='off':lower_y,upper_y=-np.inf,np.inf
    def check_budget():
        if _cancel is not None and _cancel.is_set():raise TimeoutError('중지 요청')
        if _deadline is not None and perf_counter()>=_deadline:raise TimeoutError('추가 확인 시간 제한')
    check_budget()
    previous_flow=[None,None]
    def solve_mid(free):
        # 오리피스·명시한 추가 손실을 포함해 중점 속도 full_mid를 구한다.
        if scalar_flow:
            rhs=scalar_path*float(free[-1])
            velocity=2*rhs/(1+math.sqrt(1+4*scalar_coefficient*abs(rhs)))
            full_mid[active]=free-scalar_drag*(abs(velocity)*velocity)
        else:
            rhs=T@free[-modes:]
            flow=rhs.copy() if previous_flow[0] is None else previous_flow[0]+rhs-previous_flow[1]
            tolerance=1e-11*(1+max(abs(rhs)))
            for _ in range(20):
                # 여러 유로는 유속과 저항의 연성 방정식을 Newton 반복으로 푼다. 수렴 실패는 오류로 보고한다.
                residual=flow+transfer@(weights*abs(flow)*flow)-rhs
                if max(abs(residual))<tolerance:break
                flow-=np.linalg.solve(flow_eye+transfer*(2*weights*abs(flow)),residual)
            else:
                # 예측 초기값이 불리하면 기존 초기값과 반복 횟수로 다시 푼다.
                flow=rhs.copy()
                for _ in range(20):
                    residual=flow+transfer@(weights*abs(flow)*flow)-rhs
                    if max(abs(residual))<tolerance:break
                    flow-=np.linalg.solve(flow_eye+transfer*(2*weights*abs(flow)),residual)
                else:raise ValueError('유체 저항 계산이 수렴하지 않았습니다. 입력 조건을 확인하세요.')
            previous_flow[:]=[flow.copy(),rhs.copy()]
            full_mid[active]=free-drag@(T.T@(weights*abs(flow)*flow))
    # 출력 기록의 각 구간을 내부 안정 간격으로 다시 나누고 ag는 선형 보간한다.
    for i,span in enumerate(np.diff(t),1):
        check_budget()
        if failure is not None:break
        count=max(1,int(np.ceil(span/stepmax-1e-10)));dt=span/count;h=dt/2
        if last_h is None or abs(last_h-h)>1e-13:
            inv=np.linalg.inv(Ma+h*Ca+h*h*Ka)
            vm=inv@Ma;qm=-h*inv@Ka;force=-h*inv@la;drag=h*inv[:,-modes:]
            # 1~3개의 가지 유속만을 미지수로 두는 중점법의 비선형 저항 방정식
            transfer=T@drag[-modes:]@T.T
            scalar_flow=len(weights)==1
            # 유로가 하나인 경우 저항 방정식의 안정적인 닫힌 해를 사용해 반복 계산을 줄인다.
            if scalar_flow:
                scalar_coefficient=float(transfer[0,0]*weights[0])
                scalar_drag=drag[:,0]*float(T[0,0])*weights[0]
                scalar_path=float(T[0,0])
            last_h=h
            if slug:
                hinv=h*inv
                slug_fluid_correction=hinv[:,-1]
                slug_building_correction=(hinv[:,attach0]*cross_h[0]+hinv[:,attach1]*cross_h[1])/d.B
            if fast_water:
                eye=np.eye(dimension)
                transition=np.block([[eye+dt*qm,dt*vm],[2*qm,2*vm-eye]])
                ground_step=np.r_[dt*force,2*force]
                drag_step=np.r_[dt*scalar_drag,2*scalar_drag]
                flow_row=scalar_path*np.r_[qm[-1],vm[-1]]
                flow_ground=scalar_path*force[-1]
        if fast_water:
            initial=packed
            for j in range(count):
                gm=ag[i-1]+(ag[i]-ag[i-1])*(j+.5)/count
                rhs=flow_row@packed+flow_ground*gm
                velocity=2*rhs/(1+math.sqrt(1+4*scalar_coefficient*abs(rhs)))
                packed=transition@packed+ground_step*gm-drag_step*(abs(velocity)*velocity)
                if not lower_y<packed[dimension-1]<upper_y:
                    # 경계가 걸린 표본 구간만 기존 사건 보간 루틴으로 다시 계산한다.
                    packed=initial
                    break
            else:
                internal_steps+=count
                q[active]=packed[:dimension]
                v[active]=packed[dimension:]
                Q[i]=q
                V[i]=v
                nvalid+=1
                continue
        for j in range(count):
            internal_steps+=1
            # 입력 기록 두 표본 사이의 중간 시각 가속도. 단위는 m/s²이다.
            gm=ag[i-1]+(ag[i]-ag[i-1])*(j+.5)/count
            # 비선형 오리피스 저항을 적용하기 전의 중점 속도 예측값.
            free0=vm@v[active]+qm@q[active]+force*gm
            if slug:
                # 기둥 둘/유체 자유도 하나. 선형 모형과의 차이를 보정력으로 더한다.
                # 유체: 중력 복원력 제거, 수평관 결합 감소(e/B), 질량 변화 Δm(q)의 Δm·q̈+½Δm'·q̇².
                # 건물: 결합 감소분의 q̈ 반력과 결합 변화율에 따른 q̇² 항.
                # 암시적 중점법: 보정력을 같은 단계의 중점 상태(위치 q+h·v중점, 속도 v중점, 가속도 (v다음-v)/dt)로
                # 평가하도록 고정점 반복한다. 직전 단계 값을 쓰면 감쇠가 없는 긴 계산에서 에너지 오차가 쌓인다.
                qf0=float(q[fluid]);est_q=qf0;est_v=float(v[fluid]);est_acc=a_prev.copy()
                for _iteration in range(8):
                    terms=slug_terms(est_q)
                    free=free0
                    if terms is not None:
                        e,de,dm,dmd,grav=terms
                        qdd=float(est_acc[-1]);absolute=est_acc[attached]+exc_att*gm
                        extra_fluid=grav+(e/d.B)*float(cross_h@absolute)-dm*qdd-.5*dmd*est_v*est_v
                        extra_building=e*qdd+de*est_v*est_v
                        free=free0+slug_fluid_correction*extra_fluid+slug_building_correction*extra_building
                    solve_mid(free)
                    mid_f=float(full_mid[fluid]);new_q=qf0+h*mid_f
                    if terms is None and slug_terms(new_q) is None:break
                    new_acc=2*(full_mid[active]-v[active])/dt
                    change=abs(new_q-est_q)+h*abs(mid_f-est_v)
                    est_q=new_q;est_v=mid_f;est_acc=new_acc
                    if change<1e-13*(1+abs(qf0)):break
                else:
                    raise ValueError(f'slug 반복 계산 미수렴: {t[i-1]+(j+.5)*dt:.8g}초, 8회 반복. 시간 간격과 수면 상태를 확인하세요.')
            else:
                solve_mid(free0)
            mid=full_mid
            old_q=q;old_v=v
            # 중점 속도로 좌표를 업데이트한 뒤 중점 관계에서 다음 시각 속도를 계산한다.
            q=q+dt*mid;v=2*mid-v
            if slug:a_prev=(v[active]-old_v[active])/dt;gm_prev=gm
            # 유체 일반화 좌표를 화면에서 보는 각 기둥 수면 변화로 바꾼다. 단위는 m이다.
            rise=S@q[fluid:]
            if installed and mode!='off' and np.max(np.maximum(lower_rise-rise,rise-clearance))>=0:
                old_rise=S@old_q[fluid:]
                lower=lower_rise
                upper=np.broadcast_to(np.asarray(clearance),rise.shape)
                candidates=[]
                for column in range(len(rise)):
                    bound=lower[column] if rise[column]<=lower[column] else upper[column]
                    if rise[column]<=lower[column] or rise[column]>=upper[column]:
                        fraction=(bound-old_rise[column])/(rise[column]-old_rise[column])
                        candidates.append((float(np.clip(fraction,0,1)),column,rise[column]<=lower[column]))
                # 한 내부 단계에서 여러 기둥이 경계에 닿으면 가장 먼저 닿은 사건을 선택한다.
                fraction,column,is_lower=min(candidates)
                q=old_q+fraction*(q-old_q);v=old_v+fraction*(v-old_v)
                failure=t[i-1]+(j+fraction)*dt
                failure_kind='모델 적용 범위 초과' if is_lower else '수면 상한 도달'
                failure_detail=f'{column+1}번 기둥 · {failure:.6f}초 (내부 단계 보간) · {failure_kind}'+(
                    (' · 물기둥 끝이 수평관 가운데(오리피스)에 도달. 미끄럼 근사 범위 밖.' if slug else ' · 수면이 수평관 천장 높이에 도달, 공기 유입 가능(모든 형상 공통 기준).') if is_lower else '')
                # 원래 기록의 표본을 지우지 않고 경계 시각을 추가한다.
                # 모든 설계는 동일한 원본 가진의 선형 보간을 받는다.
                if failure<t[i]-1e-12:
                    value=float(np.interp(failure,t,ag))
                    t=np.insert(t,i,failure);ag=np.insert(ag,i,value)
                    Q=np.insert(Q,i,q,axis=0);V=np.insert(V,i,v,axis=0)
                else:
                    Q[i]=q;V[i]=v
                # 마지막 경계 상태까지 유효하게 저장한 표본 수. 전체 구간 저감률 산출 가능 여부와는 별개이다.
                nvalid=i+1
                break
        if failure is not None:break
        if fast_water:packed=np.r_[q[active],v[active]]
        Q[i]=q;V[i]=v;nvalid+=1
    # 이 아래는 TLCD 중단과 무관하게 원래 입력 끝까지 맨건물·고정질량 건물을 계산한다.
    baseline_steps=np.maximum(1,np.ceil(np.diff(original_t)/stepmax-1e-10)).astype(np.int64)
    baseline_blocks=[]
    for indices in (np.r_[np.arange(2*n,3*n),np.arange(4*n,5*n)],
                    np.r_[np.arange(3*n,4*n),np.arange(5*n,6*n)]):
        mb=M[np.ix_(indices,indices)];kb=K[np.ix_(indices,indices)];cb=C[np.ix_(indices,indices)]
        baseline_blocks.append((indices,mb))   # 장치 없음·물 고정 건물의 절대가속도 계산에 필요(원본 누락 수정)
        # 비교 대상도 TLCD와 같은 내부 시간 간격으로 적분한다.
        # 다른 간격의 기준 응답을 재사용하면 저감률에 수치 오차가 섞인다.
        # 질량·강성·감쇠·내부 간격이 같을 때만 비교 건물 결과를 재사용한다.
        cache_key=(mb.tobytes(),kb.tobytes(),cb.tobytes(),baseline_steps.tobytes(),excitation_key)
        stored=baseline_cache.get(cache_key) if baseline_cache is not None else None
        if stored is None:
            influence=np.r_[np.ones(n),np.zeros(n)]
            qb_history=np.zeros((len(original_t),2*n));vb_history=qb_history.copy()
            base_step=stepmax;last_dt=None;last_steps=None
            state_b=np.zeros(4*n)
            for i,span in enumerate(np.diff(original_t),1):
                check_budget()
                steps=max(1,int(np.ceil(span/base_step-1e-10)));dt=span/steps;half=dt/2
                if last_dt is None or abs(dt-last_dt)>1e-13 or steps!=last_steps:
                    invb=np.linalg.inv(mb+half*cb+half*half*kb)
                    bm=invb@mb;bk=-half*invb@kb;bg=-half*bm@influence
                    # 선형 비교 건물: 기존 중점법의 여러 내부 단계를 같은 전이식으로 합성한다.
                    # 두 기록 표본 사이 선형 보간도 동일하다. 적분법/간격을 바꾸지 않는다.
                    identity=np.eye(2*n)
                    transition=np.block([[identity+dt*bk,dt*bm],[2*bk,2*bm-identity]])
                    forcing=np.r_[dt*bg,2*bg]
                    advance=np.eye(4*n);previous=np.zeros(4*n);following=previous.copy()
                    for j in range(steps):
                        fraction=(j+.5)/steps
                        advance=transition@advance
                        previous=transition@previous+forcing*(1-fraction)
                        following=transition@following+forcing*fraction
                    last_dt=dt;last_steps=steps
                state_b=advance@state_b+previous*original_ag[i-1]+following*original_ag[i]
                qb_history[i]=state_b[:2*n];vb_history[i]=state_b[2*n:]
            stored=(qb_history,vb_history)
            if baseline_cache is not None:baseline_cache[cache_key]=stored
        for column,index in enumerate(indices):
            Q[:,index]=np.interp(t,original_t,stored[0][:,column])
            V[:,index]=np.interp(t,original_t,stored[1][:,column])
    # 상대 운동식 M*q'' = -K*q-C*q'-저항-M*r*ag 에 ag를 더하면 절대가속도가 된다.
    # 아래 force에는 -M*r*ag를 넣지 않으므로 solve(M,force)가 곧 절대가속도다.
    force=-np.nan_to_num(Q)@K.T-np.nan_to_num(V)@C.T
    currents=np.nan_to_num(V[:,fluid:])@T.T
    force[:,fluid:]-=(weights*abs(currents)*currents)@T
    acc=np.zeros_like(force)
    acc[:,active]=np.linalg.solve(Ma,force[:,active].T).T
    if slug:
        # 표준 U관의 단일 유체 자유도에 한정한다. 기존 행렬식과 같은 Schur 보완식으로
        # 시각마다 작은 행렬을 복사·역산하던 작업을 일괄 계산한다. 물리식은 변경하지 않는다.
        yq=Q[:nvalid,fluid]
        over=np.maximum(-(legs[None,:]+yq[:,None]*sl[None,:]),0.)
        rows=np.flatnonzero(over.sum(axis=1)>0)
        if len(rows):
            ov=over[rows];on=(ov>0).astype(float);qd=V[rows,fluid]
            e=ov@vol_ratio;de=-(on@(vol_ratio*sl))
            dm=ov@mass_coef;dmd=-(on@(mass_coef*sl))
            f=force[rows][:,active].copy()
            f[:,fpos]+=-(ov*gravity_coef)@sl-.5*dmd*qd*qd
            f[:,attach0]+=cross_h[0]/d.B*de*qd*qd;f[:,attach1]+=cross_h[1]/d.B*de*qd*qd
            # 건물 블록은 대각 질량. 유효 결합 c_eff = c - (e/B)·c_h, 유효 유체 질량 m + Δm 으로 Schur 보완식을 푼다.
            diagonal=np.diag(Ma)[:2*n];coupling=Ma[:2*n,fpos]
            c_eff=np.repeat(coupling[None,:],len(rows),axis=0)
            c_eff[:,attach0]-=e/d.B*cross_h[0];c_eff[:,attach1]-=e/d.B*cross_h[1]
            base=f[:,:2*n]/diagonal
            schur=Ma[fpos,fpos]+dm-np.einsum('ij,ij->i',c_eff,c_eff/diagonal)
            fluid_acc=(f[:,fpos]-np.einsum('ij,ij->i',base,c_eff))/schur
            acc[np.ix_(rows,active[:2*n])]=base-fluid_acc[:,None]*c_eff/diagonal
            acc[rows,fluid]=fluid_acc
    for indices,mb in baseline_blocks:
        acc[:,indices]=np.linalg.solve(mb,force[:,indices].T).T
    # 유체 계산이 끝난 뒤의 장치 건물 가속도는 미계산이므로 NaN 처리한다.
    acc[nvalid:,:2*n]=np.nan
    heights=(Q[:,fluid:]@S.T)*up[:,2]
    speeds=(V[:,fluid:]@S.T)*up[:,2]
    dt=np.diff(t);vg=np.r_[0,np.cumsum(dt*(ag[:-1]+ag[1:])/2)]
    # 가속도를 구간별로 두 번 적분한 지면 변위. 단방향 사인 가진 화면은 done()에서 알려진 해로 표시한다.
    ground=np.r_[0,np.cumsum(dt*vg[:-1]+dt**2*(2*ag[:-1]+ag[1:])/6)]
    floors_x=Q[:,:n];floors_y=Q[:,n:2*n]
    travel=np.nanmax(np.hypot(floors_x[:nvalid],floors_y[:nvalid]))+max(abs(ground[:nvalid]))
    roof=n-1;bare=3*n-1;fixed=4*n-1
    # 결과를 사전으로 반환한다. state/acc의 열 순서는 metrics() 주석을 참조한다.
    # floors_x/floors_y는 모든 층의 상대 변위, levels는 각 물기둥의 정지 수면 대비 변화이다.
    return dict(t=t,ag=ag,ground=ground,first=Q[:,[0,n]],travel=travel,installed=installed,
        integration_max_step_s=stepmax,
        floors_x=floors_x,floors_y=floors_y,floors_acc=acc[:,:n],floor_bare=Q[:,2*n:3*n],
        floor_bare_acc=acc[:,2*n:3*n],story_height=story_height,mount=mount,
        lower_water=lower_rise*up[:,2],upper_water=np.broadcast_to(clearance,len(up))*up[:,2],
        fluid_model='물 / '+{'stop':'연속 물기둥 / 공기 유입 이후 미해석','slug':'물기둥 미끄럼 근사(빈 세로관 복원력 제거·수평 물 길이 감소)','off':'선형 연속 물기둥(판정 끔, 참고 계산)'}[mode],air_mode=mode,
        fluid_properties=dict(density_kg_m3=d.rho),
        computational_work=dict(internal_steps=internal_steps,resistance_solver='오리피스 유속 풀이'),
        fluid_scope='물/오리피스 근사',
        geometry_scope='수평관 천장 기준 보수적 충수 제한; 실제 접합부 공기 유입 시각 미확정' if standard_u else '기존 형상별 물기둥 근사',
        failure_kind=failure_kind,failure_detail=failure_detail,
        floor_bare_y=Q[:,4*n:5*n],
        levels=heights,rest_height=leg*up[0,2] if np.ndim(leg)==0 else leg*up[:,2],
        state=np.column_stack([Q[:,roof],V[:,roof],heights[:,-1],speeds[:,-1],Q[:,bare],V[:,bare],Q[:,fixed],V[:,fixed]]),
        acc=acc[:,[bare,fixed,roof]],lateral=np.column_stack([Q[:,2*n-1],V[:,2*n-1]]),lateral_acc=acc[:,2*n-1],
        valid=failure is None,failure_time=failure,n_valid=nvalid)



# 주 GUI·비교·최적화가 함께 사용하는 진입점. 입력 검증 후 network_response()에 전달한다.
def simulate_space(b, d, t, ag, installed=True,*,_baseline_cache=None,air_check=True,air_mode=None,_step_scale=1.,_deadline=None,_cancel=None):
    """수평 두 방향의 지붕 운동과 두 수면의 연직 운동을 결합한다.

    세계 X·Y 층별 강성을 가진 행렬을 가진 방향 좌표로 회전한다. 관과 나란한 축에서는
    물과 건물이 힘을 주고받고, 직각 축에서는 물도 건물에 실린 질량으로 움직인다.
    축별로 적분한 뒤 지진 방향 X와 횡방향 Y로 다시 회전한다.
    """
    validate(b, d)
    t, ag = np.asarray(t, dtype=float), np.asarray(ag, dtype=float)
    if (t.ndim != 1 or t.shape != ag.shape or len(t) < 2
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(ag))
            or np.any(np.diff(t) <= 0)):
        raise ValueError('시간은 증가해야 하며 각 시간에 가속도 하나가 필요합니다.')
    if not np.isfinite(_step_scale) or not 0<_step_scale<=1:raise ValueError('내부 시간 간격 배율은 0 초과 1 이하입니다.')
    return network_response(b,d,t,ag,installed,_baseline_cache,air_check,air_mode,_step_scale,_deadline,_cancel)


# 현재 3D 실험의 표·그림·요약 저장. 물리 한계와 부분 구간의 평가 범위를 함께 기록한다.
def export_space(folder, b, d, r, title):
    plt = setup_plot()
    if r.get('installed',True):
        fig, axes = plt.subplots(3,2,figsize=(14,10))
        fig.subplots_adjust(hspace=.65,wspace=.25)
        draw_result(fig, list(axes.flat), b,d,r,title)
    else:
        fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
        for series,label in [(r['ground'],'지면'),(r['ground']+r['first'][:,0],'1층'),(r['ground']+r['state'][:,0],'지붕')]:
            ax.plot(r['t'],series*1000,label=label)
        ax.set(title='관 없음 · '+title,xlabel='시간 (초)',ylabel='정지 기준 위치 (mm)')
        ax.legend();ax.grid(axis='y',alpha=.2)
    save_result(folder,b,d,r,fig,title)
    plt.close(fig)
    if 'levels' in r:
        np.savetxt(Path(folder)/'column_heights.csv',np.column_stack((r['t'],r['rest_height']+r['levels'])),
            delimiter=',',comments='',header='time_s,'+','.join(f'column_{j+1}_height_m' for j in range(r['levels'].shape[1])))
    np.savetxt(Path(folder)/'spatial_motion.csv',
               np.column_stack((r['t'],r['ground'],r['first'],r['state'][:,0],r['lateral'][:,0],
                                (np.ravel(r['rest_height'])[0]+r['levels'][:,0] if 'levels' in r else d.h-r['state'][:,2]) if r.get('installed',True) else np.full(len(r['t']),np.nan),
                                (np.ravel(r['rest_height'])[-1]+r['levels'][:,-1] if 'levels' in r else d.h+r['state'][:,2]) if r.get('installed',True) else np.full(len(r['t']),np.nan),
                                r['acc'][:,2],r['lateral_acc'])),
               header='time_s,ground_displacement_m,floor1_relative_X_m,floor1_relative_Y_m,roof_X_m,roof_Y_m,left_water_height_m,right_water_height_m,absolute_ax_m_s2,absolute_ay_m_s2',
               delimiter=',',comments='')


# 지진 기록 모드의 방향과 가상 거리 배율. 사용자가 지정한 위치는 방향과 경험적 크기 조절에 사용한다.
# 실제 지진파 전파·도달 시각·주파수별 감쇠·지반 증폭을 계산하는 진원 모델은 아니다.
@dataclass(frozen=True)
class Source:
    east: float = -6
    north: float = 0
    depth: float = 8
    strength: float = .03

    def input_for(self, waveform, heading):
        """거리·방향 영향을 독립적으로 실험하는 가상 입력. 시간은 도착 후 기준."""
        if not all(math.isfinite(x) for x in asdict(self).values()) or self.depth <= 0 or self.strength < 0:
            raise ValueError('진원 깊이는 양수, 기준 세기는 0 이상이어야 합니다.')
        distance = math.hypot(self.east,self.north,self.depth)
        bearing = math.degrees(math.atan2(-self.north,-self.east)) if self.east or self.north else 0.
        # 10 km에서 입력한 진폭. 근거리 발산을 막도록 1 km 완화 길이를 둔다.
        pga = self.strength*math.sqrt(101)/math.hypot(distance,1)
        peak = np.max(np.abs(waveform))
        if peak == 0 and pga > 0:
            raise ValueError('모든 값이 0인 기록은 세기를 키울 수 없습니다.')
        signal = waveform*(pga*G/peak) if peak else np.zeros_like(waveform)
        return signal, (heading-bearing)%180, dict(**asdict(self),distance_km=distance,
            bearing_deg=bearing,heading_deg=heading,site_pga_g=pga)


def acceleration_table(result,start=None,end=None):
    t=result['t'];start=float(t[0] if start is None else start);end=float(t[-1] if end is None else end)
    if not t[0]<=start<end<=t[-1]:raise ValueError('평가 구간은 입력 시간 안에서 시작 < 끝이어야 합니다.')
    window=np.r_[start,t[(t>start)&(t<end)],end]
    def values(array):
        return np.column_stack([np.interp(window,t,array[:,i]) for i in range(array.shape[1])])
    baseline=values(result['floor_bare_acc'])/G
    active=values(result['floors_acc'])/G
    valid=result['valid'] or (result['failure_time'] is not None and end<=result['failure_time'] and result['n_valid']>=2)
    rows=[]
    for i in range(baseline.shape[1]):
        bp=float(np.max(abs(baseline[:,i])));br=float(rms(baseline[:,i],window))
        ap=float(np.max(abs(active[:,i]))) if valid else None
        ar=float(rms(active[:,i],window)) if valid else None
        rows.append(dict(floor=i+1,start_s=start,end_s=end,
            scope='전체 구간; 과도응답 포함' if start==t[0] and end==t[-1] else '사용자 지정 구간; 정상상태 여부 미확정',
            baseline_peak_g=bp,tlcd_peak_g=ap,baseline_rms_g=br,tlcd_rms_g=ar,
            peak_reduction_pct=reduction(bp,ap) if valid else None,
            rms_reduction_pct=reduction(br,ar) if valid else None,
            status='유효 평가 구간' if valid else '유체 미완료: 전체 성능 산출 불가'))
    return rows

# ── 공정 비교 도구 ─────────────────────────────────────────────────
# 원칙: (1) 같은 건물·물 질량·손실 설정·수면 처리·가진, (2) 모양마다 조율비 r·개구비 β·수평 길이 B를
# 각자 최적화한 뒤 최선끼리 비교, (3) 여러 가진과 건물 진동수 ±10%에서 검증.
# 모양만 바꾸면 TLCD 진동수가 바뀌므로, search_trial()로 모든 후보를 같은 r에 다시 조율하고
# 물 질량은 단면을 함께 조정해 유지한다. 성능 계산은 주 실험실과 같은 simulate_space()를 쓴다.
FAIR_EXCITATIONS = ('공진 사인', '엘센트로 지진', '고베지진', '멕시코시티 지진')


def fair_candidate(d, label, tilt=60., columns=3, bore_ratio=1.4):
    """기준 장치 d에서 모양만 바꾼 후보를 만든다. 물 질량·손실 설정·각도는 그대로 둔다."""
    base = replace(d, bores=(), tops=(), leg_length=None)
    if label == 'U형':
        return replace(base, shape='U형', tilt=90.)
    if label == '기울인 U형':
        if not 0 < tilt < 180 or math.isclose(tilt, 90.): raise ValueError('기둥 기울기는 0°~180° 사이, 90°가 아닌 값입니다(90°는 기준 U형, 90° 초과는 안쪽).')
        return replace(base, shape='V형', tilt=float(tilt))
    if label == '다기둥형':
        if int(columns) != columns or not 3 <= columns <= 24: raise ValueError('일렬형 기둥 수는 3~24의 정수입니다.')
        return replace(base, shape='다기둥형', columns=int(columns), tilt=90.)
    if label == '피자 거치대':
        if int(columns) != columns or not 3 <= columns <= 24: raise ValueError('방사형(피자) 기둥 수는 3~24의 정수입니다.')
        return replace(base, shape=label, columns=int(columns), tilt=90.)
    if label == '비대칭 U형':
        if not bore_ratio > 0 or bore_ratio == 1: raise ValueError('비대칭 지름비는 1이 아닌 양수여야 합니다.')
        return replace(base, shape='U형', tilt=90., bores=(d.diameter*bore_ratio, d.diameter))
    raise ValueError(f'알 수 없는 후보: {label}')


def fair_label(label, tilt=60., columns=3, bore_ratio=1.4):
    return {'기울인 U형': f'U형 기둥 기울기 {tilt:g}°'+(' (안쪽)' if tilt > 90 else ''), '다기둥형': f'일렬형 {columns:g}기둥',
            '피자 거치대': f'방사형(피자) {columns:g}기둥',
            '비대칭 U형': f'비대칭 U형 (지름비 {bore_ratio:g}:1)'}.get(label, label)


def device_height(d):
    """관 축 끝(넘침 한계)까지의 최대 세로 높이[m]. 수평관 중심선 기준."""
    feet, up, leg, *_ = network(d)
    leg = np.broadcast_to(np.asarray(leg, float), up.shape[0])
    if d.separate_u: top = np.broadcast_to(u_dimensions(d)[4], up.shape[0])
    elif d.leg_length is not None: top = np.full(up.shape[0], d.leg_length)
    else: top = leg + d.freeboard/up[:, 2]
    return float(np.max(top*up[:, 2]))


def fair_excitations(b, sine_amplitude_g=.01):
    """비교용 가진 4종. 지진은 내장 기록(최대 0.03 g), 공진 사인은 건물 1차 진동수·39회·quintic 3주기 램프."""
    f = tuning_frequency(b)
    out = {'공진 사인': laboratory_input(round(f, 4), sine_amplitude_g, '가속도 진폭 (g)', 39, None,
                                     ramp_start=3/f, ramp_end=3/f, ramp_profile='quintic')[:2]}
    for kind in FAIR_EXCITATIONS[1:]:
        out[kind] = quake_wave(kind)
    return out


def _fair_score(result):
    m = metrics(result)
    lower = np.min(np.abs(result['lower_water'])) if np.isfinite(result['lower_water']).all() else np.inf
    upper = np.min(np.abs(result['upper_water']))
    limit = min(lower, upper)
    if m is None:
        return dict(valid=False, peak=None, rms=None, acc=None, water_cm=None, margin=None,
                    note=result.get('failure_detail', '수면 한계'))
    water = m['peak_water_displacement_m']
    return dict(valid=True, peak=m['peak_reduction_vs_bare_pct'], rms=m['rms_reduction_vs_bare_pct'],
                acc=m['acceleration_reduction_vs_bare_pct'], water_cm=100*water,
                margin=100*(1-water/limit) if np.isfinite(limit) and limit > 0 else None, note='')


def fair_comparison(b, d, candidates, optimize_on='엘센트로 지진', ratios=(.9, .95, 1.), betas=(.3, .5, .7, .9),
                    lengths=None, air_mode='stop', metric='rms', max_height=None, sine_amplitude_g=.01,
                    progress=None, stop=None, require_all=True, max_checks=40):
    """candidates: [(라벨, 기준 이름, 매개변수 dict)]. 각 후보를 최적화한 뒤 가진 4종·건물 ±10%로 평가한다."""
    if metric not in ('rms', 'peak'): raise ValueError('선정 기준은 rms 또는 peak입니다.')
    floor = b.floor_data()[3] if not b.mount else b.mount
    waves = fair_excitations(b, sine_amplitude_g)
    if optimize_on not in waves: raise ValueError('최적화 가진을 확인하세요.')
    t, ag = waves[optimize_on]
    lengths = [d.B] if not lengths else list(lengths)
    results = []
    for index, (label, kind, params) in enumerate(candidates):
        if stop is not None and stop.is_set(): break
        item = dict(label=label, kind=kind, params=params, best=None, scores={}, robust={}, note='', searched=0, eligible=0)
        results.append(item)
        if progress is not None: progress.update(candidate=index+1, candidates=len(candidates), label=label, completed=0, total=0)
        try:
            cand = fair_candidate(d, kind, **params)
            rows = search_designs(b, cand, t, ag, betas, [cand.angle], lengths, True, list(ratios), [floor],
                                  stop=stop, progress=progress, air_mode=air_mode)
        except ValueError as error:
            item['note'] = str(error); continue
        item['searched'] = len(rows)
        key = 'rms_pct' if metric == 'rms' else 'peak_pct'
        good = sorted([r for r in rows if r['eligible'] and r[key] is not None], key=lambda r: r[key], reverse=True)
        item['eligible'] = len(good)
        # 최적화 가진 하나에서만 1등이면 물이 한계에 걸친 설계가 뽑힐 수 있다. require_all이면
        # 순위대로 확인하며 가진 4종을 모두 끝까지 견디는 첫 설계를 고른다(최대 max_checks개 확인).
        chosen = None; checked = 0; rejected = {'height': 0, 'waves': 0}
        for row in good:
            if stop is not None and stop.is_set(): break
            model, test = search_trial(b, cand, row['B'], row['r'], floor)
            test = replace(test, beta=row['beta'], angle=row['angle'])
            height = device_height(test)
            if max_height is not None and height > max_height + 1e-12:
                rejected['height'] += 1; continue
            if checked >= max_checks: break
            checked += 1
            scores = {}
            for name, (tt, aa) in waves.items():
                scores[name] = _fair_score(simulate_space(model, test, tt, aa, air_mode=air_mode))
                if require_all and not scores[name]['valid']: break
            if require_all and not all(v['valid'] for v in scores.values()) or len(scores) < len(waves):
                rejected['waves'] += 1; continue
            chosen = (row, model, test, height, scores); break
        item['checked'] = checked; item['rejected'] = rejected
        if chosen is None:
            item['note'] = '조건을 만족하는 설계 없음' + (f' · 높이 초과 {rejected["height"]}개' if rejected['height'] else '') + \
                (f' · 다른 가진에서 물 한계 초과 {rejected["waves"]}개' if rejected['waves'] else '') + \
                (f' · 상태 예: {rows[0]["status"]} {rows[0]["reason"][:60]}' if rows and not good else ''); continue
        row, model, test, height, scores = chosen
        item['best'] = dict(r=row['r'], beta=row['beta'], B=row['B'], h=test.h, diameter=test.diameter,
                            mass=test.mass, height=height, tlcd_hz=test.frequency, building_hz=tuning_frequency(model),
                            loss=test.loss, rank=good.index(row)+1)
        item['scores'] = scores
        for scale in (.9, 1.1):
            if stop is not None and stop.is_set(): break
            # TLCD는 그대로 두고 건물 강성만 바꿔 건물 진동수를 scale배로 만든 뒤 그 공진에서 흔든다.
            shifted = replace(model, stories=tuple(k*scale**2 for k in model.stories),
                              stories_y=tuple(k*scale**2 for k in model.stories_y))
            f = tuning_frequency(shifted)
            tt, aa = laboratory_input(round(f, 4), sine_amplitude_g, '가속도 진폭 (g)', 39, None,
                                      ramp_start=3/f, ramp_end=3/f, ramp_profile='quintic')[:2]
            item['robust'][scale] = _fair_score(simulate_space(shifted, test, tt, aa, air_mode=air_mode))
    return results


def fair_report_text(results, settings):
    """공정 비교 결과를 표 문자열로 만든다. 기준은 목록의 첫 후보(U형)."""
    fmt = lambda v: '   -  ' if v is None else f'{v:6.1f}'
    names = list(FAIR_EXCITATIONS)
    lines = ['[공정 비교] 같은 건물·물 질량·손실·수면 처리·가진에서, 모양마다 r·β·B를 따로 최적화한 최선끼리 비교',
             f"최적화 가진: {settings['optimize_on']} · 선정 기준: {'RMS 변위 저감' if settings['metric']=='rms' else '최대 변위 저감'}"
             f" · 수면 처리: {AIR_MODE_LABELS.get(settings['air_mode'], settings['air_mode'])}"
             + (f" · 높이 제한 {settings['max_height']*100:g} cm" if settings.get('max_height') else ''),
             f"고정 조건: 건물 1차 {settings['building_hz']:.3f} Hz · 물 {settings['water_kg']:.4g} kg · 손실 {settings['loss_text']}"
             f" · 공진 사인 {settings['sine_amplitude_g']:g} g · 지진 최대 0.03 g", '']
    base = next((r for r in results if r['best']), None)
    for r in results:
        lines.append(f"■ {r['label']}  (탐색 {r['searched']}개, 최적화 가진에서 선정 가능 {r['eligible']}개)")
        if not r['best']:
            lines.append(f"   최적 설계 없음: {r['note']}"); lines.append(''); continue
        bst = r['best']
        lines.append(f"   최적: r {bst['r']:.3g} · β {bst['beta']:.3g} · B {bst['B']*100:.1f} cm · h {bst['h']*100:.1f} cm · "
                     f"안지름 {bst['diameter']*100:.2f} cm · 높이 {bst['height']*100:.1f} cm · 물 {bst['mass']:.4g} kg · 손실 {bst['loss']:.2f}")
        if bst.get('rank', 1) > 1:
            lines.append(f"   ※ 최적화 가진 순위 {bst['rank']}위 설계 (상위 설계는 다른 가진에서 물 한계 초과 또는 높이 초과)")
        lines.append('   가진           최대변위저감%  RMS저감%  가속도저감%  물 최대cm  물 여유%   U형 대비(최대/RMS %p)')
        for name in names:
            s = r['scores'].get(name)
            if s is None: continue
            if not s['valid']:
                lines.append(f"   {name:<12} 계산 중단: {s['note'][:70]}"); continue
            diff = ''
            if base is not r and base and base['scores'].get(name, {}).get('valid'):
                bs = base['scores'][name]
                diff = f"{s['peak']-bs['peak']:+6.1f} / {s['rms']-bs['rms']:+6.1f}"
            lines.append(f"   {name:<12} {fmt(s['peak'])}      {fmt(s['rms'])}   {fmt(s['acc'])}     {fmt(s['water_cm'])}   {fmt(s['margin'])}   {diff}")
        rb = r['robust']
        if rb:
            parts = []
            for scale in (.9, 1.1):
                s = rb.get(scale)
                parts.append(f"건물 {int(round((scale-1)*100)):+d}%: " + (f"최대 {s['peak']:.1f}% / RMS {s['rms']:.1f}%" if s and s['valid'] else '계산 중단'))
            lines.append('   강건성(공진 사인) ' + ' · '.join(parts))
        lines.append('')
    lines.append('선정 규칙: 최적화 가진 순위대로 확인하여 가진 4종을 모두 끝까지 견디는 첫 설계를 최적으로 선택.')
    lines.append('읽는 법: 여러 가진·강건성에서 고루 U형보다 높으면 우수. 몇 %p 차이는 모델 불확실성(관 손실 등) 안일 수 있음.')
    lines.append('U형 외 모양은 실험 검증 전이며, 분기·꺾임 손실은 모양별로 따로 반영하지 않았다.')
    return '\n'.join(lines)


def frequency_experiment(b,d,frequencies,amplitude,mode,cycles,measure_cycles,installed=True,air_mode='stop'):
    if not isinstance(cycles,int) or not isinstance(measure_cycles,int) or not 1<=measure_cycles<=cycles:
        raise ValueError('주기 수는 정수이고 1 ≤ 평가 주기 ≤ 전체 주기여야 합니다.')
    rows=[]
    for hz in frequencies:
        t,ag,meta=laboratory_input(float(hz),amplitude,mode,cycles)
        result=simulate_space(b,d,t,ag,installed,air_mode=air_mode)
        start=max(float(t[0]),float(t[-1]-measure_cycles/hz))
        tables=acceleration_table(result,start,float(t[-1]))
        # 액체가 앞 구간에서 한계에 도달했다면 정상상태 구간의 성능도 산출하지 않는다.
        for i,row in enumerate(tables):
            window=np.r_[start,t[(t>start)&(t<t[-1])],t[-1]]
            base=np.interp(window,result['t'],result['floor_bare'][:,i])
            row.update(frequency_hz=float(hz),frequency_ratio=float(hz/tuning_frequency(b)),
                amplitude=amplitude,amplitude_mode=mode,cycles=cycles,measure_cycles=measure_cycles,
                baseline_u_rms_m=float(rms(base,window)),baseline_u_peak_m=float(np.max(abs(base))),
                tlcd_u_rms_m=None,tlcd_u_peak_m=None,
                air_mode=result['air_mode'],bearing_deg=b.bearing,experiment='현재 가진 방위의 독립 고정 주파수 실험; 시간변화 사인 스윕 아님')
            if result['valid']:
                active=np.interp(window,result['t'],result['floors_x'][:,i])
                row.update(tlcd_u_rms_m=float(rms(active,window)),tlcd_u_peak_m=float(np.max(abs(active))))
            rows.append(row)
    return rows

def tanveer_known_conditions():
    # 논문 표의 구조 매개변수와 본문 설계식만 사용. 결과값에 맞추는 보정은 수행하지 않는다.
    b=Building(mass=8.8,masses=(2.2,)*4,stories=(1505.10,)*4,stories_y=(1505.10,)*4,
        heights=(.381,)*4,mount=4,damping_mode='직접 계수',story_c=(1.720,)*4,story_cy=(1.720,)*4)
    b=replace(b,frequency=tuning_frequency(b))
    L=2*G/(2*np.pi*.97*b.frequency)**2;B=.70*L;mass=.05*sum(b.masses)
    A=mass/(1000*L)
    d=Damper(B=B,h=(L-B)/2,diameter=math.sqrt(4*A/np.pi))
    return b,d,dict(status='알려진 조건만 적용; 정확 재현 실행 금지',
        computed=dict(water_mass_kg=mass,L_m=L,B_m=B,h_m=d.h,area_m2=A,diameter_m=d.diameter,
            model_first_hz=b.frequency,tuning_ratio=.97),
        missing=['일반 TLCD의 비선형 손실계수/오리피스','조화 가진 진폭','평가 시간/주기','관 끝 높이','실제 진동대 기록/사인 스윕 주파수 이력'],
        note='본문의 ξ_l 및 c_L=2m_l ξ_l ω_d는 TLCBD 선형감쇠 정의. 본 코드의 무차원 비선형 ξ로 직접 대입하지 않는다.',
        sine_sweep_displacement_cm=.15,harmonic_candidates_hz=[.5,1.,1.5],
        source='https://doi.org/10.1371/journal.pone.0224436')


STABLE_TUNING_RATIO = .98   # 안정 예제에서만 사용하는 조율비

def stable_example():
    """넓은 탐색 범위를 위한 2층 교육용 예제. 실제 제작·구조 안전성 판정용이 아니다.
    목표 범위 r=.9~1, beta=.2~.8, B=.1~1 m, 기둥 기울기 45~90°, 설치 방향 0~60°.
    기본 가진은 0.35 Hz·0.01 g·39주기·시작/종료 3주기 quintic 램프다.
    h는 물량 파라미터이며 긴 관이 필요하다. 다른 가진·평가 시간의 완료 여부는 별도 계산한다.
    """
    building=Building(mass=20.,damping=.25,masses=(10.,10.),stories=(1.,1.),
        stories_y=(1.,1.),heights=(.3,.3),mount=2,width=1.2,depth=1.2)
    stiffness=(.35/tuning_frequency(building))**2
    building=replace(building,stories=(stiffness,stiffness),stories_y=(stiffness,stiffness),frequency=.35)
    B=.3
    length=2*G/(2*np.pi*STABLE_TUNING_RATIO*building.frequency)**2
    area=.29452/(1000*length)
    return building,Damper(B=B,h=(length-B)/2,diameter=math.sqrt(4*area/np.pi),
        freeboard=.75,beta=.5,pipe_loss=0.)


def read_settings(path):
    """설정 데이터는 실행 파일과 별도로 보존한다."""
    if not path.exists():return dict(version=1,profiles={},last=None)
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('version')!=1 or not isinstance(data.get('profiles'),dict):
        raise ValueError('지원하지 않는 설정 파일 형식입니다.')
    return data

def write_settings(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


# GUI 조립, 입력 적용, 작업 스레드 및 결과 표시를 담당한다.
# 작업 스레드는 숫자 계산을, Tkinter 메인 스레드는 위젯 변경을 담당한다.
def lab(b,d,t,ag,title,out):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import time
    from concurrent.futures import ThreadPoolExecutor
    root = tk.Tk()
    root.title('TLCD 실험실')
    root.geometry('1070x745')
    root.minsize(830,620)
    # 왼쪽 폭을 메시지 길이와 분리한다. 긴 설정·오류는 세로로 늘어나며 스크롤한다.
    sidebar=ttk.Frame(root,width=460);sidebar.pack(side='left',fill='y')
    sidebar.pack_propagate(False)
    sidebar_canvas=tk.Canvas(sidebar,highlightthickness=0,width=440)
    sidebar_scroll=ttk.Scrollbar(sidebar,orient='vertical',command=sidebar_canvas.yview)
    sidebar_scroll.pack(side='right',fill='y');sidebar_canvas.pack(side='left',fill='both',expand=True)
    sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
    panel=ttk.Frame(sidebar_canvas,padding=14)
    sidebar_window=sidebar_canvas.create_window((0,0),window=panel,anchor='nw')
    layout_state={'pending':None,'width':None}
    def resize_sidebar(*_):
        # 입력값·오류가 길어도 왼쪽 폭은 창 너비만을 기준으로 결정한다.
        available=max(360,min(480,int(root.winfo_width()*.43)))
        sidebar.configure(width=available)
        viewport=max(1,available-sidebar_scroll.winfo_reqwidth())
        if layout_state['width']!=viewport:
            layout_state['width']=viewport
            sidebar_canvas.itemconfigure(sidebar_window,width=viewport)
            def wrap_labels(parent):
                for child in parent.winfo_children():
                    if isinstance(child,ttk.Label):
                        siblings=child.master.winfo_children()
                        entries=[w for w in siblings if isinstance(w,(ttk.Entry,ttk.Spinbox))]
                        # 같은 가로 행의 입력칸 공간을 먼저 확보하고 긴 왼쪽 라벨을 줄바꿈한다.
                        row_label=child.pack_info().get('side')=='left' if child.winfo_manager()=='pack' else False
                        reserve=max((w.winfo_reqwidth() for w in entries),default=0) if row_label else 0
                        child.configure(wraplength=max(45 if reserve else 100,viewport-55-reserve))
                    wrap_labels(child)
            wrap_labels(panel)
        sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox('all'))
        layout_state['pending']=None
    def queue_sidebar_resize(event=None):
        if event is not None and event.widget not in (root,panel,sidebar_canvas):return
        if layout_state['pending'] is None:layout_state['pending']=root.after_idle(resize_sidebar)
    panel.bind('<Configure>',queue_sidebar_resize)
    sidebar_canvas.bind('<Configure>',queue_sidebar_resize)
    root.bind('<Configure>',queue_sidebar_resize,add='+')
    def scroll_sidebar(event):
        widget=event.widget
        if isinstance(widget,(ttk.Combobox,ttk.Spinbox)):return
        while widget is not None:
            if widget is sidebar:
                sidebar_canvas.yview_scroll(-int(event.delta/120),'units');return
            widget=getattr(widget,'master',None)
    root.bind_all('<MouseWheel>',scroll_sidebar,add='+')
    body = ttk.Frame(root,padding=(0,10,12,8))
    body.pack(side='left',fill='both',expand=True)
    ttk.Label(panel,text='TLCD 실험실',font=('Malgun Gothic',17,'bold')).pack(anchor='w')
    quick_actions=ttk.Frame(panel);quick_actions.pack(fill='x',pady=(4,8))
    ttk.Style(root).configure('Sidebar.TNotebook.Tab',padding=(4,3))
    settings=ttk.Notebook(panel,style='Sidebar.TNotebook');settings.pack(fill='x',pady=6)
    pipe_page=ttk.Frame(settings,padding=6); quake_page=ttk.Frame(settings,padding=6)
    shape_page=ttk.Frame(settings,padding=6)
    settings.add(shape_page,text='모양')
    shape_var=tk.StringVar(value='U형' if d.shape=='V형' else d.shape)   # V형은 화면에서 'U형 + 기울기'
    ttk.Label(shape_page,text='관 모양').pack(anchor='w')
    shape_display=tk.StringVar(value=SHAPE_DISPLAY.get(shape_var.get(),shape_var.get()))
    syncing=[False]
    def display_to_shape(*_):
        if syncing[0]:return
        syncing[0]=True;shape_var.set(SHAPE_INTERNAL.get(shape_display.get(),shape_display.get()));syncing[0]=False
    def shape_to_display(*_):
        if syncing[0]:return
        syncing[0]=True;shape_display.set(SHAPE_DISPLAY.get(shape_var.get(),shape_var.get()));syncing[0]=False
    shape_display.trace_add('write',display_to_shape);shape_var.trace_add('write',shape_to_display)
    picker_shape=ttk.Combobox(shape_page,textvariable=shape_display,values=[SHAPE_DISPLAY[x] for x in GUI_SHAPES],state='readonly',width=22)
    picker_shape.pack(fill='x')
    tilt_var=tk.StringVar(value=f'{d.tilt:g}')   # 기둥 기울기. 90=수직, 90 미만 바깥쪽, 90 초과 안쪽
    tr=ttk.Frame(shape_page);tr.pack(fill='x',pady=4)
    ttk.Label(tr,text='기둥 기울기 (°)').pack(side='left')
    ttk.Entry(tr,textvariable=tilt_var,width=7).pack(side='right')
    tilt_hint=tk.StringVar()
    def update_tilt_hint(*_):
        where={'U형':'양쪽 기둥이','다기둥형':'양 끝 기둥만(가운데는 수직)','피자 거치대':'모든 기둥이'}.get(shape_var.get(),'기둥이')
        tilt_hint.set(f'90=수직 · 90 미만=바깥쪽 · 90 초과=안쪽\n{where} 기울어집니다.')
    update_tilt_hint();shape_var.trace_add('write',update_tilt_hint)
    ttk.Label(shape_page,textvariable=tilt_hint,foreground='#30566a').pack(anchor='w')
    ttk.Label(shape_page,text='각 기둥 당 같은 질량으로 물 분배\n모양 비교 시 빈 관 질량도 고정합니다.').pack(anchor='w')
    column_var=tk.StringVar(value=str(d.columns))
    row=ttk.Frame(shape_page);row.pack(fill='x')
    ttk.Label(row,text='기둥 수 (일렬형 2~24 · 방사형 3~24)').pack(side='left')
    ttk.Spinbox(row,from_=2,to=24,width=4,textvariable=column_var).pack(side='right')
    leg_specs={d.shape:(d.bores,d.tops)}
    def edit_legs():
        shape=shape_var.get()
        if shape!='U형':
            messagebox.showinfo('기둥 설정','모양에서 U형을 선택하세요.');return
        window=tk.Toplevel(root);window.title(shape+' 기둥 설정')
        ttk.Label(window,text='안지름·전체 높이(cm) · 빈칸은 기본값\n높이는 바닥 관 중심부터 열린 끝까지입니다.').grid(row=0,column=0,columnspan=3)
        for i,label in enumerate(('위치','안지름','전체 높이')):
            ttk.Label(window,text=label).grid(row=1,column=i)
        groups=['U관']
        specs=leg_specs.get(shape,((),()))
        entries=[[],[]]
        for i in range(2*len(groups)):
            ttk.Label(window,text=groups[i//2]+(' · 왼쪽',' · 오른쪽')[i%2]).grid(row=i+2,column=0)
            for j in range(2):
                val=tk.StringVar(value=f'{specs[j][i]*100:g}' if specs[j] and specs[j][i] else '')
                entries[j].append(val);ttk.Entry(window,width=9,textvariable=val).grid(row=i+2,column=j+1)
        def accept():
            try:
                values=[tuple(float(v.get())/100 if v.get().strip() else None for v in group) for group in entries]
                if any(v is not None and (not math.isfinite(v) or v<=0) for group in values for v in group):raise ValueError()
            except ValueError:
                messagebox.showerror('값 확인','양수를 cm로 입력하세요.',parent=window);return
            leg_specs[shape]=tuple(group if any(v is not None for v in group) else () for group in values)
            window.destroy();calculate()
        ttk.Button(window,text='적용',command=accept).grid(row=2+2*len(groups),column=0,columnspan=3)
    ttk.Button(shape_page,text='U관 기둥별 안지름 · 높이',command=edit_legs).pack(fill='x')
    settings.add(pipe_page,text='관 설정');settings.add(quake_page,text='가진')
    freq_page=ttk.Frame(settings,padding=6)
    settings.add(freq_page,text='진동수')
    omega_b=tk.StringVar(value=f'{2*math.pi*b.frequency:.9g}')
    omega_l=tk.StringVar(value=f'{2*math.pi*d.frequency:.9g}')
    tune_mode=tk.BooleanVar(value=False)
    frequency_widgets={}
    for label,var in [('건물 ω (rad/s)',omega_b),('TLCD ω (rad/s)',omega_l)]:
        row=ttk.Frame(freq_page);row.pack(fill='x',pady=4)
        ttk.Label(row,text=label).pack(side='left')
        entry=ttk.Entry(row,textvariable=var,width=11);entry.pack(side='right')
        frequency_widgets[label]=entry
    # 원본 버그 수정: 예전에는 반복문 변수 entry를 썼는데, 뒤의 '가진' 탭 반복문이 같은 이름을 다시 써서
    # 체크박스가 TLCD ω 칸 대신 진원 세기 칸을 열고 닫았다. TLCD 칸을 이름으로 직접 가리킨다.
    tlcd_entry=frequency_widgets['TLCD ω (rad/s)']
    def sync_tlcd_entry(*_):
        tlcd_entry.state(['!readonly'] if tune_mode.get() else ['readonly'])
    def switch_tune():
        sync_tlcd_entry()
        if not tune_mode.get(): preview_frequency()
    ttk.Checkbutton(freq_page,text='TLCD 목표값으로 물 높이 조절',variable=tune_mode,command=switch_tune).pack(anchor='w')
    tune_mode.trace_add('write',sync_tlcd_entry)   # 설정 불러오기처럼 체크 상태가 코드로 바뀔 때도 맞춘다.
    sync_tlcd_entry()
    ttk.Label(freq_page,text='건물은 질량을 유지하고 강성을 조절합니다.\nTLCD는 바닥 관 길이를 유지합니다.').pack(anchor='w')
    floor_page=ttk.Frame(settings,padding=6)
    settings.add(floor_page,text='층별')
    masses0,ks0,hs0,mount0=b.floor_data()
    floor_fields={}
    reference_size=(b.width,b.depth,masses0.copy())
    size_link=tk.BooleanVar(value=False)
    stiffness_mode=tk.StringVar(value='직접 입력')
    ttk.Checkbutton(floor_page,text='건물 크기 연동 · 일정 단위면적 질량 가정',variable=size_link).pack(anchor='w')
    ttk.Combobox(floor_page,textvariable=stiffness_mode,values=['직접 입력','목표 X 1차 진동수'],state='readonly',width=24).pack(anchor='w')
    ttk.Label(floor_page,text='목표 모드에서는 X 강성만 같은 비율로 조정').pack(anchor='w')
    frequency_note=tk.StringVar()
    ttk.Label(floor_page,textvariable=frequency_note).pack(anchor='w')
    count_var=tk.StringVar(value=str(len(masses0)))
    count_row=ttk.Frame(floor_page);count_row.pack(fill='x')
    ttk.Label(count_row,text='건물 층수').pack(side='left')
    ttk.Spinbox(count_row,from_=1,to=100000,textvariable=count_var,width=6).pack(side='right')
    for key,label,vals in [('m','층별 질량 (kg)',masses0),('k','X 강성 (N/m)',ks0),('y','Y 강성 (N/m)',b.stories_y or ks0),('h','층 높이 (m)',hs0)]:
        row=ttk.Frame(floor_page);row.pack(fill='x',pady=2)
        ttk.Label(row,text=label).pack(side='left')
        v=tk.StringVar(value=', '.join(f'{x:.8g}' for x in vals))
        ttk.Entry(row,textvariable=v,width=19).pack(side='right')
        floor_fields[key]=v
    damping_var=tk.StringVar(value=str(b.damping))
    row=ttk.Frame(floor_page);row.pack(fill='x')
    ttk.Label(row,text='감쇠비 (0.02 = 2%)').pack(side='left')
    ttk.Entry(row,textvariable=damping_var,width=7).pack(side='right')
    mount_var=tk.StringVar(value=str(mount0))
    row=ttk.Frame(floor_page);row.pack(fill='x',pady=2)
    ttk.Label(row,text='관 설치 층').pack(side='left')
    ttk.Entry(row,textvariable=mount_var,width=6).pack(side='right')
    ttk.Label(floor_page,text='새 층은 바로 아래층의 값을 복사합니다.').pack(anchor='w')
    size_row=ttk.Frame(floor_page);size_row.pack(fill='x')
    size_vars=[]
    for label,value in [('가로 cm',b.width),('세로 cm',b.depth)]:
        ttk.Label(size_row,text=label).pack(side='left')
        var=tk.StringVar(value=f'{100*value:g}');size_vars.append(var)
        ttk.Entry(size_row,width=5,textvariable=var).pack(side='left')
    def three_floors():
        for key,values in [('m',MASSES),('k',STIFFNESSES),('h',HEIGHTS),('y',STIFFNESSES)]:
            floor_fields[key].set(', '.join(map(str,values)))
        count_var.set(str(len(MASSES)))
        mount_var.set(str(INSTALL_FLOOR))
        calculate()
    ttk.Button(floor_page,text='코드 상단의 층별 예제 적용',command=three_floors).pack(fill='x')
    ttk.Button(floor_page,text='현재 층별 그래프 비교',command=lambda:history_window(floor_view=True)).pack(fill='x')
    default_kind='엘센트로 지진' if title.startswith('1940') else '현재 입력 기록'
    presets=dict(QUAKE_NOTES)
    if default_kind not in presets:presets[default_kind]='불러온 입력 기록을 사용합니다.'
    wave_cache={default_kind:(t,ag)}
    kind_var=tk.StringVar(value=default_kind);wave_note=tk.StringVar(value=presets[default_kind])
    ttk.Label(quake_page,text='흔들림 유형').pack(anchor='w')
    kind_box=ttk.Combobox(quake_page,textvariable=kind_var,values=list(presets),state='readonly',width=22)
    kind_box.pack(fill='x')
    ttk.Label(quake_page,textvariable=wave_note,wraplength=245,foreground='#30566a').pack(anchor='w')
    kind_box.bind('<<ComboboxSelected>>',lambda _:wave_note.set(presets[kind_var.get()]))
    hz_var=tk.StringVar(value='1')
    ttk.Label(quake_page,text='단방향 진동수 (Hz)').pack(anchor='w')
    ttk.Entry(quake_page,textvariable=hz_var,width=8).pack(anchor='w')
    amplitude_mode=tk.StringVar(value='가속도 진폭 (g)')
    amplitude_var=tk.StringVar(value='0.01')
    ttk.Combobox(quake_page,textvariable=amplitude_mode,
        values=['가속도 진폭 (g)','변위 진폭 (cm)'],state='readonly',width=22).pack(fill='x')
    ttk.Entry(quake_page,textvariable=amplitude_var,width=10).pack(anchor='w')
    cycles_var=tk.StringVar(value='30')
    cycles_row=ttk.Frame(quake_page);cycles_row.pack(fill='x',pady=2)
    ttk.Label(cycles_row,text='가진 횟수 (회, 빈칸=기존 30초)').pack(side='left')
    ttk.Entry(cycles_row,textvariable=cycles_var,width=8).pack(side='right')
    duration_note=tk.StringVar()
    ttk.Label(quake_page,textvariable=duration_note,foreground='#30566a').pack(anchor='w')
    def update_duration_note(*_):
        try:
            frequency=float(hz_var.get())
            duration=float(cycles_var.get())/frequency if cycles_var.get().strip() else 30.
            duration_note.set(f'실험 시간 {duration:.5g}초' if frequency>0 and duration>0 else '양수를 입력하세요.')
        except (ValueError,ZeroDivisionError):duration_note.set('진동수와 횟수를 확인하세요.')
    hz_var.trace_add('write',update_duration_note);cycles_var.trace_add('write',update_duration_note)
    update_duration_note()
    ttk.Label(quake_page,text='진폭은 중심에서 최대값 · 기본 0.01 g는 실행용 가정값\n변위 x=A sin(2πft), 가속도 a=−(2πf)² A sin(2πft)',wraplength=245).pack(anchor='w')
    original_wave=ag
    reference_peak=float(np.max(np.abs(ag))/G)
    src=Source(strength=reference_peak)
    quake_fields={}
    source_entries=[]
    for key,label in [('east','동쪽 위치 (km)'),('north','북쪽 위치 (km)'),('depth','깊이 (km)'),('strength','10 km 기준 세기 (g)')]:
        row=ttk.Frame(quake_page);row.pack(fill='x',pady=2)
        ttk.Label(row,text=label).pack(side='left')
        quake_fields[key]=tk.StringVar(value=str(round(getattr(src,key),12)))
        entry=ttk.Entry(row,textvariable=quake_fields[key],width=10)
        entry.pack(side='right');source_entries.append(entry)
    ttk.Label(quake_page,text='지진 모드용 진원·세기 설정\n건물 위치 (0, 0) · 음수는 서쪽/남쪽').pack(anchor='w')
    def update_wave_controls(*_):
        wave_note.set(presets[kind_var.get()])
        for entry in source_entries:
            entry.configure(state='disabled' if kind_var.get()=='단방향' else 'normal')
    kind_var.trace_add('write',update_wave_controls)
    update_wave_controls()
    precision_page=ttk.Frame(settings,padding=6);settings.add(precision_page,text='감쇠·램프')
    damping_mode_var=tk.StringVar(value=b.damping_mode)
    ttk.Label(precision_page,text='건물 감쇠 입력 방식').pack(anchor='w')
    ttk.Combobox(precision_page,textvariable=damping_mode_var,values=['강성비례','모드 감쇠','직접 계수'],state='readonly').pack(fill='x')
    ttk.Label(precision_page,text='강성비례: 1차 모드만 정한 감쇠비, 높은 모드는 더 큼(층이 적을 때 적합)\n모드 감쇠: 모든 모드가 같은 감쇠비(층이 많은 건물에 권장)',wraplength=280,foreground='#30566a').pack(anchor='w')
    c_vars={}
    for key,label,initial in [('x','X 층간 c (N·s/m)',b.story_c),('y','Y 층간 c (빈칸=X)',b.story_cy)]:
        ttk.Label(precision_page,text=label).pack(anchor='w')
        c_vars[key]=tk.StringVar(value=', '.join(map(str,initial)))
        ttk.Entry(precision_page,textvariable=c_vars[key],width=25).pack(fill='x')
    loss_mode_var=tk.StringVar(value='개구비' if d.xi is None else '직접 ξ')
    xi_scope_var=tk.StringVar(value=d.xi_scope)
    ttk.Combobox(precision_page,textvariable=xi_scope_var,values=['total','local'],state='readonly').pack(fill='x')
    ttk.Label(precision_page,text='total=총손실(추가 손실 포함), local=국부손실(추가 손실 별도)',wraplength=280).pack(anchor='w')
    xi_var=tk.StringVar(value='' if d.xi is None else str(d.xi))
    ttk.Label(precision_page,text='유체 비선형 손실 입력').pack(anchor='w')
    ttk.Combobox(precision_page,textvariable=loss_mode_var,values=['개구비','직접 ξ'],state='readonly').pack(fill='x')
    ttk.Entry(precision_page,textvariable=xi_var).pack(fill='x')
    ttk.Label(precision_page,text='직접 ξ는 무차원 관 평균속도 기준\n논문의 선형 유체 감쇠비와 다릅니다.\n직접 ξ는 total/총손실 또는 local/국부손실로 구분합니다.',wraplength=280).pack(anchor='w')
    pipe_loss_var=tk.StringVar(value=f'{d.pipe_loss:g}')
    ttk.Label(precision_page,text='추가 국부 손실계수 (기본 0)').pack(anchor='w')
    ttk.Entry(precision_page,textvariable=pipe_loss_var).pack(fill='x')
    ttk.Label(precision_page,text='근거가 있는 국부 손실만 입력하세요. 총손실 ξ에는 중복으로 더하지 않습니다.',wraplength=280,foreground='#30566a').pack(anchor='w')
    ramp_profile_var=tk.StringVar(value='quintic')
    ttk.Label(precision_page,text='램프 방식 · quintic(기존) / cosine(병합)').pack(anchor='w')
    ttk.Combobox(precision_page,textvariable=ramp_profile_var,values=['quintic','cosine'],state='readonly').pack(fill='x')
    ttk.Label(precision_page,text='코사인 램프는 접속점의 가속도가 불연속일 수 있습니다.',wraplength=280).pack(anchor='w')
    ramps={}
    for key,label in [('start','시작 램프'),('end','종료 램프')]:
        flag=tk.BooleanVar(value=False);value=tk.StringVar(value='1');unit=tk.StringVar(value='초')
        ramps[key]=(flag,value,unit)
        row=ttk.Frame(precision_page);row.pack(fill='x')
        ttk.Checkbutton(row,text=label,variable=flag).pack(side='left')
        ttk.Entry(row,textvariable=value,width=5).pack(side='left')
        ttk.Combobox(row,textvariable=unit,values=['초','주기'],state='readonly',width=5).pack(side='left')
    ttk.Label(precision_page,text='선택한 포락선 적용 · 기본 OFF\n사용자 입력이며 논문 램프 재현이 아닙니다.',wraplength=280).pack(anchor='w')
    paper_mode=tk.StringVar(value='사용자 실험')
    paper_report=[None]
    input_summary=tk.StringVar(value='입력 파형 정보는 조건 적용 후 표시됩니다.')
    ttk.Label(precision_page,textvariable=input_summary,wraplength=290).pack(anchor='w')
    csv_info=tk.StringVar(value='CSV 미선택')
    csv_unit=tk.StringVar(value='m/s2')
    ttk.Combobox(quake_page,textvariable=csv_unit,values=['m/s2','g','cm/s2'],state='readonly',width=10).pack(anchor='w')
    ttk.Label(quake_page,textvariable=csv_info,wraplength=280).pack(anchor='w')
    def load_csv_gui():
        path=filedialog.askopenfilename(parent=root,filetypes=[('CSV','*.csv')])
        if not path:return
        try:
            tt,aa,mm=load_input(path,csv_unit.get(),metadata=True)
        except (ValueError,OSError,KeyError) as error:messagebox.showerror('CSV 입력',str(error));return
        wave_cache['CSV 기록']=(tt,aa);csv_metadata.clear();csv_metadata.update(mm)
        presets['CSV 기록']='CSV 원본 크기 직접 사용 · 진원 보정 및 합산 없음'
        kind_box.configure(values=list(presets));kind_var.set('CSV 기록')
        csv_info.set(f"{mm['original_start_s']:g}~{mm['original_end_s']:g} s / {len(tt)}개 / dt {mm['min_dt_s']:.5g}~{mm['max_dt_s']:.5g}s / 최대 {mm['site_pga_g']:.5g}g")
        setup_plot()
        preview=tk.Toplevel(root);preview.title('입력 가속도 미리보기')
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        fig=Figure(figsize=(7,3),constrained_layout=True);ax=fig.subplots()
        ax.plot(tt+mm['original_start_s'],aa);ax.set(xlabel='원본 시간 (s)',ylabel='가속도 (m/s²)')
        FigureCanvasTkAgg(fig,master=preview).get_tk_widget().pack(fill='both',expand=True)
    csv_metadata={}
    ttk.Button(quake_page,text='CSV 기록 선택 / 변경',command=load_csv_gui).pack(fill='x')
    ttk.Label(quake_page,text='CSV 해제는 흔들림 유형을 다른 모드로 선택').pack(anchor='w')
    pipe_on=tk.BooleanVar(root,True)
    fields={}
    dimension_labels={}
    def update_dimension_labels():
        shape=shape_var.get()
        meanings={'U형':'바닥 수평관 중심선 간 거리 B (cm)',
            'V형':'양쪽 경사관 하단 중심 간 거리 B (cm)',
            '피자 거치대':'가운데~각 기둥 거리의 합 B (cm)',
            '다기둥형':'양 끝 기둥 중심선 간 거리 B (cm)'}
        if 'B' in dimension_labels:dimension_labels['B'].set(meanings[shape])
        if 'h' in dimension_labels:dimension_labels['h'].set('기준 U형 환산 물높이 h (cm, 물량 기준)')

    for key,label,value in [('B','바닥 수평관 중심선 간 거리 B (cm)',d.B*100),('h','기준 U형 환산 물높이 h (cm, 물량 기준)',d.h*100),
              ('diameter','관 안지름 D_i (cm)',d.diameter*100),('angle','설치 각도 (°)',d.angle),
              ('beta','오리피스 개구비 β',d.beta)]:
        row=ttk.Frame(pipe_page); row.pack(fill='x',pady=3)
        dimension_labels[key]=tk.StringVar(value=label)
        ttk.Label(row,textvariable=dimension_labels[key]).pack(side='left')
        fields[key]=tk.StringVar(value=f'{value:g}')
        input_entry=ttk.Entry(row,textvariable=fields[key],width=8)
        if key=='h':input_entry.configure(state='readonly')
        input_entry.pack(side='right')
    ttk.Label(pipe_page,text='h는 물 질량·안지름·B에서 계산되는 결과값입니다.',wraplength=280).pack(anchor='w')
    ttk.Label(pipe_page,text='관 방향은 동쪽 0° · 북쪽 90°').pack(anchor='w',pady=4)
    tune_ratio=tk.StringVar(value=f'{d.frequency/b.frequency:.8g}')
    ratio_enabled=tk.BooleanVar(value=False)
    ttk.Label(freq_page,text='현재 조율비 (X 1차 모드 기준)').pack(anchor='w')
    ttk.Label(freq_page,textvariable=tune_ratio).pack(anchor='w')
    water_var=tk.StringVar(value=f'{d.mass:.9g}')
    ttk.Label(pipe_page,text='총 물 질량 (kg)').pack(anchor='w')
    ttk.Entry(pipe_page,textvariable=water_var,width=10).pack(anchor='w')
    ttk.Label(pipe_page,text='오리피스 손실만 근사 · 분기관 경험식 적용 불확실',wraplength=250).pack(anchor='w')
    air_mode_var=tk.StringVar(value=AIR_MODE_LABELS['stop'])
    ttk.Label(pipe_page,text='수면 한계 처리').pack(anchor='w')
    ttk.Label(pipe_page,text='수평관 천장 도달 시 중단').pack(anchor='w')
    container_mass_var=tk.StringVar(value=str(b.container_mass))
    ttk.Label(pipe_page,text='빈 관·부착물 질량 (kg, 실측값)').pack(anchor='w')
    ttk.Entry(pipe_page,textvariable=container_mass_var,width=10).pack(anchor='w')
    freeboard_var=tk.StringVar(value=str(d.freeboard))  # 수면 위 여유[m], 설정별 보존
    tube_length_var=tk.StringVar(value='' if d.leg_length is None else f'{100*d.leg_length:g}')
    ttk.Label(pipe_page,text='각 기둥 관 길이 (cm, 관 축 기준)').pack(anchor='w')
    ttk.Entry(pipe_page,textvariable=tube_length_var,width=10).pack(anchor='w')
    ttk.Label(pipe_page,text='빈칸은 기존 자동 길이 · 물높이와 별개\nV형 수직 높이 = 관 길이 × sin(경사각)\n개별 U관 높이가 우선 · 빈 관 질량은 자동 변경 안 됨',wraplength=280).pack(anchor='w')
    water_note=tk.StringVar()
    ttk.Label(pipe_page,textvariable=water_note,wraplength=280,foreground='#30566a').pack(anchor='w')
    ttk.Label(shape_page,text='형상·기둥 수·기울기를 바꾸면 같은 물량과 치수에서도 조율비가 달라집니다. 목표값 설정 또는 최적 설계 탐색으로 재조율하세요.\n간격 검사는 안지름 기준이며 관벽 두께는 미포함입니다.',wraplength=280,foreground='#30566a').pack(anchor='w')
    def preview_frequency(*_):
        # 실제 적용과 동일한 입력 경로를 사용한다. h 입력란은 계산 결과 표시용이다.
        if tune_mode.get():return
        try:
            width=float(fields['B'].get())/100
            diameter=float(fields['diameter'].get())/100
            # 물 질량이 기준 입력이다. 화면의 이전 h를 사용하지 않고 부피식으로 다시 구한다.
            mass=float(water_var.get())
            if min(width,diameter,mass)<=0:raise ValueError('양수가 필요합니다.')
            rho=1000.
            height=(mass/(rho*np.pi*diameter**2/4)-width)/2
            if height<=0:raise ValueError('수직부에 남는 물이 없습니다.')
            bores,tops=leg_specs.get(shape_var.get(),((),()))
            trial=replace(d,bores=bores,tops=tops,columns=int(column_var.get()),shape=internal_shape(shape_var.get(),float(tilt_var.get()),bores,tops),
                B=width,h=height,diameter=diameter,tilt=float(tilt_var.get()),freeboard=float(freeboard_var.get()))
            validate(b,trial)
            water_note.set(column_surface_text(trial,b))
            fields['h'].set(f'{height*100:.9g}')
            omega_l.set(f'{2*np.pi*trial.frequency:.9g}')
        except (ValueError,ZeroDivisionError,np.linalg.LinAlgError):
            omega_l.set('입력 확인')
            water_note.set('입력 치수·기둥 간격을 확인하세요.')
    for key in ('B','diameter'):fields[key].trace_add('write',preview_frequency)
    water_var.trace_add('write',preview_frequency)
    column_var.trace_add('write',preview_frequency)
    def stiffness_input_state(*_):
        frequency_widgets['건물 ω (rad/s)'].configure(state='normal' if stiffness_mode.get()=='목표 X 1차 진동수' else 'readonly')
    stiffness_mode.trace_add('write',stiffness_input_state)
    stiffness_input_state()
    update_dimension_labels()
    def change_shape(_):
        update_dimension_labels()
        # 방사형(피자)은 기둥 3개 이상. 처음 고르면 기본 3기둥(기존 피자 거치대)으로 맞춘다.
        if shape_var.get()=='피자 거치대' and current[0].shape!='피자 거치대':column_var.set('3')
        # 모양 전환은 마지막으로 적용한 물의 양을 기준으로 한다.
        previous=current[0]
        for key in ('B','h','diameter'):
            fields[key].set(str(100*getattr(previous,key)))
        tune_mode.set(False);switch_tune()
        calculate(keep_time=True)
    picker_shape.bind('<<ComboboxSelected>>',change_shape)
    tilt_var.trace_add('write',preview_frequency)
    status=tk.StringVar()
    summary=tk.StringVar()
    source=tk.StringVar(value=title)
    source_label=ttk.Label(body,textvariable=source,wraplength=500)
    source_label.pack(anchor='w',fill='x')
    body.bind('<Configure>',lambda event:source_label.configure(wraplength=max(120,event.width-20)),add='+')
    mode_bar=ttk.Frame(body)
    mode_bar.pack(fill='x',pady=(3,4))
    ttk.Label(mode_bar,text='지붕 장치',font=('Malgun Gothic',10,'bold')).pack(side='left',padx=(0,8))
    mode_buttons=[]
    for label,value in [('관 있음',True),('관 없음',False)]:
        btn=ttk.Radiobutton(mode_bar,text=label,value=value,variable=pipe_on,command=lambda:calculate(keep_time=True))
        btn.pack(side='left',padx=5);mode_buttons.append(btn)
    def save_view():
        from matplotlib.figure import Figure
        from matplotlib.patches import Polygon,Ellipse,Rectangle
        path=filedialog.asksaveasfilename(title='현재 시점을 발표용 그림으로 저장',
            defaultextension='.png',filetypes=[('PNG 그림','*.png')],initialfile='TLCD_실험장면.png')
        if not path: return
        setup_plot()
        width,height=scene.winfo_width(),scene.winfo_height()
        fig=Figure(figsize=(width/90,height/90),facecolor=scene['bg'])
        ax=fig.add_axes((0,0,1,1),xlim=(0,width),ylim=(height,0));ax.axis('off')
        for layer,item in enumerate(scene.find_all()):
            kind=scene.type(item)
            pts=np.array(scene.coords(item)).reshape(-1,2)
            opt=lambda key:scene.itemcget(item,key)
            color=opt('fill') or 'none'
            if kind=='text':
                anchor=opt('anchor')
                ax.text(*pts[0],opt('text'),color=color,fontsize=8,zorder=layer,
                        ha='left' if 'w' in anchor else 'center',va='top' if 'n' in anchor else 'bottom' if 's' in anchor else 'center')
            elif kind=='line':
                ax.plot(*pts.T,color=color,lw=float(opt('width'))*.8,zorder=layer,ls='--' if opt('dash') else '-')
                if opt('arrow')=='last' and np.linalg.norm(pts[-1]-pts[-2])>1:
                    ax.annotate('',xy=pts[-1],xytext=pts[-2],zorder=layer,
                                arrowprops=dict(arrowstyle='-|>',color=color,lw=1.8,shrinkA=0,shrinkB=0))
            else:
                style=dict(facecolor=color,edgecolor=opt('outline') or 'none',lw=.7,zorder=layer)
                if kind=='polygon': patch=Polygon(pts,**style)
                elif kind=='rectangle': patch=Rectangle(pts[0],*(pts[1]-pts[0]),**style)
                elif kind=='oval': patch=Ellipse(pts.mean(axis=0),*(pts[1]-pts[0]),**style)
                else: continue
                ax.add_patch(patch)
        fig.savefig(path,dpi=210)
        status.set('현재 장면을 PNG로 저장했어요.')
    ttk.Button(mode_bar,text='장면 PNG 저장',command=save_view).pack(side='right')
    scene=tk.Canvas(body,bg='#f1f5f7',height=335,highlightthickness=1,highlightbackground='#d5dfe5')
    scene.pack(fill='both',expand=True,pady=(4,0))
    bar=ttk.Frame(body); bar.pack(fill='x',pady=5)
    play=ttk.Button(bar); play.pack(side='left')
    position=tk.DoubleVar(value=0)
    scrub=ttk.Scale(bar,from_=0,to=1,variable=position)
    scrub.pack(side='left',fill='x',expand=True,padx=8)
    clock=tk.StringVar(); ttk.Label(bar,textvariable=clock,width=10).pack(side='left')
    graph_type=tk.StringVar(value='건물 변위')
    choices=['건물 변위','건물 가속도','물 높이 변화','옆 방향 변위','지면 · 1층 · 지붕 위치']
    choices+=['선택 층 변위','선택 층 절대가속도','선택 층 층간변위비']
    graph_bar=ttk.Frame(body);graph_bar.pack(fill='x')
    chooser=ttk.Combobox(graph_bar,state='readonly',values=choices,textvariable=graph_type,width=18)
    chooser.pack(side='left')
    ttk.Label(graph_bar,text='측정 층').pack(side='left',padx=(10,2))
    view_floor=tk.StringVar(value='1')
    floor_selector=ttk.Combobox(graph_bar,state='readonly',width=4,textvariable=view_floor)
    floor_selector.pack(side='left')
    chart=tk.Canvas(body,height=142,bg='white',highlightthickness=0); chart.pack(fill='x')
    legend=tk.StringVar()
    ttk.Label(body,textvariable=legend).pack(anchor='w')
    pool=ThreadPoolExecutor(max_workers=1)
    current=[d,simulate_space(b,d,t,ag)]
    initial_info=building_summary(b,current[1])
    frequency_note.set(f"X 1차 {initial_info['fx']:.4f} Hz / Y 1차 {initial_info['fy']:.4f} Hz")
    current[1]['building_spec']=b
    current[1]['source']=dict(src.input_for(ag,d.angle)[2],wave=default_kind)
    history=[]
    zoom=[1.]
    camera=[math.radians(36),math.radians(25)]
    mesh_cache={}
    playback={'running':False,'start':0.,'busy':False}
    cache={(src,d,b,True,default_kind):current[1]}
    # 재생 중 같은 도형은 좌표만 바꾼다. 카메라를 돌려도 매 프레임 새로 만들지 않는다.
    objects={}
    previous_paint={}
    def paint(index,kind,coords,**style):
        key=(index,kind)
        item=objects.get(key)
        signature=(tuple(coords),tuple(style.items()))
        if item is not None and previous_paint.get(key)==signature: return
        previous_paint[key]=signature
        if item is None:
            item=getattr(scene,'create_'+kind)(*coords,**style)
            objects[key]=item
        else:
            scene.coords(item,*coords)
            if kind=='text': scene.itemconfigure(item,text=style['text'])
    def draw_network(dam,r,j,P,shift,roof,heading,yaw,pitch):
        # 세계 방위에 놓은 원형 관의 겉면과 실제 계산된 물 높이를 투영한다.
        key=('network',dam,heading,tuple(P.ravel()))
        if key not in mesh_cache:
            mesh_cache.clear()
            for obj in list(objects):
                if isinstance(obj[0],tuple) and obj[0][0]=='tube':
                    scene.delete(objects.pop(obj))
            feet,up,leg,starts,ends=network(dam)[:5]
            az=np.radians(heading)
            rot=np.array([[np.cos(az),np.sin(az),0],[-np.sin(az),np.cos(az),0],[0,0,1]])
            tubes=[]
            segments=[(a,b-a,None) for a,b in zip(starts,ends)]
            rest=np.broadcast_to(leg,len(feet))
            tops=u_dimensions(dam)[4] if dam.separate_u else np.full(len(feet),dam.leg_length) if dam.leg_length is not None else rest+dam.freeboard/up[:,2]
            bores=u_dimensions(dam)[1] if dam.separate_u else np.full(len(feet),dam.diameter)
            segments.extend((a,u*tops[i],i) for i,(a,u) in enumerate(zip(feet,up)))
            direction=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
            for a,v,column in segments:
                start=a@rot+[0,0,roof+dam.diameter/2]
                vector=v@rot;axis=vector/np.linalg.norm(vector)
                normal=np.cross(axis,[0,0,1] if abs(axis[2])<.98 else [0,1,0])
                normal/=np.linalg.norm(normal);normal2=np.cross(axis,normal)
                phi=np.arange(16)*2*np.pi/16
                ring=(dam.diameter if column is None else bores[column])/2*(np.cos(phi)[:,None]*normal+np.sin(phi)[:,None]*normal2)
                tubes.append(((start+.5*vector)@direction,start@P,vector@P,ring@P,column))
            mesh_cache[key]=(sorted(tubes,key=lambda v:v[0]),rest*up[:,2],tops*up[:,2])
        tubes,rest,tops=mesh_cache[key]
        for index,(_,base,span,ring,column) in enumerate(tubes):
            base=base+shift
            fill=1 if column is None else max(0.,(rest[column]+r['levels'][j,column])/tops[column])  # 미끄럼 근사에서 빈 기둥은 0
            low=base+.86*ring;high=low+span*fill
            # 실루엣의 볼록 다각형은 두 원을 이은 원통의 정확한 선형 투영이다.
            length=np.linalg.norm(span)
            perp=np.array([-span[1],span[0]])/max(length,1e-12)
            k=int(np.argmax(ring@perp));k2=(k+8)%16
            def line_id(tag,coords,**style):
                paint(('tube',index,tag),'line',coords.ravel().tolist(),**style)
            body=np.array([low[k],high[k],high[k2],low[k2]])
            paint(('tube',index,'body'),'polygon',body.ravel().tolist(),fill='#298bb4',outline='')
            for tag,center in [('start',low),('end',high)]:
                paint(('tube',index,tag),'polygon',center.ravel().tolist(),fill='#55b8ce',outline='')
            for side in [k,k2]:
                line_id(('side',side==k),np.vstack([base+ring[side],base+span+ring[side]]),fill='#758e9e',width=1)
            if column is not None:
                rim=base+span+ring
                line_id('rim',np.vstack([rim,rim[0]]),fill='#486678',width=2)
                paint(('tube',index,'number'),'text',tuple(base+span+[0,-9]),text=str(column+1),fill='#284353')

    def draw_scene(*_):
        dam,r=current
        last=r['n_valid']-1
        j=min(last,int(np.searchsorted(t,position.get())))
        x=float(r['state'][j,0]); y=float(r['lateral'][j,0]); level=r['state'][j,2]
        width,height=scene.winfo_width(),scene.winfo_height()
        if width<5 or height<5: return
        # 세계 좌표는 동·북·위. 건물과 카메라는 진원 방위와 독립적이다.
        meta=r['source']
        bearing=math.radians(meta['bearing_deg'])
        dx=x*math.cos(bearing)-y*math.sin(bearing)
        dy=x*math.sin(bearing)+y*math.cos(bearing)
        story_z=np.r_[0,np.cumsum(r['story_height'])]
        nf=len(story_z)-1
        bx,by,H=b.width/2,b.depth/2,story_z[-1]
        yaw,pitch=camera
        cy,sy,cp,sp=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch)
        ground=r['ground'][j]
        gx,gy=ground*math.cos(bearing),ground*math.sin(bearing)
        fx,fy=r['first'][j]
        first_x=fx*math.cos(bearing)-fy*math.sin(bearing)
        first_y=fx*math.sin(bearing)+fy*math.cos(bearing)
        # 바닥부터 관 끝까지의 범위와 이번 실험의 전체 이동량으로 한 번의 배율을 정한다.
        half=max(.54,np.hypot(bx,by)+.06,dam.B*.5+dam.diameter)+r['travel']
        top=H+(dam.leg_length if dam.leg_length is not None else dam.h+dam.freeboard)+dam.diameter
        if dam.separate_u:
            feet=network(dam)[0]
            top=H+max(feet[:,2]+u_dimensions(dam)[4])+dam.diameter
        scale=min(width*.65/(2.05*half),(height-62)/(top*cp+2*half*sp+.06))
        scale*=zoom[0]
        P=np.array([[cy,sy*sp],[-sy,cy*sp],[0,-cp]])*max(1,scale)
        fixed=np.array([width*.35,26+(top*cp+half*sp)*scale])
        origin=fixed+np.array([gx,gy,0])@P
        def poly(key,points,fill,outline):
            screen=np.asarray(points)@P+origin
            paint(key,'polygon',screen.ravel().tolist(),fill=fill,outline=outline)
        # 배경 기준선은 정지하고, 흙과 콘크리트 기초는 적분한 지면 변위만큼 함께 이동한다.
        ref=np.array([[-.5,-.32,-.03],[.5,-.32,-.03]])@P+fixed
        paint('stationary','line',ref.ravel().tolist(),fill='#8799a3',width=2,dash=(3,4))
        def slab(name,hx,hy,z,color):
            poly(name,[(-hx,-hy,z),(hx,-hy,z),(hx,hy,z),(-hx,hy,z)],color,'#899292')
        slab('soil',bx+.14,by+.10,-.026,'#c3bfaf')
        slab('footing',bx+.025,by+.025,-.006,'#a6b2b5')
        for n in range(5):
            mark=np.array([[-.37+n*.18,.28,-.025],[-.35+n*.18,.28,-.025]])@P+origin
            paint(('soilmark',n),'line',mark.ravel().tolist(),fill='#897657',width=2)
        def wallpoint(a,f,z):
            seg=int(np.clip(np.searchsorted(story_z,z)-1,0,nf-1))
            mix=(z-story_z[seg])/r['story_height'][seg]
            def interp(displacements):
                return (displacements[j,seg-1] if seg else 0)*(1-mix)+displacements[j,seg]*mix
            ux,uy=interp(r['floors_x']),interp(r['floors_y'])
            return (a+ux*math.cos(bearing)-uy*math.sin(bearing),f+ux*math.sin(bearing)+uy*math.cos(bearing),z)
        def face(key,side,u1,u2,z1,z2,color,edge):
            def point(u,z):
                return wallpoint(u,math.copysign(by,cy),z) if side=='front' else wallpoint(math.copysign(bx,sy),u,z)
            poly(key,[point(u1,z1),point(u2,z1),point(u2,z2),point(u1,z2)],color,edge)
        for side,half,base in [('front',bx,'#dbe4e8'),('side',by,'#aabac4')]:
            for story in range(nf):
                low,high=story_z[story:story+2];height_i=high-low
                face((side,'wall',story),side,-half,half,low,high,base,'#8496a0')
                for n in range(3):
                    u=(-.67+n*.67)*half
                    face((side,story,n),side,u-.18*half,u+.18*half,
                         low+.30*height_i,low+.80*height_i,'#497488','#e9eff0')
                face(('band',side,story),side,-half,half,high-.04*height_i,high,'#788f9d','#788f9d')
        face('door','front',-.15*bx,.15*bx,0,.58*story_z[1],'#3c5663','#d3cbbd')
        poly('roof',[wallpoint(a,f,H) for a,f in [(-bx,-by),(bx,-by),(bx,by),(-bx,by)]],
             '#d4dce0','#72838b')
        # 둥근 단면을 따라 만든 표면 격자. 정지 형상과 카메라 투영은 재사용한다.
        # 내부 층에 설치한 관은 해당 층 위에 투시 표시한다.
        attach_z=story_z[r['mount']]
        dx,dy,_=wallpoint(0.,0.,attach_z)
        if r.get('installed',True) and (dam.shape!='U형' or dam.separate_u):
            draw_network(dam,r,j,P,origin+np.array([dx,dy,0])@P,attach_z,meta['heading_deg'],yaw,pitch)
        elif r.get('installed',True):
            tube_top=dam.leg_length if dam.leg_length is not None else dam.h+dam.freeboard
            air_height=tube_top-dam.h
            angle=math.radians(meta['heading_deg'] if 'levels' in r else meta['bearing_deg']+dam.angle)
            key=(dam,round(angle,9),width,height,yaw,pitch,scale)
            if key not in mesh_cache:
                mesh_cache.clear()
                radius=dam.diameter/2
                bend=min(dam.B*.22,dam.h*.45,radius*1.8)
                # (관 축을 따른 수평 위치, 높이, 단면의 평면 내 법선)
                rings=[(-dam.B/2,tube_top,1.,0.)]
                for alpha in np.linspace(0,math.pi/2,5):
                    rings.append((-dam.B/2+bend*(1-math.cos(alpha)),bend*(1-math.sin(alpha)),math.cos(alpha),math.sin(alpha)))
                for alpha in np.linspace(0,math.pi/2,5):
                    rings.append((dam.B/2-bend+bend*math.sin(alpha),bend*(1-math.cos(alpha)),-math.sin(alpha),math.cos(alpha)))
                rings.append((dam.B/2,tube_top,-1.,0.))
                ca,sa=math.cos(angle),math.sin(angle)
                theta=np.arange(16)*2*math.pi/16
                def make_mesh(rad):
                    out=[]
                    for u,z,nu,nz in rings:
                        along=u+rad*np.cos(theta)*nu
                        across=rad*np.sin(theta)
                        out.append(np.column_stack([along*ca-across*sa,along*sa+across*ca,
                                attach_z+radius+z+rad*np.cos(theta)*nz]))
                    return np.array(out)
                water=make_mesh(radius*.87); shell=make_mesh(radius)
                # 면 그리기 순서는 고정 카메라에서 먼 쪽부터.
                depth=shell@np.array([sy*cp,cy*cp,sp])
                faces=sorted(((i,k) for i in range(len(rings)-1) for k in range(16)),
                             key=lambda pair:sum(depth[ii,kk%16] for ii in (pair[0],pair[0]+1) for kk in (pair[1],pair[1]+1)))
                ix=np.array([[i,i+1,i+1,i] for i,k in faces])
                kx=np.array([[k,k,(k+1)%16,(k+1)%16] for i,k in faces])
                shades=['#%02x%02x%02x'%(18+int(v*22),115+int(v*70),159+int(v*62)) for v in (.5+.5*np.sin(theta))]
                mesh_cache[key]=(water@P,shell@P,ix,kx,[shades[k] for i,k in faces])
                # 회전한 관의 면 순서와 음영이 바뀌므로 관 그림만 새로 만든다.
                for obj in list(objects):
                    if isinstance(obj[0],tuple) and obj[0][0]=='tube':
                        scene.delete(objects.pop(obj))
            water,shell,ix,kx,colors=mesh_cache[key]
            shift=origin+np.array([dx,dy,0])@P
            water=water+shift
            water[0]+=(-air_height-level)*P[2]
            water[-1]+=(-air_height+level)*P[2]
            for n,coords in enumerate(water[ix,kx].reshape(-1,8).tolist()):
                paint(('tube','water',n),'polygon',coords,fill=colors[n],outline='')
            shell=shell+shift
            for side in (0,-1):
                paint(('tube','surface',side),'polygon',water[side].ravel().tolist(),fill='#81deeb',outline='#418ca3')
                ring=shell[side]
                paint(('tube','rim',side),'line',np.vstack([ring,ring[0]]).ravel().tolist(),fill='#566f81',width=2)
            for k in (0,4,8,12):
                paint(('tube','wall',k),'line',shell[:,k].ravel().tolist(),fill='#839ba8',width=1)
        elif mesh_cache:
            mesh_cache.clear()
            for obj in list(objects):
                if isinstance(obj[0],tuple) and obj[0][0]=='tube':
                    scene.delete(objects.pop(obj))
        if meta.get('wave')=='단방향':
            paint('lab-caption','text',(width*.83,height*.33),
                text=f"실험실 · 세계 X방향\n{meta['harmonic_hz']:g} Hz\n가속도 진폭 {meta['site_pga_g']:.5g} g\n변위 진폭 {meta['displacement_amplitude_m']*100:.5g} cm",
                fill='#304c5c')
        elif meta.get('wave')=='CSV 기록':
            paint('lab-caption','text',(width*.83,height*.33),
                text=f"CSV 직접 입력 · 세계 X방향\n{meta.get('samples',len(t))}개 표본\n최대 가속도 {meta['site_pga_g']:.5g} g\n거리 배율·정규화 없음",fill='#304c5c')
        else:
            # 진원은 km 단위이므로 건물과 별도 축척의 평면도·단면도에 표시한다.
            mx,my=width*.83,height*.33
            size=min(width*.105,height*.14)
            east,north,depth=meta['east'],meta['north'],meta['depth']
            span=max(1.,abs(east),abs(north))
            factor=size/span
            sx,sy=mx+factor*east,my-factor*north
            paint('mapcard','rectangle',(mx-size-22,my-size-26,mx+size+22,my+size+23),fill='#ffffff',outline='#d4dfe5')
            paint('mapx','line',(mx-size,my,mx+size,my),fill='#d5dfe5')
            paint('mapy','line',(mx,my-size,mx,my+size),fill='#d5dfe5')
            # 지도 화살표의 시작은 진원 바로 위의 점, 끝은 건물이다.
            paint('map-arrow','line',(sx,sy,mx,my),fill='#d4473e',width=3,arrow='last',arrowshape=(9,11,4))
            paint('site','rectangle',(mx-4,my-4,mx+4,my+4),fill='#18394b',outline='')
            paint('surface-point','oval',(sx-4,sy-4,sx+4,sy+4),fill='#d4473e',outline='white')
            name='건물 바로 아래' if not (east or north) else ('북' if north>0 else '남' if north<0 else '')+('동' if east>0 else '서' if east<0 else '')+'쪽'
            paint('map-caption','text',(mx,my+size+12),text=f'● 진앙   ■ 건물',fill='#344f60')
            # 건물 모서리 아래에 가려지지 않도록 지붕 위에 독립적인 방향 지시선을 둔다.
            uv=(np.array([math.cos(bearing),math.sin(bearing),0.])@P)
            uv=uv/max(1e-12,np.linalg.norm(uv))
            target=np.array([width*.33,42.])
            start=target-uv*min(width*.09,46.)
            overhead=not(east or north)
            if overhead: start=target-np.array([0.,20.])
            paint('direction','line',(*start,*target),fill='#d4473e',width=3,arrow='last',arrowshape=(9,11,4))
            paint('arrival','text',(width*.51,40),text=f'{name}에서 도달' if not overhead else '건물 바로 아래 진원',fill='#943e39')
            paint('map-title','text',(mx,my-size-13),text='진앙 → 건물  |  위쪽은 북쪽',fill='#304c5c')
            surface=height*.65
            paint('ground','line',(mx-size,surface,mx+size,surface),fill='#69858e')
            section_scale=size/max(1.,abs(east),depth)
            sx=mx+east*section_scale
            sz=surface+section_scale*depth
            paint('depthline','line',(sx,surface,sx,sz),fill='#cf8985',dash=(3,3))
            paint('hypocenter','oval',(sx-5,sz-5,sx+5,sz+5),fill='#d43d39',outline='')
            paint('section','text',(mx,surface-12),text='동서 단면 · 빨간 점은 진원',fill='#304c5c')
            paint('depth','text',(mx,sz+15),text=f"깊이 {meta['depth']:g} km",fill='#913a34')
        paint('header','text',(12,10),text=(f"{r['mount']}층 관 설치" if r.get('installed',True) else '관 없음')+'   /   드래그로 시점 회전',anchor='nw',fill='#233d50')
        for obj in list(objects):
            if isinstance(obj[0],tuple) and obj[0][0]=='dimension':
                scene.delete(objects.pop(obj));previous_paint.pop(obj,None)
        if r.get('installed',True) and dam.shape=='U형' and not dam.separate_u:
            ca,sa=np.cos(angle),np.sin(angle)
            base_z=attach_z+dam.diameter/2
            def dimension_point(u,z):
                return np.array([dx+u*ca,dy+u*sa,base_z+z])@P+origin
            def dimension_line(tag,points,**style):
                paint(('dimension',tag),'line',np.array(points).ravel().tolist(),**style)
            def dimension_text(tag,point,text):
                paint(('dimension',tag),'text',tuple(point),text=text,fill='#172d42',anchor='w',font=('Malgun Gothic',9))
            left=dimension_point(-dam.B/2,0);right=dimension_point(dam.B/2,0)
            dimension_line('center',[left,right],fill='#172d42',dash=(5,3),width=2)
            # B endpoints stay on the projected vertical centerlines, offset only on screen.
            offset=np.array([0,22])
            dimension_line('B',[left+offset,right+offset],fill='#172d42',arrow='both',width=1)
            dimension_line('Bl',[left,left+offset],fill='#718392',dash=(2,3))
            dimension_line('Br',[right,right+offset],fill='#718392',dash=(2,3))
            dimension_text('Blabel',(left+right)/2+offset+[0,12],f'B {dam.B*100:.3f} cm')
            rest=dimension_point(dam.B/2,dam.h)
            dimension_line('rest',[dimension_point(-dam.B/2,dam.h),rest],fill='#477b9b',dash=(2,4))
            hoffset=np.array([30,0])
            dimension_line('h',[right+hoffset,rest+hoffset],fill='#172d42',arrow='both',width=1)
            dimension_line('h0',[right,right+hoffset],fill='#718392',dash=(2,3))
            dimension_line('h1',[rest,rest+hoffset],fill='#718392',dash=(2,3))
            dimension_text('hlabel',(right+rest)/2+hoffset+[4,0],f'h {dam.h*100:.3f} cm')
            dimension_text('formula',np.array([14,46]),f'정지 기준 · L = B + 2h = {dam.length*100:.3f} cm · D_i = {dam.diameter*100:.3f} cm')
        paint('readout','text',(12,height-8),text=f'{t[j]:.2f} 초   |   지면 {ground*1000:+.1f} mm   ·   지면 대비 지붕 {x*1000:+.1f} mm',anchor='sw',fill='#314b5a')
        clock.set(f'{t[j]:.2f} 초')
        chart.delete('cursor')
        cw=chart.winfo_width()
        px=65+(cw-85)*(t[j]-t[0])/(t[-1]-t[0])
        chart.create_line(px,14,px,117,fill='#8392a0',dash=(3,3),tags='cursor')

    def draw_chart(*_):
        # 현재 적용 완료된 결과를 읽는다. 아직 적용하지 않은 입력란 값으로 그래프를 다시 계산하지 않는다.
        dam,r=current
        idx=choices.index(graph_type.get())
        off=not r.get('installed',True)
        if off and idx in (0,1): arrays=r['state'][:,0:1]*1000 if idx==0 else r['acc'][:,2:3]/G
        elif idx==0: arrays=r['state'][:,[4,6,0]]*1000
        elif idx==1: arrays=r['acc']/G
        elif idx==2: arrays=(r['levels']+r['rest_height'] if 'levels' in r else d.h+r['state'][:,2:3])*1000
        # 「측정 층」에서 선택한 층의 장치 있음/없음 응답을 꺼내 같은 축에 그린다.
        elif idx>=5:
            k=int(view_floor.get())-1
            base=r['floor_bare'];active=r['floors_x']
            if idx==5: arrays=1000*np.column_stack((base[:,k],active[:,k]))
            elif idx==6: arrays=np.column_stack((r['floor_bare_acc'][:,k],r['floors_acc'][:,k]))
            else:
                def drift(x):return (x[:,k]-(x[:,k-1] if k else 0))*100/r['story_height'][k]
                arrays=np.column_stack((drift(base),drift(active)))
            if off:arrays=arrays[:,:1]
        elif idx==3: arrays=r['lateral'][:,:1]*1000
        else:
            ground=r['ground']
            arrays=1000*np.column_stack((ground,ground+r['first'][:,0],ground+r['state'][:,0]))
        if idx==4: legend.set('정지 기준 위치   ·   회색  지면       주황  1층       파랑  지붕')
        elif idx in (0,1): legend.set('회색: 장치 없음       주황: 무게추(TLCD무게만큼)       파랑: TLCD적용')
        else: legend.set('파랑  TLCD를 설치한 모형')
        if off and idx!=4: legend.set('관 없음 · 건물 응답' if idx!=2 else '관 없음 · 물 높이 측정 대상 없음')
        if idx>=5 and not off: legend.set(f'{view_floor.get()}층   ·   회색  장치 없음       파랑  현재 TLCD')
        # 계산 결과의 SI 단위를 화면용 mm, g, % 등으로 변환해 축 이름에 표시한다.
        unit=['mm','g','mm','mm','mm','mm','m/s²','%'][idx]
        n=r['n_valid']; width=chart.winfo_width()
        chart.delete('all')
        if width<100: return
        stride=max(1,n//max(80,width//2))
        ids=np.unique(np.r_[np.arange(0,n,stride),n-1])
        bound=max(float(np.max(np.abs(arrays[:n]))),1e-10)
        if idx==2 and 'lower_water' in r:bound=max(bound,float(np.max(abs(np.r_[r['lower_water']+r['rest_height'],r['upper_water']+r['rest_height']])))*1000)
        xx=65+(width-85)*(t[ids]-t[0])/(t[-1]-t[0])
        colors=['#798898','#d18534','#007db4'] if arrays.shape[1]==3 else ['#007db4']
        for sign in [-1,-.5,0,.5,1]:
            pos=65-sign*48
            chart.create_line(65,pos,width-20,pos,fill='#e4eaf0')
            chart.create_text(61,pos,text=f'{bound*sign:.2g} {unit}',anchor='e')
        if idx>=5 and not off:colors=['#798898','#007db4']
        if idx==2 and 'levels' in r:
            palette=['#256ca2','#dd882f','#24836b','#99568a','#723db0','#ba3741']
            colors=[palette[i%len(palette)] for i in range(arrays.shape[1])]
            legend.set('기둥 번호순 · 파랑, 주황, 초록, 보라, 자주, 빨강 (반복)')
        if idx==2 and 'lower_water' in r:
            for bound_value in np.r_[r['lower_water']+r['rest_height'],r['upper_water']+r['rest_height']]*1000:
                y_limit=65-48*bound_value/bound
                chart.create_line(65,y_limit,width-20,y_limit,fill='#b94a48',dash=(4,3))
        for i,color in enumerate(colors):
            if off and idx==2: break
            yy=65-48*arrays[ids,i]/bound
            if len(xx)>1: chart.create_line(*np.column_stack([xx,yy]).ravel().tolist(),fill=color,width=1.6)
        chart.create_text(65,130,text='0 초',anchor='w')
        chart.create_text(width-20,130,text=f'{t[-1]:g} 초',anchor='e')
        draw_scene()

    def refresh():
        dam,r=current
        count=r['floors_x'].shape[1]
        floor_selector.configure(values=list(range(1,count+1)))
        view_floor.set(str(min(int(view_floor.get()),count)))
        m=metrics(r)
        def pct(v): return '기준값 0' if v is None else f'{v:+.1f}%'
        if not r.get('installed',True):
            summary.set(f"관 없음 · 기준 실험\n최대 지붕 변위  {1000*np.max(np.abs(r['state'][:,0])):.2f} mm\n최대 절대가속도  {np.max(np.abs(r['acc'][:,2]))/G:.3f} g")
        elif m:
            a,_,z=m['peak_displacement_m']
            summary.set(f'최대 변위 · 지진 방향\n{a*1000:.2f} → {z*1000:.2f} mm\n\n장치 없음 대비 저감률\n최대 변위  {pct(m["peak_reduction_vs_bare_pct"])}\nRMS 변위  {pct(m["rms_reduction_vs_bare_pct"])}\n가속도  {pct(m["acceleration_reduction_vs_bare_pct"])}\n\n{shape_label(dam)} · 물 {dam.mass:.3f} kg\n관 포함 {dam.mass+b.container_mass:.3f} kg'+extent_text(dam))
        else:
            summary.set(r.get('failure_detail','수면 한계'))
            partial=partial_metrics(r)
            if partial['metrics']:
                value=partial['metrics']['rms_reduction_vs_bare_pct']
                summary.set(summary.get()+f"\n유효 구간만 RMS 저감 {value:+.2f}%" if value is not None else summary.get())
        if r.get('installed',True):
            summary.set(summary.get()+'\n\n'+column_surface_text(dam,b))
            water_note.set(column_surface_text(dam,b))
        scrub.configure(to=max(t[r['n_valid']-1],1e-12))
        position.set(0); draw_chart()
    def pause():
        playback['running']=False
        play.configure(text='▶ 재생')
    def tick():
        if not playback['running']: return
        end=t[current[1]['n_valid']-1]
        pos=min(end,time.monotonic()-playback['start'])
        position.set(pos); draw_scene()
        if pos>=end: pause()
        else: playback['timer']=root.after(33,tick)
    def toggle():
        if playback['running']:
            pause()
            if playback.get('timer'): root.after_cancel(playback['timer'])
            return
        end=t[current[1]['n_valid']-1]
        if position.get()>=end: position.set(0)
        playback.update(running=True,start=time.monotonic()-position.get())
        play.configure(text='Ⅱ 멈춤'); tick()
    def task(work,done,on_finish=None):
        if playback['busy']: return
        pause()
        if playback.get('timer'): root.after_cancel(playback['timer'])
        playback['busy']=True
        picker_shape.state(['disabled'])
        for button in mode_buttons: button.state(['disabled'])
        status.set('계산 중…')
        job=pool.submit(work)
        def poll():
            if not job.done():
                root.after(40,poll); return
            playback['busy']=False
            picker_shape.state(['!disabled'])
            for button in mode_buttons: button.state(['!disabled'])
            try: done(job.result())
            except Exception as error:
                status.set('조건을 확인해 주세요.'); messagebox.showerror('실험실',str(error))
            finally:
                if on_finish is not None:on_finish()
                if root.winfo_exists():update_context_controls()
        root.after(40,poll)
    def calculate(keep_time=False):
        nonlocal ag
        if paper_mode.get()=='논문 미확인':
            messagebox.showinfo('논문 조건 미확인','손실계수·가진 진폭·평가 시간 등이 미확인입니다. 사용자 실험으로 명시적으로 전환한 후 값을 지정하세요.');return
        previous_time=position.get() if keep_time else 0.
        # 「관 있음/없음」의 선택값이다. False이면 유체 결합과 추가 관 질량을 제거한다.
        enabled=pipe_on.get()
        try:
            # 화면 문자열 → 숫자. cm 입력(B,h,D)은 아래에서 m로 변환한다.
            vals={key:float(field.get()) for key,field in fields.items()}
            # 화면의 cm를 내부 계산 단위 m로 바꾸는 위치. angle·beta는 여기서 변환하지 않는다.
            for key in ['B','h','diameter']: vals[key]/=100
            wb=float(omega_b.get())
            if not math.isfinite(wb) or wb<=0: raise ValueError('건물 각진동수는 양수여야 합니다.')
            # 층별 입력란의 쉼표 문자열을 숫자 튜플로 만든다.
            # 'm'→질량, 'k'→X 층간 강성, 'y'→Y 층간 강성, 'h'→층 높이. 관 물높이 h와 다른 값이다.
            lists={key:tuple(float(i.strip()) for i in field.get().split(',')) for key,field in floor_fields.items()}
            # 「건물 층수」에 맞춰 목록을 자르거나 마지막 층 값을 복사한다. 기존 층의 입력값은 유지한다.
            wanted=int(count_var.get())
            if wanted<1:raise ValueError('층수는 1 이상의 정수여야 합니다.')
            previous=len(b.floor_data()[0])
            if wanted!=previous:
                for key,values in lists.items():
                    if len(values) not in (previous,wanted):
                        raise ValueError('층별 값은 기존 층수 또는 새 층수만큼 입력하세요.')
                    lists[key]=(values+(values[-1],)*max(0,wanted-len(values)))[:wanted]
                if wanted<previous and int(mount_var.get())==b.floor_data()[3]:
                    mount_var.set(str(min(wanted,int(mount_var.get()))))
            elif len(set(map(len,lists.values())))==1:
                wanted=len(lists['m'])
            masses,ks,hs=lists['m'],lists['k'],lists['h'];count=len(masses);mount=int(mount_var.get())
            if len(ks)!=count or len(hs)!=count or not 1<=mount<=count:
                raise ValueError('질량·강성·높이의 개수를 맞추고, 설치 층을 1층부터 마지막 층 사이로 입력하세요.')
            if any(not math.isfinite(v) or v<=0 for arr in lists.values() for v in arr):
                raise ValueError('질량, 강성, 높이는 모두 유한한 양수여야 합니다.')
            # 「건물 크기 연동」을 선택한 경우에만 고정 기준 면적 대비 질량을 계산한다.
            # 기준 질량을 사용하므로 조건 적용을 반복해도 면적비가 누적 곱해지지 않는다.
            if size_link.get():
                refmass=reference_size[2]
                if len(refmass)!=count:raise ValueError('크기 연동 기준 층수와 현재 층수가 다릅니다. 수동 모드를 사용하세요.')
                factor=(float(size_vars[0].get())/100*float(size_vars[1].get())/100)/(reference_size[0]*reference_size[1])
                masses=tuple(refmass*factor)
            diff=np.eye(count)-np.eye(count,k=-1)
            # 장치 없는 건물의 X방향 1차 omega를 현재 질량·X 강성으로 계산한다.
            actual=modes(np.diag(masses),diff.T@(np.array(ks)[:,None]*diff))[0][0]
            # 목표 모드에서만 X 강성 전체를 (목표 omega/현재 omega)²배 한다. Y 강성은 이 줄에서 바꾸지 않는다.
            if stiffness_mode.get()=='목표 X 1차 진동수':
                ks=tuple(k*(wb/actual)**2 for k in ks);actual=wb
            # 위에서 확정한 질량·강성·치수를 Building에 넣는다. 이후 실제 M/K/C 조립의 입력이 된다.
            cx=tuple(float(x.strip()) for x in c_vars['x'].get().split(',') if x.strip())
            cy=tuple(float(x.strip()) for x in c_vars['y'].get().split(',') if x.strip())
            target_b=replace(b,container_mass=float(container_mass_var.get()),damping_mode=damping_mode_var.get(),story_c=cx,story_cy=cy,stories_y=lists['y'],damping=float(damping_var.get()),width=float(size_vars[0].get())/100,depth=float(size_vars[1].get())/100,mass=sum(masses),frequency=actual/(2*np.pi),masses=masses,stories=ks,heights=hs,mount=mount)
            mass=float(water_var.get())
            if not np.isfinite(mass) or mass<=0:raise ValueError('물 질량은 양수여야 합니다.')
            # 질량 m=rho*A*(B+2h), A=pi*D²/4를 h에 대해 푼 식. 현재 h 입력칸은 이 결과를 표시한다.
            density=1000.
            vals['h']=(mass/(density*np.pi*vals['diameter']**2/4)-vals['B'])/2
            if vals['h']<=0:raise ValueError('물이 바닥 관을 채우기에 부족합니다. B를 줄이거나 물 질량을 늘리세요.')
            # 「U관 기둥별 안지름·높이」의 사용자 설정을 선택 형상의 관 정보에 합친다.
            bores,tops=leg_specs.get(shape_var.get(),((),()))
            tilt_value=float(tilt_var.get())
            if not 0<tilt_value<180:raise ValueError('기둥 기울기는 0° 초과 180° 미만입니다(90°=수직, 90° 미만 바깥쪽, 90° 초과 안쪽).')
            vals.update(leg_length=float(tube_length_var.get())/100 if tube_length_var.get().strip() else None,shape=internal_shape(shape_var.get(),tilt_value,bores,tops),tilt=tilt_value,columns=int(column_var.get()),bores=bores,tops=tops)
            if ratio_enabled.get():
                ratio=float(tune_ratio.get())
                if not np.isfinite(ratio) or ratio<=0:raise ValueError('조율비는 양수여야 합니다.')
                omega_l.set(str(ratio*actual));tune_mode.set(True)
            # 「TLCD 목표값으로 물 높이 조절」을 켠 경우에만 목표 omega에 맞는 h를 찾는다.
            if tune_mode.get():
                wl=float(omega_l.get())
                if not math.isfinite(wl) or wl<=0: raise ValueError('TLCD 각진동수는 양수여야 합니다.')
                lo,hi=1e-7,max(1.,vals['h'])
                def rate(height):
                    trial=replace(d,**dict(vals,h=height,tops=(),leg_length=None))
                    validate(target_b,trial)
                    return 2*np.pi*trial.frequency
                if rate(lo)<=wl: raise ValueError('이 관 길이에서 가능한 각진동수보다 큽니다.')
                while rate(hi)>wl:
                    hi*=2
                    if hi>1e6:raise ValueError('모형 크기에 맞는 각진동수를 입력하세요.')
                for _ in range(45):
                    mid=(lo+hi)/2
                    if rate(mid)>wl:lo=mid
                    else:hi=mid
                vals['h']=(lo+hi)/2
            if tune_mode.get():
                # 목표 h를 구한 다음 안지름을 조절하여 총 물 질량을 입력값으로 되돌린다.
                scale=math.sqrt(mass/(density*np.pi*vals['diameter']**2/4*(vals['B']+2*vals['h'])))
                vals['diameter']*=scale
                vals['bores']=tuple(None if x is None else x*scale for x in vals['bores'])
                fields['diameter'].set(f"{vals['diameter']*100:.9g}")
            # Damper에 확정 입력을 넣고 길이·개구비·설치 조건을 검사한다. 아직 방향은 화면의 세계 방위이다.
            vals['xi_scope']=xi_scope_var.get()
            vals['xi']=float(xi_var.get()) if loss_mode_var.get()=='직접 ξ' else None
            vals['pipe_loss']=float(pipe_loss_var.get())
            vals['freeboard']=float(freeboard_var.get())
            raw=replace(d,**vals); validate(target_b,raw)
            kind=kind_var.get()
            # 단방향은 실험실 Hz/진폭만 사용. 지진 기록 모드에서만 진원·거리·세기 입력을 사용한다.
            if kind=='단방향':
                timeline,signal,meta=laboratory_input(float(hz_var.get()),
                    float(amplitude_var.get()),amplitude_mode.get(),float(cycles_var.get()) if cycles_var.get().strip() else None,
                    ramp_start=ramp_seconds('start'),ramp_end=ramp_seconds('end'),ramp_profile=ramp_profile_var.get())
                quake=None
                relative=raw.angle%180
            elif kind=='CSV 기록':
                if 'CSV 기록' not in wave_cache:raise ValueError('CSV 파일을 먼저 선택하세요.')
                timeline,signal=wave_cache[kind];meta=dict(csv_metadata);quake=None;relative=raw.angle%180
            else:
                quake=Source(**{key:float(field.get()) for key,field in quake_fields.items()})
                if kind not in wave_cache:wave_cache[kind]=quake_wave(kind)
                timeline,input_wave=wave_cache[kind]
                signal,relative,meta=quake.input_for(input_wave,raw.angle)
                meta['harmonic_hz']=None
            # 가진 방위를 저장한다. 건물의 X/Y 강성행렬을 가진 방향 좌표로 회전할 때 사용한다.
            target_b=replace(target_b,bearing=meta['bearing_deg'])
            meta['wave']=kind
            meta['heading_deg']=raw.angle
            # 화면 관 방위에서 가진 방위를 뺀 상대각을 실제 연성 계산에 전달한다.
            dam=replace(raw,angle=relative,reverse=(raw.angle-meta['bearing_deg'])%360>=180)
            # 캐시 키에는 실제 계산을 바꾸는 모든 설정과 가진 진폭·주파수를 포함한다.
            key=(quake,raw,target_b,enabled,kind,meta.get('harmonic_hz'),
                meta.get('amplitude_mode'),meta.get('amplitude_value'),meta.get('cycles'),meta.get('ramp_start_s'),meta.get('ramp_end_s'),meta.get('ramp_profile'),
                hash(timeline.tobytes()+signal.tobytes()))
        except ValueError as error:
            pipe_on.set(current[1].get('installed',True))
            messagebox.showerror('입력 확인',str(error)); return
        def done(r):
            if len(cache)>=6: cache.clear()
            nonlocal ag,b,t
            t=r["t"]
            ag=r["ag"]
            if kind=='단방향':
                # 사인 변위의 초기 지면 속도는 ωA이다. 정지 초기값으로 이중 적분하면 표류한다.
                r['ground']=np.interp(t,timeline,np.asarray(meta['ground_displacement_m'])) if 'ground_displacement_m' in meta else meta['displacement_amplitude_m']*np.sin(2*np.pi*meta['harmonic_hz']*t)
                r['travel']=np.nanmax(np.hypot(r['floors_x'],r['floors_y']))+max(abs(r['ground']))
            input_summary.set(f"{kind} · {t[-1]-t[0]:.5g} s / 최대 가속도 {np.max(abs(ag)):.6g} m/s² / 최대 지면변위 {np.max(abs(r['ground'])):.6g} m / 시작·종료 램프 {meta.get('ramp_start_s',0):g}, {meta.get('ramp_end_s',0):g} s")
            b=target_b
            omega_b.set(f'{2*np.pi*b.frequency:.9g}')
            count_var.set(str(count))
            for key,values in [('m',masses),('h',hs)]:
                floor_fields[key].set(', '.join(f'{v:.10g}' for v in values))
            floor_fields['k'].set(', '.join(f'{val:.10g}' for val in ks))
            scene.delete('all');objects.clear();previous_paint.clear();mesh_cache.clear()
            fields['h'].set(f'{dam.h*100:.9g}')
            omega_l.set(f'{2*np.pi*dam.frequency:.9g}')
            tune_ratio.set(f'{dam.frequency/b.frequency:.8g}')
            # 결과에는 계산에 사용한 건물의 스냅샷을 붙인다. 뒤에 입력을 바꿔도 이전 실험은 유지된다.
            meta['fluid_scope']=r['fluid_scope'];meta['fluid_properties']=r['fluid_properties']
            r['building_spec']=target_b
            cache[key]=r; r['source']=meta; current[:]=[dam,r]
            location=(f"실험실 {meta['harmonic_hz']:g} Hz · {meta.get('cycles',0):g}회 ({meta.get('duration_s',0):.4g}초) · 변위 진폭 {meta['displacement_amplitude_m']*100:g} cm" if kind=='단방향'
                else 'CSV 원본 입력' if kind=='CSV 기록' else f"진원 거리 {meta['distance_km']:.1f} km")
            source.set(f"{kind}  ·  {count}층 / 관 {mount}층   ·   {location}   ·   건물 입력 {meta['site_pga_g']:.4f} g   ·   관과 진동 방향 {relative:.1f}°")
            model_info=building_summary(b,r)
            frequency_note.set(f"X 1차 {model_info['fx']:.4f} Hz / Y 1차 {model_info['fy']:.4f} Hz")
            r['building_summary']=model_info
            refresh()
            position.set(min(previous_time,t[r['n_valid']-1]));draw_scene()
            persist_last()
            status.set(r.get('failure_detail') or ('주의 · 정지 물높이 1 cm 미만' if dam.h<.01 else '계산 완료 · 비교 목록에 담을 수 있어요.'))
        # 이미 같은 조건을 계산했으면 결과를 재사용한다. 새 계산은 작업 스레드에서 simulate_space()를 실행한다.
        # 작업 완료 후 done()이 입력 표시와 3D 화면을 갱신한다.
        air_mode=AIR_MODE_KEYS.get(air_mode_var.get(),'stop')
        key=key+(air_mode,)
        task(lambda:cache[key] if key in cache else simulate_space(target_b,dam,timeline,signal,enabled,air_mode=air_mode),done)

    def save():
        path=filedialog.askdirectory(title='저장할 폴더 선택')
        if path:
            from datetime import datetime
            folder=Path(path)/datetime.now().strftime('TLCD_%Y%m%d_%H%M%S_%f')
            dam,r=current
            run_title=source.get()
            task(lambda:export_space(folder,b,dam,r,run_title),lambda _:status.set(f'저장 완료\n{folder}'))
    def ramp_seconds(key):
        flag,value,unit=ramps[key]
        if not flag.get():return 0.
        duration=float(value.get())
        return duration/float(hz_var.get()) if unit.get()=='주기' else duration
    def result_table_window(title,rows,figure=None):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
        win=tk.Toplevel(root);win.title(title);win.geometry('1150x720')
        if not rows:ttk.Label(win,text='결과 없음').pack();return
        bar=ttk.Frame(win);bar.pack(fill='x')
        page=ttk.Frame(win);page.pack(fill='both',expand=True)
        columns=list(rows[0]);tree=ttk.Treeview(page,columns=columns,show='headings',height=10)
        headers={'floor':'층','baseline_peak_g':'장치 없음 최대(g)','tlcd_peak_g':'TLCD 최대(g)',
            'baseline_rms_g':'장치 없음 RMS(g)','tlcd_rms_g':'TLCD RMS(g)','peak_reduction_pct':'최대 감소(%)',
            'rms_reduction_pct':'RMS 감소(%)','scope':'평가 범위','status':'상태'}
        x=ttk.Scrollbar(page,orient='horizontal',command=tree.xview);y=ttk.Scrollbar(page,orient='vertical',command=tree.yview)
        tree.configure(xscrollcommand=x.set,yscrollcommand=y.set)
        tree.grid(row=0,column=0,sticky='nsew');x.grid(row=1,column=0,sticky='ew');y.grid(row=0,column=1,sticky='ns')
        page.rowconfigure(0,weight=1);page.columnconfigure(0,weight=1)
        for key in columns:tree.heading(key,text=headers.get(key,key));tree.column(key,width=140,stretch=False)
        for row in rows:tree.insert('','end',values=['—' if row[k] is None else f'{row[k]:.7g}' if isinstance(row[k],float) else row[k] for k in columns])
        def save_csv():
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.csv')
            if path:
                with open(path,'w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
        def copy():
            text='	'.join(headers.get(k,k) for k in columns)+'\n'
            text+='\n'.join('	'.join(str(row[k]) if row[k] is not None else '' for k in columns) for row in rows)
            root.clipboard_clear();root.clipboard_append(text)
        ttk.Button(bar,text='CSV 저장',command=save_csv).pack(side='left')
        ttk.Button(bar,text='표 복사',command=copy).pack(side='left')
        return win,bar
    def acceleration_window():
        run=current[1]
        start=tk.StringVar(value=str(run['t'][0]));end=tk.StringVar(value=str(run['t'][-1]))
        win=tk.Toplevel(root);win.title('층별 절대가속도 평가 구간')
        ttk.Label(win,text='전체 구간은 과도응답을 포함합니다. 시작·끝 시간을 지정하면 해당 구간만 평가합니다.').pack()
        for label,var in [('시작 s',start),('끝 s',end)]:
            row=ttk.Frame(win);row.pack();ttk.Label(row,text=label).pack(side='left');ttk.Entry(row,textvariable=var).pack(side='left')
        def show():
            try:rows=acceleration_table(run,float(start.get()),float(end.get()))
            except ValueError as error:messagebox.showerror('평가 구간',str(error));return
            for row in rows:row['excitation']=run['source']['wave']
            result_table_window('층별 최대·RMS 절대가속도 / 실제 계산',rows)
        ttk.Button(win,text='표 계산',command=show).pack()
    def frequency_window():
        model=b;dam=current[0];installed=pipe_on.get();frequency_air=AIR_MODE_KEYS.get(air_mode_var.get(),'stop')
        win=tk.Toplevel(root);win.title('주 실험실 주파수 응답 · 독립 고정 주파수 실험')
        ttk.Label(win,text='각 주파수는 정지 상대 초기조건에서 독립 계산합니다. 시간변화 사인 스윕이 아닙니다.').pack()
        config={}
        for key,label,default in [('start','시작 Hz','.5'),('end','끝 Hz','1.5'),('step','간격 Hz','.25'),
                ('amplitude','가진 진폭','.01'),('cycles','총 주기 수','20'),('measure','마지막 평가 주기 수','5')]:
            row=ttk.Frame(win);row.pack(fill='x');ttk.Label(row,text=label).pack(side='left')
            config[key]=tk.StringVar(value=default);ttk.Entry(row,textvariable=config[key]).pack(side='right')
        mode=tk.StringVar(value='가속도 진폭 (g)')
        ttk.Combobox(win,textvariable=mode,values=['가속도 진폭 (g)','변위 진폭 (cm)'],state='readonly').pack()
        note=tk.StringVar();ttk.Label(win,textvariable=note).pack()
        def calculate_frequency():
            if paper_mode.get()=='논문 미확인':
                messagebox.showinfo('미확인 조건','사용자 실험으로 전환하고 진폭·주기 수를 직접 지정하세요.');return
            try:
                lo,hi,step=[float(config[k].get()) for k in ('start','end','step')]
                if not all(np.isfinite([lo,hi,step])) or lo<=0 or hi<lo or step<=0:raise ValueError('주파수 범위를 확인하세요.')
                frequencies=lo+step*np.arange(int(np.floor((hi-lo)/step+1e-9))+1)
                amp=float(config['amplitude'].get());cycles=int(config['cycles'].get());measure=int(config['measure'].get());selected_mode=mode.get()
            except ValueError as error:messagebox.showerror('입력',str(error));return
            note.set('계산 중 · 주 화면과 동일 simulate_space() 사용')
            def show(rows):
                note.set('계산 완료')
                setup_plot()
                results_win,bar=result_table_window('주 실험실 주파수 결과',rows)
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                fig=Figure(figsize=(9,4),constrained_layout=True);ax=fig.subplots()
                floor=tk.StringVar(value='1');metric=tk.StringVar(value='u_rms');ratio_axis=tk.BooleanVar(value=False)
                ttk.Combobox(bar,textvariable=floor,values=list(range(1,len(model.floor_data()[0])+1)),state='readonly',width=4).pack(side='left')
                ttk.Combobox(bar,textvariable=metric,values=['u_rms','u_peak','rms_g','peak_g'],state='readonly',width=10).pack(side='left')
                canvas=FigureCanvasTkAgg(fig,master=results_win);canvas.get_tk_widget().pack(fill='both',expand=True)
                def draw(*_):
                    ax.clear();selected=[r for r in rows if r['floor']==int(floor.get())]
                    xkey='frequency_ratio' if ratio_axis.get() else 'frequency_hz'
                    name=metric.get();suffix={'u_rms':'u_rms_m','u_peak':'u_peak_m','rms_g':'rms_g','peak_g':'peak_g'}[name]
                    xx=[r[xkey] for r in selected]
                    for prefix,label in [('baseline','장치 없음'),('tlcd','TLCD')]:
                        ax.plot(xx,[np.nan if r[prefix+'_'+suffix] is None else r[prefix+'_'+suffix] for r in selected],'o-',label=label)
                    ax.set(xlabel='가진 주파수 / X 1차 주파수' if ratio_axis.get() else '가진 주파수 Hz',
                        ylabel='변위 (m)' if name.startswith('u_') else '절대가속도 (g)',title=f'{floor.get()}층 / 마지막 {measure}주기 / {selected_mode} {amp:g} / 물')
                    ax.legend();ax.grid(alpha=.2);canvas.draw_idle()
                for widget in bar.winfo_children():
                    if isinstance(widget,ttk.Combobox):widget.bind('<<ComboboxSelected>>',draw)
                ttk.Checkbutton(bar,text='주파수비 축',variable=ratio_axis,command=draw).pack(side='left')
                def png():
                    path=filedialog.asksaveasfilename(parent=results_win,defaultextension='.png')
                    if path:fig.savefig(path,dpi=300,bbox_inches='tight')
                ttk.Button(bar,text='PNG 저장',command=png).pack(side='left');draw()
            task(lambda:frequency_experiment(model,dam,frequencies,amp,selected_mode,cycles,measure,installed,air_mode=frequency_air),show)
        ttk.Button(win,text='독립 주파수 실험 실행',command=calculate_frequency).pack()

    def optimize():
        if paper_mode.get()=='논문 미확인':
            messagebox.showinfo('논문 조건 미확인','미확인 입력을 지정하고 사용자 실험으로 전환한 뒤 조건 적용을 먼저 누르세요.');return
        setup_plot()
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
        from matplotlib.colors import TwoSlopeNorm
        from collections import Counter
        dam=current[0];model=b;times=t.copy();wave=ag.copy()
        # 탐색 창을 연 시점의 물리 조건은 고정한다.
        optimization_air=AIR_MODE_KEYS.get(air_mode_var.get(),'stop')
        source_metadata=dict(current[1]['source'])
        amplitude_enabled=source_metadata.get('wave')=='단방향' and source_metadata.get('amplitude_mode')=='가속도 진폭 (g)'
        source_description=(f"단방향 {source_metadata['harmonic_hz']:g} Hz · {source_metadata.get('cycles',0):g}주기 · 램프 시작/종료 {source_metadata.get('ramp_start_s',0):g}/{source_metadata.get('ramp_end_s',0):g} s · {source_metadata.get('ramp_profile','quintic')}"
            if source_metadata.get('wave')=='단방향' else source.get())
        win=tk.Toplevel(root);win.title('최적 설계 탐색 · 성능 지도');win.geometry('1200x850')
        # 탐색변수가 늘어도 그래프를 억지로 압축하지 않고 전체 내용을 스크롤한다.
        viewport=tk.Canvas(win,highlightthickness=0)
        vertical=ttk.Scrollbar(win,orient='vertical',command=viewport.yview)
        viewport.configure(yscrollcommand=vertical.set)
        vertical.pack(side='right',fill='y');viewport.pack(side='left',fill='both',expand=True)
        body=ttk.Frame(viewport);body_id=viewport.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda _:viewport.configure(scrollregion=viewport.bbox('all')))
        viewport.bind('<Configure>',lambda event:viewport.itemconfigure(body_id,width=event.width))

        ttk.Label(body,text='다중 물기둥 형상의 r은 최저 유체모드 기준 · 단면을 함께 조정하여 물 질량 유지').pack(anchor='w')
        labels={'r':'조율비 r','beta':'개구비 β','angle':'설치 각도 θ (°)','B':'수평 길이 B (m)','n':'설치 층 n','tilt':'기둥 기울기 (°)','columns':'기둥 수'}
        keys=list(labels)
        selectable=[key for key in keys if not (key=='beta' and dam.xi is not None) and not (key=='tilt' and (dam.shape=='다기둥형' or dam.separate_u)) and not (key=='columns' and dam.shape!='다기둥형')]
        ttk.Label(body,text=('가진 진폭 고정: 주 실험실의 가속도 진폭(g)·Hz·램프를 그대로 사용합니다. 진폭은 탐색하지 않습니다.' if amplitude_enabled else '가진 세기는 주 실험실 입력값으로 고정하며 최적화 변수에 포함하지 않습니다.')).pack(anchor='w')
        ttk.Label(body,text=f'수면 처리: {optimization_air} · 수평관 천장 도달 시 중단').pack(anchor='w')
        ttk.Label(body,text=f'조율 기준 · 세계 X방향 1차 {tuning_frequency(model):.5g} Hz / 총 물 질량 {dam.mass:.5g} kg 고정').pack(anchor='w')
        controls=ttk.Frame(body);controls.pack(fill='x')
        field_widgets={};values={};fixed={};defaults={'r':(.8,1.2,.1),'beta':(.2,.8,.15),'angle':(0,90,45),
            'B':(dam.B*.8,dam.B*1.2,dam.B*.2),'n':(1,len(model.floor_data()[0]),1),'tilt':(60.,90.,15.),'columns':(2,6,1)}
        initial={'r':dam.frequency/tuning_frequency(model),'beta':dam.beta,'angle':dam.angle,'B':dam.B,'n':model.floor_data()[3],'tilt':dam.tilt,'columns':dam.columns}
        for col,text in enumerate(['변수','시작','끝','간격','고정값']):
            ttk.Label(controls,text=text).grid(row=0,column=col)
        for i,key in enumerate(keys,1):
            ttk.Label(controls,text=labels[key]).grid(row=i,column=0,sticky='w')
            values[key]=[tk.StringVar(value=f'{x:.8g}') for x in defaults[key]]
            fixed[key]=tk.StringVar(value=f'{initial[key]:.10g}')
            if key not in selectable:
                ttk.Label(controls,text=f'{initial[key]:.7g} · 현재 설계 기준 고정').grid(row=i,column=1,columnspan=4)
                continue
            for col,v in enumerate([*values[key],fixed[key]],1):
                entry=ttk.Entry(controls,textvariable=v,width=12);entry.grid(row=i,column=col)
                field_widgets[key,col]=entry
        xvar=tk.StringVar(value='B');yvar=tk.StringVar(value='n' if dam.xi is not None else 'beta');full=tk.BooleanVar(value=False)
        peak_rule=tk.BooleanVar(value=True)
        view_mode=tk.StringVar(value='고정 조건 단면도')
        selecting=[False]
        displayed={'cells':{},'axes':None}
        axisbar=ttk.Frame(body);axisbar.pack(fill='x')
        ttk.Label(axisbar,text='X축').pack(side='left')
        xp=ttk.Combobox(axisbar,textvariable=xvar,values=selectable,state='readonly',width=8);xp.pack(side='left')
        ttk.Label(axisbar,text='Y축').pack(side='left')
        yp=ttk.Combobox(axisbar,textvariable=yvar,values=selectable,state='readonly',width=8);yp.pack(side='left')
        mode_picker=ttk.Combobox(axisbar,textvariable=view_mode,values=['고정 조건 단면도','전체 최적화 결과 투영도'],state='readonly',width=25);mode_picker.pack(side='left',padx=5)
        ttk.Label(axisbar,text='r 조율비 / beta 개구비 / angle 각도 / B 길이 / n 층 / tilt 기둥 기울기 / columns 기둥 수').pack(side='left',padx=8)
        ttk.Checkbutton(body,text='전체 최적화 · 활성 변수 범위를 명시적으로 함께 탐색',variable=full).pack(anchor='w')
        ttk.Checkbutton(body,text='최대 변위 악화 설계는 최적 선정에서 제외',variable=peak_rule).pack(anchor='w')
        feedback=tk.StringVar();ttk.Label(body,textvariable=feedback,wraplength=1150).pack(fill='x')
        columns=('amplitude_g','actual_peak_g','air_mode','beta','angle','B','r','width_cm','height_cm','n','tilt','columns','rms_pct','peak_pct','eligible','status','failure_time_s','completion_pct','internal_steps','fluid_scope','reason','check_status','check_rms_delta_pp','check_peak_delta_pp')
        table_caption=tk.StringVar();ttk.Label(body,textvariable=table_caption,wraplength=1150).pack(fill='x')
        table_frame=ttk.Frame(body);table_frame.pack(fill='x')
        tree=ttk.Treeview(table_frame,columns=columns,show='headings',height=6)
        for key,title in zip(columns,['입력 진폭(g)','실제 최대가속도(g)','수면 처리','β','θ (°)','B (m)','r','장치 가로 (cm)','장치 높이 (cm)','설치 층','기둥 기울기(°)','기둥 수','RMS 저감 (%)','최대 저감 (%)','최적 선정 가능','상태','중단 시각 s','완료 %','내부 계산 단계','유체 모델 범위','원인','1위 간격 확인(최대 약 1초)','RMS 차이(%p)','최대 차이(%p)']):
            tree.heading(key,text=title);tree.column(key,width=100 if key!='reason' else 320,stretch=False)
        scroll=ttk.Scrollbar(table_frame,orient='horizontal',command=tree.xview)
        tree.configure(xscrollcommand=scroll.set);scroll.pack(side='bottom',fill='x');tree.pack(fill='x')
        fig=Figure(figsize=(11,6.3),constrained_layout=True)
        canvas=FigureCanvasTkAgg(fig,master=body);NavigationToolbar2Tk(canvas,body).pack(fill='x')
        canvas.get_tk_widget().pack(fill='both',expand=True)
        from threading import Event
        import hashlib
        inspection=tk.StringVar(value='지도에서 칸을 클릭하면 해당 계산의 다섯 설계값과 선정 가능 여부를 확인합니다.')
        ttk.Label(body,textvariable=inspection,wraplength=1150).pack(fill='x')
        results=[];memo={};traces={};verification_memo={};best_state=[None]
        run_state={'running':False,'context':None,'progress':{},'cancel':Event(),'locked':[]}
        progress_text=tk.StringVar()
        ttk.Label(body,textvariable=progress_text).pack(fill='x')
        explanation=tk.StringVar()
        ttk.Label(body,textvariable=explanation,wraplength=1150).pack(fill='x')
        def update_fields():
            if run_state['running']:return
            for key in selectable:
                varied=full.get() or key in (xvar.get(),yvar.get())
                for col in range(1,5):
                    field_widgets[key,col].state(['!disabled'] if (col<=3)==varied else ['disabled'])
        def lock_inputs():
            def visit(parent):
                for widget in parent.winfo_children():
                    if isinstance(widget,(ttk.Entry,ttk.Button,ttk.Combobox,ttk.Checkbutton,ttk.Radiobutton,ttk.Spinbox)):
                        run_state['locked'].append((widget,widget.state()))
                        widget.state(['disabled'])
                    visit(widget)
            visit(root)
            stop_button.state(['!disabled'])
            root_menu=root.cget('menu')
            if root_menu:root.nametowidget(root_menu).entryconfigure('설정',state='disabled')
            if root_menu:root.nametowidget(root_menu).entryconfigure('분석',state='disabled')
        def unlock_inputs():
            run_state['running']=False
            for widget,state in run_state['locked']:
                if widget.winfo_exists():
                    widget.state(['!disabled'])
                    if 'disabled' in state:widget.state(['disabled'])
            run_state['locked'].clear()
            if root.winfo_exists() and root.cget('menu'):root.nametowidget(root.cget('menu')).entryconfigure('설정',state='normal')
            if root.winfo_exists() and root.cget('menu'):root.nametowidget(root.cget('menu')).entryconfigure('분석',state='normal')
            if win.winfo_exists():update_fields();stop_button.state(['disabled'])
        def cancel_search():
            run_state['cancel'].set()
            progress_text.set('중지 요청 · 현재 설계 계산 완료 후 결과를 보존합니다.')
        win.bind('<Destroy>',lambda event:run_state['cancel'].set() if event.widget is win else None,add='+')

        def grids():
            if xvar.get()==yvar.get():raise ValueError('X축과 Y축에 서로 다른 변수를 선택하세요.')
            output={}
            for key in keys:
                if key not in selectable:
                    output[key]=np.array([initial[key]]);continue
                if full.get() or key in (xvar.get(),yvar.get()):
                    lo,hi,step=[float(v.get()) for v in values[key]]
                    if not all(np.isfinite([lo,hi,step])) or step<=0 or hi<lo:raise ValueError('시작 ≤ 끝, 간격 > 0으로 입력하세요.')
                    if key in ('n','columns') and any(not v.is_integer() for v in (lo,hi,step)):raise ValueError('설치 층의 시작·끝·간격은 정수입니다.')
                    count=int(np.floor((hi-lo)/step+1e-8))+1
                    output[key]=lo+step*np.arange(count)
                else:output[key]=np.array([float(fixed[key].get())])
                if not np.isfinite(output[key]).all():raise ValueError('유한한 값을 입력하세요.')
                if key=='n' and (np.any(output[key]%1) or min(output[key])<1 or max(output[key])>len(model.floor_data()[0])):raise ValueError('설치 층은 건물 범위 안의 정수입니다.')
            return output
        guide=tk.StringVar()
        ttk.Label(body,textvariable=guide,wraplength=1150).pack(fill='x')
        def counts(*_):
            if run_state['running']:return
            update_fields()
            try:
                # 화면의 탐색 범위와 고정값으로 실제 계산할 격자를 만든다. 예상 조합 수도 이 격자에서 센다.
                g=grids()
                varied=selectable if full.get() else [xvar.get(),yvar.get()]
                explanation.set('탐색 · '+', '.join(labels[k] for k in varied)+' / 유지 · '+(', '.join(f'{labels[k]}={fixed[k].get()}' for k in keys if k not in varied) or '없음'))
                if equivalent_u(dam):
                    lines=[]
                    for ratio in g['r']:
                        if ratio<=0:raise ValueError('조율비는 양수여야 합니다.')
                        L=2*G/(2*np.pi*tuning_frequency(model)*ratio)**2
                        Di=math.sqrt(4*dam.mass/(dam.rho*np.pi*L))
                        lines.append(f'r={ratio:.5g}: D_i={Di*100:.3f} cm, '+(f'0<B<{L-Di:.6g} m' if L>Di else '허용 B 없음'))
                    guide.set('현재 모델의 보수적 충수 경계이며 실제 공기 유입 확정 조건이 아닙니다. '+ ' | '.join(lines))
                else:guide.set('이 형상은 기존 기둥별 수면·관 끝 높이로 검사합니다. U형 B 제한식은 적용하지 않습니다.')
                feedback.set(f"예상 계산 조합 {int(np.prod([len(v) for v in g.values()]))}개"+' · 물 모델')
            except ValueError as error:feedback.set(str(error))
        def draw(rows):
            if not win.winfo_exists():return
            results[:]=rows;tree.delete(*tree.get_children());fig.clear()
            for row in rows:
                tree.insert('','end',values=['—' if row[k] is None else f'{row[k]:.6g}' if isinstance(row[k],(float,np.floating)) else row[k] for k in columns])
            eligible=[row for row in rows if row['eligible']]
            best=eligible[0] if eligible else None;best_state[0]=best
            feedback.set((f"최적 β={best['beta']:.4g}, θ={best['angle']:.4g}°, B={best['B']:.5g} m, r={best['r']:.5g}, n={best['n']:g} · RMS {best['rms_pct']:+.3f}%, 최대 {best['peak_pct']:+.3f}%" if best else '선정 가능한 최적점 없음')+' · '+str(dict(Counter(row['status'] for row in rows))))
            ax,trace=fig.subplots(1,2)
            context=run_state['context']
            table_caption.set('표·그래프 계산 조건'+' · '+context['source']+' · 축 '+context['x']+' / '+context['y']+' · '+str(context['fixed'])+' · 최대 변위 비악화 '+str(context['require_peak']))
            xx,yy=context['x'],context['y']
            xs=sorted(set(context['grids'][xx]));ys=sorted(set(context['grids'][yy]))
            # 전체 탐색에서는 나머지 변수의 현재 고정값과 일치하는 실제 계산 단면만 표시한다.
            requested={}
            for key in keys:
                try:requested[key]=float(fixed[key].get())
                except ValueError:requested[key]=context['fixed'][key]
            projection=view_mode.get()=='전체 최적화 결과 투영도'
            # 단면도는 존재하는 고정 조합을 선택하고, 투영도는 각 X·Y 칸의 최고 RMS 실제 행을 선택한다.
            section,snapped=select_performance_rows(rows,xx,yy,requested,projection)
            context.update(view_mode=view_mode.get(),view_fixed=snapped)
            if not projection:
                selecting[0]=True
                try:
                    for key in keys:
                        if key not in (xx,yy):fixed[key].set(f'{snapped[key]:.12g}')
                finally:selecting[0]=False
            displayed.update(cells={(float(row[xx]),float(row[yy])):row for row in section},axes=ax)
            table_caption.set('실제 계산 결과 · '+view_mode.get()+' · '+context['source']+' · 표시 단면 '+str(snapped))

            # 계산값이 없는 칸은 NaN으로 유지한다. 보간으로 성능값을 만들어 채우지 않는다.
            matrix=np.full((len(ys),len(xs)),np.nan)
            markers={'정상':'o','최대 변위 악화':'x','수면 상한 도달':'^','수면 하한 도달':'v','모델 적용 범위 초과':'^','초기 충수 조건 미달':'P','잘못된 설계':'s','계산 오류':'D'}
            for row in section:
                if row[xx] is not None and row[yy] is not None and row['rms_pct'] is not None:matrix[ys.index(float(row[yy])),xs.index(float(row[xx]))]=row['rms_pct']
            finite=matrix[np.isfinite(matrix)];bound=max(1.,float(np.max(abs(finite))) if len(finite) else 1.)
            norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound)
            if xs and ys:
                masked=np.ma.masked_invalid(matrix)
                if xx not in ('n','columns') and yy not in ('n','columns') and min(len(xs),len(ys))>=4 and np.isfinite(matrix).all():
                    im=ax.contourf(xs,ys,masked,levels=np.linspace(-bound,bound,17),cmap='RdBu',norm=norm)
                    if np.ptp(finite)>1e-10:
                        lines=ax.contour(xs,ys,masked,levels=7,colors='#44515c',linewidths=.5);ax.clabel(lines,fmt='%.1f',fontsize=7)
                else:
                    im=ax.pcolormesh(xs,ys,masked,shading='nearest',cmap='RdBu',norm=norm)
                fig.colorbar(im,ax=ax,label='RMS 지붕 변위 저감률 (%)')
                from matplotlib.patches import Rectangle
                invalid_styles={'초기 충수 조건 미달':('#dbb4e8','///'),
                    '모델 적용 범위 초과':('#f0c785','xxx'),'수면 상한 도달':('#f0c785','+++'),
                    '수면 하한 도달':('#edbca9','---'),'잘못된 설계':('#c8cbd0','...'),'계산 오류':('#e09ba5','***')}
                def edges(values):
                    a=np.array(values,float)
                    if len(a)==1:return np.array([a[0]-.05,a[0]+.05])
                    return np.r_[a[0]-(a[1]-a[0])/2,(a[:-1]+a[1:])/2,a[-1]+(a[-1]-a[-2])/2]
                xe,ye=edges(xs),edges(ys)
                seen=set()
                for row in section:
                    if row['rms_pct'] is not None or row[xx] is None or row[yy] is None:continue
                    color,hatch=invalid_styles.get(row['status'],('#dddddd','//'))
                    ix,iy=xs.index(float(row[xx])),ys.index(float(row[yy]))
                    ax.add_patch(Rectangle((xe[ix],ye[iy]),xe[ix+1]-xe[ix],ye[iy+1]-ye[iy],
                        facecolor=color,edgecolor='#777777',hatch=hatch,linewidth=.3,zorder=3,label=row['status'] if row['status'] not in seen else None))
                    seen.add(row['status'])
                for status,marker in markers.items():
                    subset=[row for row in section if row['rms_pct'] is not None and row['status']==status and row[xx] is not None and row[yy] is not None]
                    if subset:ax.scatter([r[xx] for r in subset],[r[yy] for r in subset],marker=marker,s=15,color='#202020',label=status)
                if best and best in section:ax.plot(best[xx],best[yy],'*',ms=15,color='#f3c13a',markeredgecolor='black',label='실제 계산 최적점')
            ax.set(xlabel=labels[xx],ylabel=labels[yy],title=view_mode.get()+'\n색상 RMS / 해칭 무효 / 빈 칸 미계산')
            if not section:ax.text(.5,.5,'완료된 계산 결과가 없습니다.',transform=ax.transAxes,ha='center')
            if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=7)
            fixed_text=('투영도 · 각 칸의 최고 RMS (최대 변위 악화도 표시, 선정은 별도)' if projection else '실제 계산 단면 · '+', '.join(f'{labels[k]}={snapped[k]:.6g}' for k in keys if k not in (xx,yy)))
            mass_values,k_values,_,_=model.floor_data()
            condition=f"층 질량 kg={np.array2string(mass_values,precision=3)} · X 강성 N/m={np.array2string(k_values,precision=3)} · Y 강성={np.array2string(np.array(model.stories_y) if model.stories_y else k_values,precision=3)}"
            best_text=(f"최적 β={best['beta']:.4g}, θ={best['angle']:.4g}°, B={best['B']:.4g} m, r={best['r']:.4g}, n={best['n']:g} / RMS {best['rms_pct']:+.2f}%, 최대 {best['peak_pct']:+.2f}%" if best else '선정 가능한 최적점 없음')
            fluid_note='물 모델'
            if best:best_text+=(f" / 가속도 입력 {best['amplitude_g']:g} g" if best['amplitude_g'] is not None else '')+f", 실제 최대 {best['actual_peak_g']:.6g} g, 수면 처리 {optimization_air}"
            if best:best_text+=f" / 기둥 기울기 {best['tilt']:g}°, 기둥 {best['columns']:g}개"
            if best:best_text+=' / '+best.get('check_status','미확인')+(f" · RMS 차이 {best['check_rms_delta_pp']:+.4g}%p" if best.get('check_rms_delta_pp') is not None else '')
            import textwrap
            caption=fluid_note+'\n'+('중지된 탐색 · 완료된 조합만 표시\n' if context.get('stopped') else '')+fixed_text+'\n'+source_description+'\n'+condition+'\n'+best_text
            fig.suptitle('\n'.join(textwrap.fill(line,width=95) for line in caption.splitlines()),fontsize=8)
            if best:
                rr=traces.get(tuple(best[k] for k in ('beta','angle','B','r','n','amplitude_g','tilt','columns')))
                if rr is not None:
                    trace.plot(rr['t'],rr['state'][:,4]*1000,label='장치 없음')
                    trace.plot(rr['t'],rr['state'][:,0]*1000,label='최적 설계')
                    trace.legend();trace.set(xlabel='시간 (s)',ylabel='지붕 상대변위 (mm)')
            canvas.draw_idle()
        def inspect_cell(event):
            if event.inaxes is not displayed['axes'] or event.xdata is None:return
            points=list(displayed['cells'])
            if not points:return
            context=run_state['context'];xkey,ykey=context['x'],context['y']
            xs=sorted(set(context['grids'][xkey]));ys=sorted(set(context['grids'][ykey]))
            x=min(xs,key=lambda value:abs(value-event.xdata))
            y=min(ys,key=lambda value:abs(value-event.ydata))
            row=displayed['cells'].get((x,y))
            if row is None:
                inspection.set('이 칸에 실제 계산된 조합이 없습니다.');return
            details=' · '.join(f'{labels[k]}={row[k]:.7g}' if row[k] is not None else f'{labels[k]}=미사용' for k in keys)
            score='전체 구간 성능값 없음' if row['rms_pct'] is None else f"RMS {row['rms_pct']:+.4f}% / 최대 {row['peak_pct']:+.4f}%"
            inspection.set(details+' · '+score+f" · {row['status']} · 최적 선정 가능 {row['eligible']} · "+row['reason'])
        canvas.mpl_connect('button_press_event',inspect_cell)
        mode_picker.bind('<<ComboboxSelected>>',lambda _:draw(results) if run_state['context'] else None)
        def start():
            if run_state['running'] or playback['busy']:return
            try:g=grids();rule=peak_rule.get()
            except ValueError as error:feedback.set(str(error));return
            if pending[0]:win.after_cancel(pending[0]);pending[0]=None
            # 계산 시작 시 입력 조건을 복사한다. 이후 결과표·그림·CSV는 이 계산 조건을 참조한다.
            context=dict(x=xvar.get(),y=yvar.get(),fixed={k:float(g[k][0]) if full.get() or k in (xvar.get(),yvar.get()) else float(v.get()) for k,v in fixed.items()},
                grids={k:v.tolist() for k,v in g.items()},full=full.get(),require_peak=rule,
                building=asdict(model),damper=asdict(dam),source=source_description,source_metadata=source_metadata,air_mode=optimization_air,
                excitation_sha256=hashlib.sha256(times.tobytes()+wave.tobytes()).hexdigest(),
                duration_s=float(times[-1]-times[0]),samples=len(times),stopped=False)
            run_state.update(running=True,context=context,progress={})
            run_state['cancel'].clear();lock_inputs()
            def monitor():
                if not win.winfo_exists() or not run_state['running']:return
                p=run_state['progress']
                progress_text.set(f"완료 {p.get('completed',0)} / {p.get('total',0)} · 캐시 재사용 {p.get('reused',0)}"+(' · 중지 요청됨' if run_state['cancel'].is_set() else ''))
                if run_state['running']:win.after(100,monitor)
            monitor()
            def compute():
                # 작업 스레드의 탐색 실행. stop과 progress는 중지 요청·진행 상황 전달에 사용한다.
                rows=search_designs(model,dam,times,wave,g['beta'],g['angle'],g['B'],rule,g['r'],g['n'],memo,
                    stop=run_state['cancel'],progress=run_state['progress'],tilts=g['tilt'],column_counts=g['columns'],air_mode=optimization_air,amplitudes=[float(source_metadata['amplitude_value'])] if amplitude_enabled else None,laboratory=source_metadata if amplitude_enabled else None)
                context['stopped']=run_state['cancel'].is_set()
                if not context['stopped']:
                    check_t,check_a,_=optimization_input(times,wave,source_metadata if amplitude_enabled else None,float(source_metadata['amplitude_value']) if amplitude_enabled else None)
                    quick_verify_best(model,dam,check_t,check_a,rows,optimization_air,run_state['cancel'],verification_memo)
                    context['stopped']=run_state['cancel'].is_set()
                else:
                    for row in rows:row.update(check_status='중지로 미확인',check_rms_delta_pp=None,check_peak_delta_pp=None)
                valid=[row for row in rows if row['eligible']]
                if valid and not context['stopped']:
                    best=valid[0];key=tuple(best[k] for k in ('beta','angle','B','r','n','amplitude_g','tilt','columns'))
                    if key not in traces:
                        mb,dd=search_trial(model,design_variant(dam,best['tilt'],best['columns']),best['B'],best['r'],best['n'])
                        tt,aa,_=optimization_input(times,wave,source_metadata if amplitude_enabled else None,best['amplitude_g'] if amplitude_enabled else None)
                        traces[key]=simulate_space(mb,replace(dd,beta=best['beta'],angle=best['angle']),tt,aa,air_mode=optimization_air)
                return rows
            def display(rows):
                if win.winfo_exists():
                    draw(rows)
                    p=run_state['progress']
                    progress_text.set(f"{'중지됨' if context['stopped'] else '완료'} · 평가 {len(rows)} / {p.get('total',0)} · 캐시 {p.get('reused',0)} · 미계산 {p.get('total',0)-len(rows)}")
            # 계산은 백그라운드에서, 결과 표시와 입력 잠금 해제는 Tkinter 메인 스레드에서 수행한다.
            task(compute,display,on_finish=unlock_inputs)
        def swap():
            x,y=xvar.get(),yvar.get();xvar.set(y);yvar.set(x)
            if run_state['context']:
                run_state['context'].update(x=xvar.get(),y=yvar.get());draw(results)
            else:counts()
        def refine():
            best=best_state[0]
            if best is None:return
            for key in (xvar.get(),yvar.get()):
                step=float(values[key][2].get())/2
                if key in ('n','columns'):step=max(1,int(step))
                center=best[key];lo=center-step;hi=center+step
                if key=='beta':lo=max(.001,lo);hi=min(1.,hi)
                if key=='n':lo=max(1,lo);hi=min(len(model.floor_data()[0]),hi)
                if key in ('r','B'):lo=max(1e-6,lo)
                if key=='angle':lo=max(0,lo);hi=min(180,hi)
                if key=='tilt':lo=max(.01,lo);hi=min(179.99,hi)
                if key=='columns':lo=max(2,lo);hi=min(24,hi)
                for v,value in zip(values[key],(lo,hi,step)):v.set(f'{value:.10g}')
            start()
        def save_csv():
            if not results:return
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.csv')
            if path:
                with open(path,'w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.DictWriter(f,fieldnames=[*results[0],'calculation_context']);writer.writeheader();writer.writerows(dict(row,calculation_context=json.dumps(run_state['context'],ensure_ascii=False)) for row in results)
        def save_png():
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.png',filetypes=[('PNG','*.png')])
            if path:fig.savefig(path,dpi=300,bbox_inches='tight')
        buttons=ttk.Frame(controls);buttons.grid(row=len(keys)+1,column=0,columnspan=5)
        for label,command in [('계산 / 지도 갱신',start),('축 교환',swap),('최적점 주변 정밀 탐색',refine),('CSV 저장',save_csv),('PNG 300 dpi 저장',save_png)]:
            ttk.Button(buttons,text=label,command=command).pack(side='left')
        stop_button=ttk.Button(buttons,text='중지',command=cancel_search,state='disabled');stop_button.pack(side='left')
        for group in values.values():
            for value in group:value.trace_add('write',counts)
        pending=[None]
        def fixed_changed(*_):
            if selecting[0]:return
            counts()
            if pending[0]:win.after_cancel(pending[0])
            if results:
                def refresh_map():
                    if not win.winfo_exists():return
                    if playback['busy']:pending[0]=win.after(300,refresh_map)
                    else:pending[0]=None;draw(results)
                pending[0]=win.after(600,refresh_map)
        for value in fixed.values():value.trace_add('write',fixed_changed)
        for value in (xvar,yvar,full):value.trace_add('write',counts)
        counts()
    def compare():
        if paper_mode.get()=='논문 미확인':
            messagebox.showinfo('논문 조건 미확인','미확인 입력을 지정하고 사용자 실험으로 전환한 뒤 조건 적용을 먼저 누르세요.');return
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        dam=current[0]
        def show(figure):
            status.set('28개 조건 비교 완료')
            win=tk.Toplevel(root);win.title('형상과 설치 각도 비교')
            canvas=FigureCanvasTkAgg(figure,master=win)
            canvas.get_tk_widget().pack(fill='both',expand=True)
            toolbar=NavigationToolbar2Tk(canvas,win);toolbar.update()
            canvas.draw_idle()
        def both():
            return [sweep(b,dam,t,ag,metric=key) for key in ('peak_reduction_vs_bare_pct','rms_reduction_vs_bare_pct')]
        task(both,lambda figures:[show(fig) for fig in figures])
    def angle_window():
        if paper_mode.get()=='논문 미확인':
            messagebox.showinfo('논문 조건 미확인','미확인 입력을 지정하고 사용자 실험으로 전환한 뒤 조건 적용을 먼저 누르세요.');return
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        from matplotlib.figure import Figure
        # 창을 연 시점의 실험 조건을 보관한다. 비교 중에는 설치 각도만 바뀐다.
        dam = current[0]
        wave = ag
        times = t
        fixed_building = b
        setup_plot()
        win = tk.Toplevel(root)
        win.title('설치 각도별 지붕 변위')
        win.geometry('920x670')
        ttk.Label(win, text=f'{source.get()}   |   바닥 관 {dam.B*100:g} cm   ·   물 높이 {dam.h*100:g} cm').pack(anchor='w', padx=14, pady=8)
        controls = ttk.Frame(win)
        controls.pack(fill='x', padx=14)
        ttk.Label(controls, text='진동 방향과 관 사이 각도 (°)').pack(side='left')
        angles_text = tk.StringVar(win, value='0, 45, 90')
        entry = ttk.Entry(controls, textvariable=angles_text, width=25)
        entry.pack(side='left', padx=7)
        feedback = tk.StringVar(win)
        fig = Figure(figsize=(8, 3.8), constrained_layout=True)
        axis = fig.subplots()
        plot = FigureCanvasTkAgg(fig, master=win)
        table = ttk.Treeview(win, columns=('angle','peak','rate','rms'), show='headings', height=5)
        for key, label in [('angle','설치 각도'),('peak','최대 변위 (mm)'),('rate','최대 변위 저감률'),('rms','RMS 변위 저감률')]:
            table.heading(key, text=label)
            table.column(key, width=145, anchor='center')
        memo = {}
        def redraw():
            try:
                angles = sorted(set(float(v.strip()) for v in angles_text.get().split(',')))
                if not 2 <= len(angles) <= 8 or not all(0 <= a <= 180 for a in angles):
                    raise ValueError
            except ValueError:
                feedback.set('0~180 사이의 서로 다른 각도 2~8개를 쉼표로 나눠 입력하세요.')
                return
            if playback['busy']:
                feedback.set('이전 계산이 끝나면 다시 비교를 누르세요.')
                return
            feedback.set('계산 중…')
            def compute():
                # 큰 기록을 여러 번 비교해도 메모리에는 현재 선택만 보관한다.
                return {a: memo[a] if a in memo else simulate_space(fixed_building, replace(dam, angle=a), times, wave) for a in angles}
            def display(results):
                status.set('각도별 비교 완료')
                if not win.winfo_exists(): return
                memo.clear()
                memo.update(results)
                table.delete(*table.get_children())
                axis.clear()
                reference = max(results.values(), key=lambda r: r['n_valid'])
                axis.plot(reference['t'], reference['state'][:,4]*1000, '--', color='#56616b', label='장치 없음', lw=1.1)
                for angle, result in results.items():
                    axis.plot(result['t'], result['state'][:,0]*1000, label=f'{angle:g}°', lw=1.5)
                    m = metrics(result)
                    if m is None:
                        values = ('—', '—', f"{result['failure_time']:.2f}초 수면 한계")
                    else:
                        rate = m['peak_reduction_vs_bare_pct']
                        values = (f"{1000*m['peak_displacement_m'][2]:.2f}", '기준값 0' if rate is None else f'{rate:+.1f}%', '기준값 0' if m['rms_reduction_vs_bare_pct'] is None else f"{m['rms_reduction_vs_bare_pct']:+.2f}%")
                    table.insert('', 'end', values=(f'{angle:g}°', *values))
                table.configure(height=len(angles))
                axis.set(xlabel='시간 (초)', ylabel='지진 방향 지붕 변위 (mm)', xlim=(times[0],times[-1]))
                axis.grid(alpha=.2)
                axis.legend(ncol=min(5,len(angles)+1))
                plot.draw()
                feedback.set('각 실선은 해당 각도의 TLCD입니다. 양의 저감률은 흔들림이 줄었다는 뜻이에요.')
            task(compute,display)
        ttk.Button(controls, text='그래프 비교', command=redraw).pack(side='left')
        entry.bind('<Return>', lambda _: redraw())
        ttk.Label(win, textvariable=feedback).pack(anchor='w', padx=14, pady=5)
        table.pack(side='bottom', fill='x', padx=14, pady=8)
        toolbar = NavigationToolbar2Tk(plot, win, pack_toolbar=False)
        toolbar.pack(side='bottom', fill='x')
        plot.get_tk_widget().pack(fill='both', expand=True)
        redraw()

    def remember():
        dam,r=current
        if any(previous is r for _,previous in history):
            status.set('이미 담긴 실험이에요. 조건을 바꾸고 적용하세요.');return
        m=r['source']
        excitation=(f"실험실 {m['harmonic_hz']:g} Hz · 진폭 {m['site_pga_g']:g} g" if m.get('wave')=='단방향'
            else f"진원 ({m['east']:g}, {m['north']:g}, 깊이 {m['depth']:g}) km · 기준 {m['strength']:g} g")
        name=(f"실험 {len(history)+1}  |  ω 건물 {2*math.pi*b.frequency:.2f} / 물 {2*math.pi*dam.frequency:.2f} rad/s  |  {excitation}"
              f"  ·  관 {m['heading_deg']:g}°"
              f"  ·  길이/물높이/지름 {dam.B*100:g}/{dam.h*100:g}/{dam.diameter*100:g} cm  ·  개구비 {dam.beta:g}")
        mode=shape_label(dam) if r.get('installed',True) else '관 없음'
        if mode=='관 없음': name=f"실험 {len(history)+1} | {excitation} · 건물 {2*math.pi*b.frequency:.2f} rad/s"
        if dam.separate_u and r.get('installed',True):
            _,bores,_,_,tops=u_dimensions(dam)
            name+=' · 기둥 안지름/높이(cm) '+', '.join(f'{w*100:g}/{h*100:g}' for w,h in zip(bores,tops))
        history.append((m['wave']+f" · {r['floors_x'].shape[1]}층 건물 · 설치 {r['mount']}층 · "+mode+' · '+name,r))
        status.set(f'실험 {len(history)} 저장됨 · 실험 그래프 비교에서 선택하세요.')

    def history_window(floor_view=False):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
        from matplotlib.figure import Figure
        if not any(rr is current[1] for _,rr in history): remember()
        setup_plot()
        win=tk.Toplevel(root);win.title('실험 그래프 비교');win.geometry('1040x700')
        book=ttk.Notebook(win);book.pack(fill='both',expand=True)
        page=ttk.Frame(book);detail=ttk.Frame(book)
        report=ttk.Frame(book);book.add(report,text='X·Y 층별 / 크기 비교')
        report_columns=('experiment','direction','floor','rms','peak','drift','mass','fx','fy','roof_peak','roof_rms')
        table=ttk.Treeview(report,columns=report_columns,show='headings')
        for key,title in zip(report_columns,['실험','방향','층','RMS 저감 %','최대 저감 %','최대 층간비 %','총질량 kg','X 1차 Hz','Y 1차 Hz','지붕 최대 m','지붕 RMS m']):
            table.heading(key,text=title);table.column(key,width=100)
        scrollbar=ttk.Scrollbar(report,orient='horizontal',command=table.xview)
        table.configure(xscrollcommand=scrollbar.set);scrollbar.pack(side='bottom',fill='x');table.pack(fill='both',expand=True)
        for index,(_,run) in enumerate(history,1):
            spec=run['building_spec'];info=building_summary(spec,run)
            co,si=np.cos(np.radians(spec.bearing)),np.sin(np.radians(spec.bearing))
            for direction,active,base in [('X',run['floors_x']*co-run['floors_y']*si,run['floor_bare']*co-run['floor_bare_y']*si),
                                          ('Y',run['floors_x']*si+run['floors_y']*co,run['floor_bare']*si+run['floor_bare_y']*co)]:
                for floor in range(active.shape[1]):
                    ar=rms(active[:,floor],run['t']) if run['valid'] else None
                    br=rms(base[:,floor],run['t'])
                    peak=np.max(abs(active[:,floor])) if run['valid'] else None
                    bp=np.max(abs(base[:,floor]))
                    drift=np.nanmax(abs(active[:,floor]-(active[:,floor-1] if floor else 0)))/run['story_height'][floor]*100 if run['valid'] else None
                    values=[index,direction,floor+1,100*(1-ar/br) if ar is not None and br>1e-12 else None,100*(1-peak/bp) if peak is not None and bp>1e-12 else None,drift,info['total_mass'],info['fx'],info['fy'],info['peak_m'],info['rms_m']]
                    table.insert('','end',values=['—' if v is None else f'{v:.5g}' if isinstance(v,float) else v for v in values])
        book.add(page,text='실험 그래프');book.add(detail,text='U형 설계 · 모드 분석')
        ttk.Label(page,text='함께 볼 실험을 클릭하세요. 다시 클릭하면 선택이 풀려요.').pack(anchor='w',padx=12,pady=5)
        items=tk.Listbox(page,selectmode='multiple',exportselection=False,height=5)
        items.pack(fill='x',padx=12)
        rows=list(history)
        for label,_ in rows: items.insert('end',label)
        items.select_set(max(0,len(rows)-3),'end')
        bar=ttk.Frame(page);bar.pack(fill='x',padx=12,pady=5)
        options=['건물 변위','건물 가속도','물 높이 변화','옆 방향 변위','지면 입력 가속도','장치 없는 건물 변위','고정 질량 건물 변위']
        options+=['층별 상대변위','층별 절대가속도','층간변위비','층별 가속도 RMS']
        compare_metrics=[(key,stat) for key in ('변위','절대가속도','층간변위') for stat in ('RMS','최대')]
        options.extend(f'{key} {stat} 저감률 (%)' for key,stat in compare_metrics)
        var=tk.StringVar(value=options[7] if floor_view else options[0])
        picker=ttk.Combobox(bar,textvariable=var,values=options,state='readonly',width=24)
        picker.pack(side='left')
        floor_number=tk.StringVar(value='1')
        ttk.Label(bar,text='측정 층').pack(side='left',padx=(10,2))
        floor_pick=ttk.Combobox(bar,textvariable=floor_number,state='readonly',width=4,
            values=list(range(1,max(r['floors_x'].shape[1] for _,r in rows)+1)))
        floor_pick.pack(side='left')
        fig=Figure(figsize=(9,4.3),constrained_layout=True)
        ax=fig.subplots();canvas=FigureCanvasTkAgg(fig,master=page)
        toolbar=NavigationToolbar2Tk(canvas,page,pack_toolbar=False);toolbar.pack(side='bottom',fill='x')
        note=tk.StringVar();ttk.Label(page,textvariable=note,wraplength=900).pack(side='bottom',fill='x',padx=12)
        canvas.get_tk_widget().pack(fill='both',expand=True)
        def redraw(*_):
            ax.clear();ax.set_facecolor('#f5f8fa')
            kind=options.index(var.get());unit='g' if kind in (1,4) else 'mm'
            peaks=[]
            selection=items.curselection()
            for j in selection:
                _,r=rows[j]
                if kind>=7:
                    k=int(floor_number.get())-1;nf=r['floors_x'].shape[1]
                    name=f"{j+1} · {r['source']['wave']}"
                    if kind>=11:
                        metric,stat=compare_metrics[kind-11]
                        if not r['valid']:
                            peaks.append(name+' · 수면 한계로 제외');continue
                        base,active=r['floor_bare'],r['floors_x']
                        if metric=='절대가속도':base,active=r['floor_bare_acc'],r['floors_acc']
                        elif metric=='층간변위':
                            base=np.diff(base,axis=1,prepend=0.0)
                            active=np.diff(active,axis=1,prepend=0.0)
                        measure=lambda x:rms(x,r['t']) if stat=='RMS' else np.max(abs(x),axis=0)
                        reference=measure(base)
                        ratio=np.full(nf,np.nan)
                        np.divide(measure(active),reference,out=ratio,where=reference>0)
                        percent=100*(1-ratio)
                        ax.plot(np.arange(nf)+1,percent,marker='o',label=name)
                        if k>=nf:summary_value='층 없음'
                        elif np.isfinite(percent[k]):summary_value=f'{percent[k]:+.2f}%'
                        else:summary_value='기준 응답 0'
                        peaks.append(f'{name} · {k+1}층 {summary_value}')
                        continue
                    if kind==10:
                        if not r['valid']:peaks.append(name+' · 수면 한계');continue
                        ax.plot(np.arange(nf)+1,rms(r['floors_acc'],r['t']),marker='o',label=name)
                        continue
                    if k>=nf:peaks.append(name+f' · {k+1}층 없음');continue
                    if kind==7:yy=r['floors_x'][:,k]*1000;unit='mm'
                    elif kind==8:yy=r['floors_acc'][:,k];unit='m/s²'
                    else:
                        yy=(r['floors_x'][:,k]-(r['floors_x'][:,k-1] if k else 0))/r['story_height'][k]*100
                        unit='%'
                    ax.plot(r['t'],yy,label=f'{name} · {k+1}층')
                    peaks.append(f'{name}  {np.nanmax(abs(yy)):.3g} {unit}'+(' · 중단 전' if not r['valid'] else ''))
                    continue
                if kind==4: yy=r['ag']/G
                elif kind==1: yy=r['acc'][:,2]/G
                elif kind==3: yy=r['lateral'][:,0]*1000
                else: yy=r['state'][:,{0:0,2:2,5:4,6:6}[kind]]*1000
                if kind==2 and not r.get('installed',True):
                    peaks.append(f'실험 {j+1} · 관 없음');continue
                ax.plot(r['t'],yy,label=f"{r['source']['wave']} · 실험 {j+1} · {'관 있음' if r.get('installed',True) else '관 없음'}",lw=1.7)
                if r['valid'] or kind==4: peaks.append(f'실험 {j+1}   {np.nanmax(np.abs(yy)):.3g} {unit}')
                else: peaks.append(f"실험 {j+1}   {r['failure_time']:.2f}초 수면 한계")
            if kind>=10:
                max_floor=max((rows[j][1]['floors_x'].shape[1] for j in selection),default=1)
                ax.set(xlabel='측정 층',ylabel=var.get() if kind>=11 else '절대가속도 RMS (m/s²)',xticks=range(1,max_floor+1))
            else:ax.set(xlabel='입력 시작 후 시간 (초)',ylabel=f'{var.get()} ({unit})')
            ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#d6e2e7')
            if ax.lines: ax.legend(ncol=min(3,len(ax.lines)))
            if kind>=11:ax.axhline(0,color='#657780',lw=.8)
            note.set(('장치 없음 대비 · 양수는 감소, 음수는 증가   |   ' if kind>=11 else '층별 RMS   ' if kind==10 else '최대 절댓값   ')+'     |     '.join(peaks))
            canvas.draw_idle()
        detail_bar=ttk.Frame(detail);detail_bar.pack(fill='x',padx=8,pady=4)
        labels=[label for label,_ in rows]
        trial=ttk.Combobox(detail_bar,values=labels,state='readonly',width=55)
        trial.pack(side='left');trial.current(len(rows)-1)
        ttk.Label(detail,text='선택한 실험의 건물과 지반 입력으로, 진동 방향에 나란한 기준 U형과 코드 상단의 U형 설계들을 비교합니다.').pack(anchor='w',padx=8)
        display=ttk.Frame(detail);display.pack(fill='both',expand=True)
        def analyze():
            selected=trial.current()
            def ready(result):
                if not win.winfo_exists():return
                for widget in display.winfo_children():widget.destroy()
                show_multistory(display,result)
                status.set('층별 설계 비교 완료')
            task(lambda:calculate_multistory(rows[selected][1]),ready)
        ttk.Button(detail_bar,text='선택한 실험으로 분석',command=analyze).pack(side='left',padx=6)
        def sync():
            for label,r in history[len(rows):]:
                rows.append((label,r));items.insert('end',label);items.select_set('end')
            trial.configure(values=[label for label,_ in rows])
            floor_pick.configure(values=list(range(1,max(r['floors_x'].shape[1] for _,r in rows)+1)))
            redraw()
        ttk.Button(bar,text='새로 담은 실험 가져오기',command=sync).pack(side='left',padx=7)
        floor_pick.bind('<<ComboboxSelected>>',redraw)
        items.bind('<<ListboxSelect>>',redraw);picker.bind('<<ComboboxSelected>>',redraw);redraw()

    def model_info():
        messagebox.showinfo('실험 모델',
            '모양 선택만 바꾸면 물 총부피와 빈 관 질량이 유지됩니다. 바닥 총길이 B를 가지에 나누고, 기준 U형 물 높이 h의 두 배를 모든 다리에 나눕니다. 기둥 기울기는 수평 기준입니다. 피자 거치대는 같은 각도 간격의 방사형 3~24기둥, 다기둥형은 일렬 2~24기둥입니다. h는 실제 수면 높이가 아닌 기준 U형 환산 물량값이며 실제 기둥별 수면은 형상에 따라 계산합니다. 기둥 안지름을 바꾸면 물의 양을 유지하도록 정지 수면을 다시 계산합니다. 그림의 차단판 효과는 손실계수로 근사합니다.\n\n'
            '진원 좌표는 건물을 기준으로 입력합니다. 가상 지진은 진원에서 건물로 향하는 수평선 방향으로 흔들린다고 가정합니다. 바로 아래 진원은 동쪽을 기준으로 사용합니다.\n\n'
            '세기는 진원 거리 10 km에서의 최대 가속도(g)입니다. 같은 파형에 거리 계수 √101 / √(거리²+1)을 곱합니다(거리 단위 km). 모든 기록은 진동 도착 시점부터 비교합니다. 실제 지반, 지진 규모, 파의 도착시간은 계산 범위 밖입니다.\n\n'
            '입력 적용 안내 · 물높이 h는 물 질량·관 안지름·B로 자동 계산합니다. 직접 강성 모드의 건물 omega는 결과 표시용입니다. 단방향 가진에서는 진원/세기 입력을 사용하지 않습니다.\n\n물 모델은 오리피스 손실과 명시한 추가 관 손실을 사용하며, 비정상 점성 이력은 미포함입니다. 분기관과 비대칭 관에서 경험식 적용 범위는 검증되지 않았습니다.\n\n물은 관을 따라 움직이는 한 물기둥으로 계산합니다. 물의 관성, 두 수면 높이 차에 따른 중력, 유속의 제곱에 비례하는 저항이 들어갑니다. 3D 화면은 이 계산값을 보여줍니다.\n\n건물은 선형 전단 모형으로 비틀림, 전도 회전, 소성 및 지반-기초 상호작용은 포함하지 않습니다. 물의 기포, 부분 충수, 접합부 3차원 흐름은 계산 범위 밖입니다. 이 효과의 계수와 구조 자료 없이 실제 응답을 보정했다고 주장할 수 없습니다.')
    ttk.Button(precision_page,text='층별 최대·RMS 가속도 표',command=acceleration_window).pack(fill='x')
    ttk.Button(precision_page,text='주 실험실 주파수 응답',command=frequency_window).pack(fill='x')
    ttk.Label(precision_page,textvariable=paper_mode).pack(anchor='w')
    ttk.Button(precision_page,text='Tanveer 2019 알려진 조건 적용',command=lambda:apply_tanveer()).pack(fill='x')
    ttk.Button(precision_page,text='사용자 실험으로 전환',command=lambda:paper_mode.set('사용자 실험')).pack(fill='x')
    def fair_window():
        """공정 비교 창: 모양마다 r·β·B를 따로 최적화한 최선끼리 가진 4종·건물 ±10%로 비교한다."""
        if not current[1].get('installed',True):
            messagebox.showinfo('공정 비교','관을 설치한 상태에서 조건 적용 후 실행하세요.');return
        import threading,csv
        dam=current[0];model=b
        win=tk.Toplevel(root);win.title('공정 비교 · 모양별 최적 설계 비교');win.geometry('1080x760')
        top=ttk.Frame(win,padding=8);top.pack(fill='x')
        ttk.Label(top,text='같은 건물·물 질량·손실·수면 처리·가진으로, 모양마다 조율비 r·개구비 β·수평 길이 B를 따로 최적화한 뒤 최선끼리 비교합니다.',wraplength=1040).grid(row=0,column=0,columnspan=8,sticky='w')
        ttk.Label(top,text=f'고정 조건: 건물 1차 {tuning_frequency(model):.4g} Hz · 물 {dam.mass:.4g} kg · 손실 '+(f'직접 ξ {dam.xi:g}' if dam.xi is not None else f'β 탐색 + 추가 손실 {dam.pipe_loss:g}')+f' · 수면 처리 {air_mode_var.get()}',wraplength=1040,foreground='#30566a').grid(row=1,column=0,columnspan=8,sticky='w')
        picks={};params={}
        row=ttk.LabelFrame(top,text='비교할 모양 (U형은 기준으로 항상 포함)',padding=6);row.grid(row=2,column=0,columnspan=8,sticky='we',pady=4)
        picks['U형']=tk.BooleanVar(value=True)
        ttk.Checkbutton(row,text='U형 (기준)',variable=picks['U형'],state='disabled').pack(side='left',padx=4)
        for key,label,extra in [('기울인 U형','기울인 U형  기울기° (90 초과=안쪽)','60'),('다기둥형','일렬형  기둥 수','3'),('피자 거치대','방사형(피자)  기둥 수','3'),('비대칭 U형','비대칭 U형  지름비','1.4')]:
            picks[key]=tk.BooleanVar(value=key in ('기울인 U형','다기둥형','비대칭 U형'))
            ttk.Checkbutton(row,text=label,variable=picks[key]).pack(side='left',padx=(10,2))
            if extra is not None:
                params[key]=tk.StringVar(value=extra);ttk.Entry(row,textvariable=params[key],width=5).pack(side='left')
        grid=ttk.Frame(top);grid.grid(row=3,column=0,columnspan=8,sticky='w',pady=4)
        wave_var=tk.StringVar(value='엘센트로 지진');metric_var=tk.StringVar(value='RMS 변위 저감')
        ttk.Label(grid,text='최적화 가진').grid(row=0,column=0,sticky='w')
        ttk.Combobox(grid,textvariable=wave_var,values=list(FAIR_EXCITATIONS),state='readonly',width=14).grid(row=0,column=1,padx=4)
        ttk.Label(grid,text='선정 기준').grid(row=0,column=2,sticky='w')
        ttk.Combobox(grid,textvariable=metric_var,values=['RMS 변위 저감','최대 변위 저감'],state='readonly',width=14).grid(row=0,column=3,padx=4)
        ranges={}
        for i,(key,label,values) in enumerate([('r','조율비 r (시작·끝·간격)',('0.90','1.04','0.02')),('beta','개구비 β (시작·끝·간격)',('0.2','1.0','0.1'))]):
            ttk.Label(grid,text=label).grid(row=1+i,column=0,columnspan=2,sticky='w')
            ranges[key]=[tk.StringVar(value=v) for v in values]
            for j,var in enumerate(ranges[key]):ttk.Entry(grid,textvariable=var,width=7).grid(row=1+i,column=2+j,padx=2)
        if dam.xi is not None:
            ttk.Label(grid,text='직접 ξ 모드: β는 탐색하지 않습니다.',foreground='#a33').grid(row=2,column=5,sticky='w')
        lengths_var=tk.StringVar(value=', '.join(f'{dam.B*100*x:.3g}' for x in (.8,1.,1.2)))
        ttk.Label(grid,text='수평 길이 B 후보 (cm, 쉼표)').grid(row=3,column=0,columnspan=2,sticky='w')
        ttk.Entry(grid,textvariable=lengths_var,width=24).grid(row=3,column=2,columnspan=3,sticky='w',padx=2)
        height_var=tk.StringVar(value='');amp_var=tk.StringVar(value='0.01');all_var=tk.BooleanVar(value=True)
        ttk.Label(grid,text='관 높이 제한 (cm, 빈칸=없음)').grid(row=4,column=0,columnspan=2,sticky='w')
        ttk.Entry(grid,textvariable=height_var,width=7).grid(row=4,column=2,padx=2)
        ttk.Label(grid,text='공진 사인 진폭 (g)').grid(row=4,column=3,columnspan=2,sticky='e')
        ttk.Entry(grid,textvariable=amp_var,width=7).grid(row=4,column=5,padx=2)
        ttk.Checkbutton(grid,text='가진 4종을 모두 끝까지 견디는 설계만 선정 (권장)',variable=all_var).grid(row=5,column=0,columnspan=6,sticky='w')
        estimate=tk.StringVar();ttk.Label(top,textvariable=estimate,foreground='#30566a').grid(row=4,column=0,columnspan=8,sticky='w')
        def span(values):
            lo,hi,step=[float(v.get()) for v in values]
            if not all(math.isfinite(x) for x in (lo,hi,step)) or step<=0 or hi<lo:raise ValueError('범위는 시작 ≤ 끝, 간격 > 0으로 입력하세요.')
            count=int(math.floor((hi-lo)/step+1e-9))+1
            if count>200:raise ValueError('한 변수의 후보가 200개를 넘습니다. 간격을 늘리세요.')
            return [round(lo+i*step,10) for i in range(count)]
        def collect():
            ratios=span(ranges['r']);betas=[dam.beta] if dam.xi is not None else span(ranges['beta'])
            if any(x<=0 or x>1 for x in betas):raise ValueError('β는 0 초과 1 이하입니다.')
            lengths=[float(x)/100 for x in lengths_var.get().replace(' ','').split(',') if x]
            if not lengths or any(not math.isfinite(x) or x<=0 for x in lengths):raise ValueError('B 후보를 양수(cm)로 입력하세요.')
            cands=[]
            for key in ('U형','기울인 U형','다기둥형','피자 거치대','비대칭 U형'):
                if not picks[key].get():continue
                p={}
                if key=='기울인 U형':p['tilt']=float(params[key].get())
                if key in ('다기둥형','피자 거치대'):p['columns']=int(float(params[key].get()))
                if key=='비대칭 U형':p['bore_ratio']=float(params[key].get())
                fair_candidate(dam,key,**p)
                cands.append((fair_label(key,**p),key,p))
            mh=float(height_var.get())/100 if height_var.get().strip() else None
            if mh is not None and not mh>0:raise ValueError('높이 제한은 양수(cm)입니다.')
            amp=float(amp_var.get())
            if not amp>0:raise ValueError('공진 사인 진폭은 양수(g)입니다.')
            return cands,ratios,betas,lengths,mh,amp
        def update_estimate(*_):
            try:
                cands,ratios,betas,lengths,_,_=collect()
                per=len(ratios)*len(betas)*len(lengths)
                seconds=sum(per*(.15 if k in ('U형','기울인 U형','비대칭 U형') else 1.)+12*(1 if k in ('U형','기울인 U형','비대칭 U형') else 6) for _,k,_ in cands)
                estimate.set(f'후보 {len(cands)}개 × 설계 {per}개 = {len(cands)*per}개 계산 · 예상 약 {max(1,round(seconds/60))}분 (컴퓨터에 따라 0.5~2배)')
            except (ValueError,TypeError) as error:estimate.set(f'입력 확인: {error}')
        for var in [lengths_var,height_var,amp_var,*ranges['r'],*ranges['beta'],*params.values()]:var.trace_add('write',update_estimate)
        for var in picks.values():var.trace_add('write',update_estimate)
        update_estimate()
        buttons=ttk.Frame(top);buttons.grid(row=5,column=0,columnspan=8,sticky='w',pady=4)
        status_var=tk.StringVar(value='[비교 실행]을 누르세요.')
        text=tk.Text(win,wrap='none',font=('Consolas',10));scroll=ttk.Scrollbar(win,orient='vertical',command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        ttk.Label(win,textvariable=status_var,wraplength=1040).pack(anchor='w',padx=8)
        scroll.pack(side='right',fill='y');text.pack(fill='both',expand=True,padx=8,pady=(0,8))
        state={'job':None,'stop':None,'results':None,'settings':None,'progress':{}}
        def run():
            if state['job'] is not None and not state['job'].done():return
            try:cands,ratios,betas,lengths,mh,amp=collect()
            except (ValueError,TypeError) as error:messagebox.showerror('공정 비교',str(error),parent=win);return
            air=AIR_MODE_KEYS.get(air_mode_var.get(),'stop')
            if air=='off':messagebox.showerror('공정 비교','수면 처리 "판정 끔"은 참고 계산이라 최적 선정에 쓸 수 없습니다. 정밀 또는 근사를 고르세요.',parent=win);return
            metric='rms' if metric_var.get().startswith('RMS') else 'peak'
            state['stop']=threading.Event();state['progress']=progress={}
            state['settings']=dict(optimize_on=wave_var.get(),metric=metric,air_mode=air,max_height=mh,building_hz=tuning_frequency(model),
                water_kg=dam.mass,loss_text=(f'직접 ξ {dam.xi:g}' if dam.xi is not None else f'β 탐색 + 추가 손실 {dam.pipe_loss:g}'),sine_amplitude_g=amp)
            state['job']=pool.submit(fair_comparison,model,dam,cands,wave_var.get(),ratios,betas,lengths,air,metric,mh,amp,progress,state['stop'],all_var.get())
            text.delete('1.0','end');poll()
        def poll():
            job=state['job'];p=state['progress']
            if not job.done():
                status_var.set(f"계산 중… 후보 {p.get('candidate','-')}/{p.get('candidates','-')} {p.get('label','')} · 탐색 {p.get('completed',0)}/{p.get('total',0)}"
                               +(' · 중지 요청됨(현재 설계 끝나면 멈춤)' if state['stop'].is_set() else ''))
                win.after(300,poll);return
            try:state['results']=job.result()
            except Exception as error:status_var.set(f'계산 실패: {error}');return
            text.delete('1.0','end');text.insert('end',fair_report_text(state['results'],state['settings']))
            status_var.set('완료' if not state['stop'].is_set() else '중지됨 · 끝난 후보까지만 표시')
        def stop():
            if state['stop'] is not None:state['stop'].set()
        def save():
            if not state['results']:messagebox.showinfo('공정 비교','먼저 비교를 실행하세요.',parent=win);return
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='공정비교.csv')
            if not path:return
            with open(path,'w',newline='',encoding='utf-8-sig') as file:
                w=csv.writer(file)
                w.writerow(['모양','가진','최대변위저감%','RMS저감%','가속도저감%','물최대cm','물여유%','r','beta','B_cm','h_cm','안지름_cm','높이_cm','물_kg','손실계수','비고'])
                for r in state['results']:
                    bst=r['best'] or {}
                    base=[bst.get('r'),bst.get('beta'),bst.get('B',0)*100 if bst else None,bst.get('h',0)*100 if bst else None,
                          bst.get('diameter',0)*100 if bst else None,bst.get('height',0)*100 if bst else None,bst.get('mass'),bst.get('loss')]
                    if not r['best']:w.writerow([r['label'],'','','','','','',*base,r['note']]);continue
                    for name,s in list(r['scores'].items())+[(f'건물 {int(round((k-1)*100)):+d}% 공진',v) for k,v in r['robust'].items()]:
                        w.writerow([r['label'],name,s['peak'],s['rms'],s['acc'],s['water_cm'],s['margin'],*base,s['note']])
            with open(Path(path).with_suffix('.txt'),'w',encoding='utf-8') as file:file.write(fair_report_text(state['results'],state['settings']))
            status_var.set(f'저장 완료: {path} (+ 같은 이름 .txt)')
        ttk.Button(buttons,text='비교 실행',command=run).pack(side='left')
        ttk.Button(buttons,text='중지',command=stop).pack(side='left',padx=6)
        ttk.Button(buttons,text='결과 저장 (CSV·TXT)',command=save).pack(side='left')
    for label,cmd in [('조건 적용',calculate),('최적 설계 탐색',optimize),('공정 비교 (모양별)',fair_window),('현재 실험 담기',remember),('실험 그래프 비교',history_window),('각도별 그래프 비교',angle_window),('형상 × 각도 비교',compare),('결과 저장',save),('물과 지진 계산 원리',model_info)]:
        parent=quick_actions if label in ('조건 적용','최적 설계 탐색','실험 그래프 비교') else panel
        ttk.Button(parent,text=label,command=cmd).pack(fill='x',pady=3)
    ttk.Separator(panel).pack(fill='x',pady=12)
    ttk.Label(panel,textvariable=summary,justify='left',wraplength=380).pack(anchor='w')
    ttk.Label(panel,textvariable=status,wraplength=205,foreground='#215a72').pack(anchor='w',pady=12)
    play.configure(command=toggle)
    scrub.configure(command=lambda _:draw_scene())
    def stop_scrub(_):
        pause()
        if playback.get('timer'): root.after_cancel(playback['timer'])
    scrub.bind('<ButtonPress-1>',stop_scrub,add='+')
    drag_start=[0,0]
    def orbit(event):
        camera[0]-=(event.x-drag_start[0])*.011
        camera[1]=min(1.20,max(.14,camera[1]+(event.y-drag_start[1])*.009))
        drag_start[:]=[event.x,event.y]
        draw_scene()
    scene.bind('<ButtonPress-1>',lambda e:drag_start.__setitem__(slice(None),[e.x,e.y]))
    scene.bind('<B1-Motion>',orbit)
    def zoom_view(event):
        zoom[0]=np.clip(zoom[0]*(1.12 if event.delta>0 else 1/1.12),.25,5.)
        draw_scene()
    scene.bind('<MouseWheel>',zoom_view)
    scene.bind('<Configure>',draw_scene);chart.bind('<Configure>',draw_chart)
    chooser.bind('<<ComboboxSelected>>',draw_chart)
    floor_selector.bind('<<ComboboxSelected>>',draw_chart)
    pause();refresh();status.set('기본 실험 준비 완료 · ▶ 재생')
    inactive_note=tk.StringVar()
    ttk.Label(settings.master,textvariable=inactive_note,wraplength=380,foreground='#68747e').pack(anchor='w',after=settings)
    def update_context_controls(*_):
        # 입력값은 보존하며 현재 선택에서 사용하지 않는 위젯만 회색 비활성화한다.
        # 계산 중 탐색 창이 잠근 위젯을 여기서 다시 활성화하지 않는다.
        if playback['busy']:return
        installed=pipe_on.get();shape=shape_var.get();laboratory=kind_var.get()=='단방향'
        target=tune_mode.get()
        states={str(damping_var):damping_mode_var.get() in ('강성비례','모드 감쇠'),
            str(c_vars['x']):damping_mode_var.get()=='직접 계수',str(c_vars['y']):damping_mode_var.get()=='직접 계수',
            str(xi_var):installed and loss_mode_var.get()=='직접 ξ',
            str(tilt_var):installed,
            str(column_var):installed and shape in ('다기둥형','피자 거치대'),
            str(cycles_var):laboratory,str(hz_var):laboratory,str(amplitude_var):laboratory,str(amplitude_mode):laboratory,
            str(mount_var):installed,str(tune_mode):installed,
            str(ramp_profile_var):laboratory,str(container_mass_var):installed,str(air_mode_var):installed and (shape=='U형' or (shape=='다기둥형' and column_var.get().strip()=='2')),str(shape_display):installed,str(water_var):installed,str(tube_length_var):installed,
            str(omega_b):stiffness_mode.get()=='목표 X 1차 진동수',
            str(omega_l):installed and target,
            str(floor_fields['m']):not size_link.get()}
        states.update({str(value):not laboratory and kind_var.get()!='CSV 기록' for value in quake_fields.values()})
        for flag,value,unit in ramps.values():
            states[str(flag)]=laboratory;states[str(value)]=laboratory and flag.get();states[str(unit)]=laboratory and flag.get()
        states.update({str(value):installed and key!='h' and not (key=='diameter' and target) for key,value in fields.items()})
        states[str(fields['beta'])]=installed and loss_mode_var.get()=='개구비'
        states[str(pipe_loss_var)]=installed and (loss_mode_var.get()=='개구비' or xi_scope_var.get()=='local')
        states[str(xi_scope_var)]=installed and loss_mode_var.get()=='직접 ξ'
        style=ttk.Style(root)
        for widget_type in ('TEntry','TSpinbox','TCombobox'):
            style.map('Context.'+widget_type,
                fieldbackground=[('disabled','#e5e7eb'),('readonly','#e5e7eb')],
                foreground=[('disabled','#777777'),('readonly','#777777')])
        def visit(parent):
            for widget in parent.winfo_children():
                if isinstance(widget,(ttk.Entry,ttk.Combobox,ttk.Spinbox)):
                    variable=str(widget.cget('textvariable'))
                elif isinstance(widget,ttk.Checkbutton):variable=str(widget.cget('variable'))
                else:variable=None
                if variable in states:
                    widget.state(['!disabled'] if states[variable] else ['disabled'])
                    if isinstance(widget,ttk.Combobox):widget.configure(style='Context.TCombobox')
                    elif isinstance(widget,ttk.Spinbox):widget.configure(style='Context.TSpinbox')
                    elif isinstance(widget,ttk.Entry):widget.configure(style='Context.TEntry')
                if isinstance(widget,ttk.Button) and widget.cget('text')=='U관 기둥별 안지름 · 높이':
                    widget.state(['!disabled'] if installed and shape=='U형' else ['disabled'])
                visit(widget)
        visit(settings)
        notes=['회색 = 현재 미사용/자동 계산. h는 물 질량·B·안지름으로 계산합니다.']
        if laboratory:notes.append('단방향에서는 진원·10 km 세기가 미사용입니다.')
        else:notes.append('지진 기록에서는 실험실 Hz·진폭이 미사용입니다.')
        if size_link.get():notes.append('층별 질량은 기준 면적비로 계산됩니다.')
        if target and installed:notes.append('목표 TLCD ω에 맞춰 h와 안지름을 계산합니다.')
        if not installed:notes.append('관 없음 · 관 설정과 설치 층은 미사용입니다.')
        inactive_note.set(' '.join(notes))
    for selection in (shape_var,kind_var,pipe_on,tune_mode,stiffness_mode,size_link,damping_mode_var,loss_mode_var,xi_scope_var,*[item[0] for item in ramps.values()]):
        selection.trace_add('write',update_context_controls)
    update_context_controls()

    # 입력 문자열과 보조 설정까지 저장하여 다시 열었을 때 같은 조건을 복원한다.
    script=globals().get('__file__')
    settings_path=(Path(script).resolve().parent if script else Path.cwd())/'TLCD_settings.json'
    try:
        saved=read_settings(settings_path)
    except (OSError,ValueError,TypeError) as error:
        saved=dict(version=1,profiles={},last=None)
        messagebox.showwarning('설정 읽기',f'기존 설정을 읽지 못했습니다. 파일을 확인하세요.\n{error}')
    variable_groups={'pipe':fields,'floor':floor_fields,'source':quake_fields}
    variables=dict(freeboard=freeboard_var,xi_scope=xi_scope_var,ramp_profile=ramp_profile_var,container_mass=container_mass_var,damping_mode=damping_mode_var,cx=c_vars['x'],cy=c_vars['y'],loss_mode=loss_mode_var,xi=xi_var,pipe_loss=pipe_loss_var,air_mode=air_mode_var,paper_mode=paper_mode,shape=shape_var,tilt=tilt_var,columns=column_var,count=count_var,mount=mount_var,
        damping=damping_var,width=size_vars[0],depth=size_vars[1],size_link=size_link,
        stiffness_mode=stiffness_mode,water_mass=water_var,tube_length=tube_length_var,wave=kind_var,hz=hz_var,
        amplitude_mode=amplitude_mode,amplitude=amplitude_var,cycles=cycles_var,
        omega_b=omega_b,omega_l=omega_l,tune=tune_mode,ratio=tune_ratio,
        ratio_enabled=ratio_enabled,pipe_on=pipe_on)
    for key,(flag,value,unit) in ramps.items():
        variables.update({key+'_ramp_on':flag,key+'_ramp_value':value,key+'_ramp_unit':unit})
    def snapshot():
        # 현재 화면의 문자열·선택 상태를 그대로 저장한다. 여기서 새 물리 계산을 수행하지 않는다.
        data=dict(values={k:v.get() for k,v in variables.items()},
            groups={name:{k:v.get() for k,v in group.items()} for name,group in variable_groups.items()},
            legs=leg_specs,reference_size=[reference_size[0],reference_size[1],reference_size[2].tolist()])
        data['values']['tilt_version']='3'   # 기울기 칸이 모든 모양의 기둥 기울기(90=수직, 90 초과 안쪽)인 저장 형식
        # 사용자가 불러온 별도 입력 기록은 재실행 후에도 복원할 수 있도록 배열을 함께 저장한다.
        if kind_var.get() not in QUAKE_NOTES:
            time_input,acc_input=wave_cache[kind_var.get()]
            data['custom_wave']=[time_input.tolist(),acc_input.tolist()]
            if kind_var.get()=='CSV 기록':data['csv_metadata']=dict(csv_metadata)
        return data

    def persist_last():
        saved['last']=snapshot()
        try:write_settings(settings_path,saved)
        except (OSError,ValueError) as error:
            messagebox.showwarning('설정 저장',f'자동 저장하지 못했습니다.\n{error}')
    def restore(data):
        nonlocal reference_size
        if playback['busy']:
            messagebox.showinfo('설정','계산이 끝난 뒤 불러오세요.');return
        try:
            # 설정 JSON의 values는 일반 입력, groups는 관·층별·진원 입력 묶음이다.
            values=data['values'];groups=data['groups']
            freeboard_var.set('.12')  # 예전 프로필의 기존 여유 높이 보존
            damping_mode_var.set('강성비례');loss_mode_var.set('개구비');xi_var.set('');xi_scope_var.set('total');pipe_loss_var.set('0');paper_mode.set('사용자 실험')
            for flag,value,unit in ramps.values():flag.set(False)
            if 'csv_metadata' in data:
                csv_metadata.clear();csv_metadata.update(data['csv_metadata'])
                csv_info.set(f"저장된 CSV · {csv_metadata.get('samples','?')}개 · 원본 시작 {csv_metadata.get('original_start_s','?')} s · 단위 {csv_metadata.get('unit','?')}")

            reference=data['reference_size']
            restored_reference=(float(reference[0]),float(reference[1]),np.array(reference[2],float))
            if 'custom_wave' in data:
                wave_cache[values['wave']]=tuple(np.array(x,float) for x in data['custom_wave'])
                presets[values['wave']]='저장한 사용자 입력 기록입니다.'
                kind_box.configure(values=list(presets))
            # 진폭 항목이 없는 예전 설정에도 실행용 기본값을 적용한다.
            amplitude_mode.set('가속도 진폭 (g)');amplitude_var.set('0.01')
            tube_length_var.set('');cycles_var.set('');container_mass_var.set('0');ramp_profile_var.set('quintic');air_mode_var.set(AIR_MODE_LABELS['stop'])
            # 알고 있는 키만 위젯 변수에 복원한다. 오래된 설정에 없는 입력은 현재 기본값을 유지한다.
            for key,value in values.items():
                if key in variables and key!='air_mode':variables[key].set(value)
            # 예전 설정: V형은 U형 + 기둥 기울기로, 그 밖의 형상은 V형 전용이던 경사각을 무시하고 수직(90°)으로 불러온다.
            if values.get('tilt_version') not in ('2','3') and values.get('shape')!='V형':tilt_var.set('90')
            # v19 이전: 기울기는 U형에만 쓰였다. 다른 모양은 수직, 피자 거치대는 3기둥으로 불러온다.
            if values.get('tilt_version') in (None,'2') and values.get('shape') not in ('U형','V형'):tilt_var.set('90')
            if values.get('tilt_version') in (None,'2') and values.get('shape')=='피자 거치대':column_var.set('3')
            if shape_var.get()=='V형':shape_var.set('U형')
            if shape_var.get()=='독립 U관 3개':
                shape_var.set('U형');tilt_var.set('90')
                messagebox.showinfo('설정 불러오기','독립 U관 3개는 v19에서 빠졌습니다. U형으로 불러왔습니다.')
            # 첨부 파일의 이전 공통 램프 주기를 시작·종료 램프 설정으로 변환한다.
            if 'ramp' in values and not any(key in values for key in ('start_ramp_on','end_ramp_on')):
                amount=float(values['ramp'])
                if not np.isfinite(amount) or amount<0:raise ValueError('저장된 램프 주기가 올바르지 않습니다.')
                ramp_profile_var.set('cosine')
                for flag,value,unit in ramps.values():
                    flag.set(amount>0);value.set(str(amount));unit.set('주기')
            for name,group in groups.items():
                for key,value in group.items():
                    if name in variable_groups and key in variable_groups[name]:variable_groups[name][key].set(value)
            leg_specs.clear()
            leg_specs.update({k:tuple(tuple(x) for x in pair) for k,pair in data['legs'].items()})
            ratio_enabled.set(False)
            # 크기 연동의 기준 치수·질량을 함께 복원해 질량 누적 변경을 방지한다.
            reference_size=restored_reference
            wave_note.set(presets[kind_var.get()])
            update_dimension_labels();switch_tune()
            # 복원한 입력을 실제 계산에 적용하는 지점. 성공하면 마지막 적용 설정도 다시 저장된다.
            calculate()
        except (KeyError,TypeError,ValueError) as error:
            messagebox.showerror('설정 불러오기',f'설정 내용을 확인하세요.\n{error}')

    def save_named():
        from tkinter import simpledialog
        if playback['busy']:
            messagebox.showinfo('설정','계산이 끝난 뒤 저장하세요.');return
        name=simpledialog.askstring('설정 저장','설정 이름을 입력하세요.',parent=root)
        if not name or not name.strip():return
        name=name.strip()
        if name in saved['profiles'] and not messagebox.askyesno('설정 저장',f'“{name}” 설정을 덮어쓸까요?'):return
        saved['profiles'][name]=snapshot()
        try:write_settings(settings_path,saved)
        except (OSError,ValueError) as error:messagebox.showerror('설정 저장',str(error));return
        status.set(f'설정 저장 완료 · {name}')
    def load_named():
        window=tk.Toplevel(root);window.title('저장한 설정')
        names=list(saved['profiles'])
        picker=ttk.Combobox(window,values=names,state='readonly',width=40);picker.pack(padx=15,pady=12)
        if names:picker.current(0)
        def load():
            if picker.get() not in saved['profiles']:return
            data=saved['profiles'][picker.get()]
            window.destroy();restore(data)
        ttk.Button(window,text='불러오기',command=load).pack(pady=8)
        ttk.Label(window,text='불러온 설정은 자동으로 조건 적용됩니다.').pack(padx=12,pady=8)
    menu=tk.Menu(root);settings_menu=tk.Menu(menu,tearoff=False)
    def load_stable_example():
        eb,ed=stable_example()
        data=snapshot()
        data['values'].update(shape='U형',tilt='90',columns='4',count='2',mount='2',damping=str(eb.damping),
            width=str(eb.width*100),depth=str(eb.depth*100),freeboard=str(ed.freeboard),size_link=False,stiffness_mode='직접 입력',water_mass=str(ed.mass),
            wave='단방향',hz=f'{eb.frequency:.2f}',amplitude_mode='가속도 진폭 (g)',amplitude='0.01',
            tune=False,ratio_enabled=False,pipe_on=True,tube_length='',cycles='39',container_mass='0',ramp_profile='quintic',
            start_ramp_on=True,start_ramp_value='3',start_ramp_unit='주기',end_ramp_on=True,end_ramp_value='3',end_ramp_unit='주기',
            damping_mode='강성비례',loss_mode='개구비',xi_scope='total',xi='',pipe_loss=f'{ed.pipe_loss:g}',air_mode=AIR_MODE_LABELS['stop'],
            paper_mode='사용자 실험')
        data['groups']['pipe'].update(B=f'{ed.B*100:g}',h=str(ed.h*100),diameter=str(ed.diameter*100),angle='0',beta=f'{ed.beta:g}')
        data['groups']['floor']={'m':','.join(map(str,eb.masses)),'k':','.join(map(str,eb.stories)),'y':','.join(map(str,eb.stories_y)),'h':','.join(map(str,eb.heights))}
        data['legs']={'U형':[[],[]]}
        data['reference_size']=[eb.width,eb.depth,list(eb.masses)]
        restore(data)
    def apply_tanveer():
        from datetime import datetime
        # 먼저 현재 입력을 프로필로 보관한다. 기존 이름 있는 프로필은 덮어쓰지 않는다.
        name='Tanveer 적용 전 '+datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        saved['profiles'][name]=snapshot()
        try:write_settings(settings_path,saved)
        except OSError as error:messagebox.showerror('설정 보존 실패',str(error));return
        pb,pd,report=tanveer_known_conditions();paper_report[0]=report
        data=snapshot()
        data['values'].update(shape='U형',count='4',mount='4',size_link=False,
            stiffness_mode='직접 입력',damping_mode='직접 계수',cx='1.720,1.720,1.720,1.720',cy='1.720,1.720,1.720,1.720',
            water_mass=str(pd.mass),freeboard=str(pd.freeboard),tune=False,ratio_enabled=False,paper_mode='논문 미확인',wave='단방향',hz='',
            amplitude='',xi='',loss_mode='직접 ξ',cycles='',tube_length='')
        for key in ('start','end'):data['values'][key+'_ramp_on']=False
        data['groups']['floor']={'m':'2.2,2.2,2.2,2.2','k':'1505.10,1505.10,1505.10,1505.10','y':'1505.10,1505.10,1505.10,1505.10','h':'.381,.381,.381,.381'}
        data['groups']['pipe'].update(B=str(pd.B*100),h=str(pd.h*100),diameter=str(pd.diameter*100),angle='0')
        data['legs']={'U형':[[],[]]};data['reference_size']=[pb.width,pb.depth,list(pb.masses)]
        restore(data)
        messagebox.showinfo('Tanveer 알려진 조건',json.dumps(report,ensure_ascii=False,indent=2))
    settings_menu.add_command(label='기본 안정 예제 불러오기',command=load_stable_example)
    settings_menu.add_command(label='이름 붙여 설정 저장',command=save_named)
    settings_menu.add_command(label='저장한 설정 불러오기',command=load_named)
    menu.add_cascade(label='설정',menu=settings_menu)
    analysis_menu=tk.Menu(menu,tearoff=False)
    for label,command in [('최적 설계 탐색',optimize),('실험 그래프 비교',history_window),
            ('각도별 그래프 비교',angle_window),('형상 × 각도 비교',compare),
            ('주 실험실 주파수 응답',frequency_window),('층별 가속도 표',acceleration_window),('공정 비교 (모양별)',fair_window)]:
        analysis_menu.add_command(label=label,command=command)
    menu.add_cascade(label='분석',menu=analysis_menu);root.configure(menu=menu)
    if saved.get('last'):root.after(100,lambda:restore(saved['last']))
    root.protocol('WM_DELETE_WINDOW',root.destroy)
    try: root.mainloop()
    finally: pool.shutdown(wait=False,cancel_futures=True)


def floor_force(time):
    """선택 사항. 시간 하나에서 각 층에 가해지는 외력(N)을 n개 반환한다."""
    return np.zeros(N)


def positive(name, value):
    if not np.isfinite(value) or value <= 0:
        raise ValueError(f'{name}은 유한한 양수여야 합니다. 입력값 {value}')


def vector(label, values, size, *, positive_only=False):
    a = np.asarray(values, dtype=float)
    if a.shape != (size,) or not np.isfinite(a).all():
        raise ValueError(f'{label}: 유한한 숫자 {size}개가 필요합니다.')
    if positive_only and np.any(a <= 0):
        raise ValueError(f'{label}: 각 값은 0보다 커야 합니다.')
    return a


# 별도 U형 모드 분석용 M/K/C 조립. 주 GUI의 Building 설정을 직접 변경하지 않는다.
def building():
    if not isinstance(N, int) or N < 1:
        raise ValueError('N은 1 이상의 정수여야 합니다.')
    mass = vector('층별 질량', MASSES, N, positive_only=True)
    stiffness = vector('층간 강성', STIFFNESSES, N, positive_only=True)
    heights = vector('층 높이', HEIGHTS, N, positive_only=True)
    # D @ u = [u1, u2-u1, ...]. 각 층간 스프링의 양 끝에 반대 방향 힘이 걸린다.
    difference = np.eye(N) - np.eye(N, k=-1)
    M = np.diag(mass)
    K = difference.T @ (stiffness[:, None] * difference)
    C = RAYLEIGH_A*M + RAYLEIGH_B*K if CUSTOM_C is None else np.asarray(CUSTOM_C, float)
    if C.shape != (N,N) or not np.isfinite(C).all() or not np.allclose(C, C.T):
        raise ValueError('감쇠행렬 C는 유한한 n×n 대칭 행렬이어야 합니다.')
    if np.linalg.eigvalsh(C).min() < -1e-10*max(1.,np.linalg.norm(C)):
        raise ValueError('감쇠행렬이 에너지를 만드는 음의 감쇠를 포함합니다.')
    return M,K,C,heights


# 대칭 일반화 고유치 문제 K*phi=omega²*M*phi를 풀어 질량 정규화 모드와 참여계수를 반환한다.
def modes(M, K):
    # 대칭 고유치 문제로 변환한 뒤 질량 정규화: phi.T M phi = I.
    root = np.sqrt(np.diag(M))
    squares, normalized = np.linalg.eigh(K / root[:, None] / root[None, :])
    phi = normalized / root[:, None]
    largest = np.argmax(np.abs(phi), axis=0)
    phi *= np.sign(phi[largest, np.arange(len(root))])
    participation = phi.T @ M @ np.ones(len(root))
    return np.sqrt(squares), phi, participation


def designs(omega, install=INSTALL_FLOOR, locations=FLOORS):
    N=len(omega)
    positive('중력가속도', G)
    positive('관 여유 높이', FREEBOARD)
    def make(code, floor, inputs):
        if not isinstance(floor, (int,np.integer)) or not 1 <= floor <= N:
            raise ValueError(f'{code}: 설치 층은 1~{N} 사이의 정수여야 합니다.')
        p = dict(inputs)
        for key in ['L','B','A','rho']:
            positive(f'{code}: {key}',p[key])
        if p['B'] >= p['L'] or not 0<p['beta']<=1:
            raise ValueError(f'{code}: B < L, Ao ≤ A여야 합니다.')
        p['Ao']=p['A']*p['beta']
        p['xi']=orifice_loss(p['beta'])+Damper.pipe_loss
        return dict(p,code=code,floor=int(floor),mf=p['rho']*p['A']*p['L'],
                    alpha=p['B']/p['L'],kf=2*p['rho']*G*p['A'],wf=math.sqrt(2*G/p['L']))
    ref = make('REF', install, REFERENCE)
    result = [ref]
    positive('사용자 설계 액체 밀도',CUSTOM_DENSITY)
    def area(L):
        positive('액체 길이',L)
        return ref['mf']/(CUSTOM_DENSITY*L) if KEEP_WATER_MASS else CUSTOM_AREA
    for idx,(j,L,B,beta) in enumerate(itertools.product(locations,L_VALUES,B_VALUES,BETA_VALUES),1):
        result.append(make(f'D{idx:02d}',j,dict(L=L,B=B,A=area(L),beta=beta,rho=CUSTOM_DENSITY)))
    for mode in TUNE_TO_MODES:
        if not isinstance(mode,int) or not 1 <= mode <= N:
            raise ValueError(f'조율 대상 모드 번호는 1~{N}입니다.')
        L = 2*G/omega[mode-1]**2
        for j in dict.fromkeys(locations):
            result.append(make(f'M{mode}F{j}',j,dict(L=L,B=ref['alpha']*L,A=area(L),
                beta=ref['beta'],rho=CUSTOM_DENSITY)))
    return result


# 별도 한 방향 U형 모델의 결합 M/K/C, 가진 방향 벡터, 비선형 저항계수를 구성한다.
def system(M,K,C,p):
    if p is None:
        return M,K,C,np.ones(len(M)),0.
    n=len(M)
    Mc=np.zeros((n+1,n+1))
    Kc=np.zeros_like(Mc)
    Cc=np.zeros_like(Mc)
    Mc[:n,:n], Kc[:n,:n], Cc[:n,:n] = M,K,C
    j=p['floor']-1
    Mc[j,j]+=p['mf']
    Mc[j,-1]=Mc[-1,j]=p['alpha']*p['mf']
    Mc[-1,-1]=p['mf']
    Kc[-1,-1]=p['kf']
    # q=[각 층의 지반 기준 변위 u, 관에 대한 액체 변위 y].
    # 통째로 지면과 이동할 때 관 내부의 상대 변위는 0. 하중은 -Mc@[1,...,1,0]*ag.
    # 마지막 성분에도 -alpha*mf*ag가 들어간다.
    influence=np.r_[np.ones(n),0.]
    # 관 평균 유속 기준 오리피스 손실만 고려. beta는 무차원 면적 개구비.
    drag=.5*p['rho']*p['A']*(orifice_loss(p['beta'])+Damper.pipe_loss)   # 관 기본 손실 포함
    return Mc,Kc,Cc,influence,drag


def grid(duration,dt):
    positive('지속 시간',duration);positive('시간 간격',dt)
    return np.linspace(0,duration,max(1,math.ceil(duration/dt))+1)


def record_input(t, base_path):
    acc=np.zeros_like(t)
    if HARMONIC_ON:
        positive('조화 가진 주파수',HARMONIC_HZ)
        if not np.isfinite(AMPLITUDE) or AMPLITUDE<0:raise ValueError('가속도 진폭은 0 이상이어야 합니다.')
        acc+=AMPLITUDE*np.sin(2*np.pi*HARMONIC_HZ*t)
    if GROUND_CSV:
        path=base_path/Path(GROUND_CSV)
        data=np.genfromtxt(path,delimiter=',',names=True,encoding='utf-8-sig',ndmin=1)
        if data.dtype.names!=('time_s','accel_m_s2') or len(data)<2:
            raise ValueError('지반 CSV는 time_s,accel_m_s2 열과 2행 이상의 기록이 필요합니다.')
        tr,ar=data['time_s'],data['accel_m_s2']
        if not np.isfinite(tr).all() or not np.isfinite(ar).all() or np.any(np.diff(tr)<=0):
            raise ValueError('CSV 시간이 증가해야 하며 시간과 가속도에 결측값이 없어야 합니다.')
        tr=tr-tr[0]
        if t[-1]>tr[-1]+1e-10:
            raise ValueError(f'CSV는 {tr[-1]:g}초까지 있습니다. DURATION을 줄이세요.')
        # 원본의 짧은 피크도 유지하도록 기록 시각을 적분/출력 격자에 포함한다.
        t=np.unique(np.r_[t,tr[tr<=t[-1]]])
        acc=np.interp(t,tr,ar)
        if HARMONIC_ON: acc+=AMPLITUDE*np.sin(2*np.pi*HARMONIC_HZ*t)
    forces=np.array([vector('층별 외력',floor_force(float(ti)),N) for ti in t])
    return t,acc,forces


# 별도 U형 분석의 암시적 중점 적분. 주 GUI의 network_response()와 진입점이 다르다.
def integrate(model,p,t,ag,forces,*,rest=False):
    """암시적 중점법. 가진 선형 보간, 비선형 손실은 매 내부 단계에서 풀어낸다."""
    N=len(model[0])
    M,K,C,_=model
    M,K,C,r,drag=system(M,K,C,p)
    dim=len(M)
    positive('내부 계산 간격',MAX_INTERNAL_DT)
    factor=np.linalg.cholesky(M)
    reduced=np.linalg.solve(factor,K)
    reduced=np.linalg.solve(factor,reduced.T).T
    fastest=math.sqrt(np.linalg.eigvalsh(reduced).max())
    maxdt=min(MAX_INTERNAL_DT,2*np.pi/(INTERNAL_POINTS_PER_PERIOD*fastest))
    q=np.zeros(dim);v=np.zeros(dim)
    if not rest:
        q[:N]=vector('초기 변위',np.zeros(N) if U0 is None else U0,N)
        v[:N]=vector('초기 속도',np.zeros(N) if V0 is None else V0,N)
        if p:q[-1],v[-1]=WATER_Y0,WATER_V0
    if not np.isfinite(q).all() or not np.isfinite(v).all():
        raise ValueError('초기조건에 유한한 수를 입력하세요.')
    limit=min(FREEBOARD,(p['L']-p['B'])/2) if p else np.inf
    if p and abs(q[-1])>=limit: raise ValueError(f"{p['code']}: 초기 액면이 관의 사용 범위를 벗어납니다.")
    loads=-ag[:,None]*(M@r)
    loads[:,:N]+=forces
    Q=np.full((len(t),dim),np.nan);V=Q.copy()
    Q[0],V[0]=q,v
    last_h=None;stop=None
    for i,span in enumerate(np.diff(t),1):
        steps=max(1,math.ceil(span/maxdt-1e-10));dt=span/steps;h=dt/2
        if last_h is None or not math.isclose(last_h,h,rel_tol=1e-11,abs_tol=0):
            inv=np.linalg.solve(M+h*C+h*h*K,np.eye(dim))
            ev=inv@M;eq=-h*inv@K;ef=h*inv
            if p: loss=ef[:,-1]*drag
            last_h=h
        delta=loads[i]-loads[i-1]
        for j in range(steps):
            fm=loads[i-1]+(j+.5)/steps*delta
            mid=ev@v+eq@q+ef@fm
            if p:
                # 유체 중점 속도 w + loss[-1]*|w|w = mid[-1]의 안정적인 닫힌 해.
                w=2*mid[-1]/(1+math.sqrt(1+4*loss[-1]*abs(mid[-1])))
                mid-=loss*(abs(w)*w)
            old_q=q;old_v=v
            q=q+dt*mid;v=2*mid-v
            if p and abs(q[-1])>=limit:
                stop=float(t[i-1]+(j+1)*dt);break
        if stop is not None:break
        Q[i],V[i]=q,v
    residual=loads-Q@K.T-V@C.T
    if p:residual[:,-1]-=drag*np.abs(V[:,-1])*V[:,-1]
    # 절대가속도 = 상대가속도 + 지반가속도. 수치 미분 대신 힘의 평형식 사용.
    absolute=np.linalg.solve(M,residual.T).T[:,:N]+ag[:,None]
    u=Q[:,:N]
    drift=np.diff(u,axis=1,prepend=np.zeros((len(t),1)))
    return dict(u=u,acc=absolute,drift=drift,ratio=drift/model[3],
                water=Q[:,-1] if p else None,stop=stop)


def rms(x,t):
    return np.sqrt(np.trapezoid(x*x,t,axis=0)/(t[-1]-t[0]))


def reduction(base,value):
    if base<=1e-14:return None
    return float(100*(1-value/base))


def multistory_metrics(t,ref,r,code):
    N=ref["u"].shape[1]
    rows=[dict(design=code,floor=i+1,status='정상' if r['stop'] is None else '수면 한계',
               stop_s=r['stop'],peak_water_m=None if r['water'] is None or r['stop'] is not None else float(np.max(abs(r['water'])))) for i in range(N)]
    for key,unit in [('u','m'),('acc','m_s2'),('drift','m'),('ratio','1')]:
        baseline=rms(ref[key],t)
        valid=r['stop'] is None
        val=rms(r[key],t) if valid else None
        for i,row in enumerate(rows):
            row[f'{key}_baseline_peak_{unit}']=np.max(abs(ref[key][:,i]))
            row[f'{key}_peak_{unit}']=np.max(abs(r[key][:,i])) if valid else None
            row[f'{key}_baseline_rms_{unit}']=baseline[i]
            row[f'{key}_rms_{unit}']=val[i] if valid else None
            pct=reduction(baseline[i],val[i]) if valid else None
            row[f'{key}_rms_reduction_pct']=pct
            row[f'{key}_change']='정의 불가' if pct is None else ('증가' if pct< -1e-8 else '감소' if pct>1e-8 else '동일')
    return rows


def sweep_group(model, entries, time, ground, steps, window_start):
    """같은 내부 간격을 쓰는 설계를 한꺼번에 적분하고 측정 구간만 보관한다."""
    # 마지막 축은 유체 좌표. 맨 건물에는 독립된 정지 좌표를 덧붙여 배열 크기를 맞춘다.
    N=len(model[0])
    dim = N+1
    dt = (time[1]-time[0])/steps
    half = dt/2
    coeffs = []
    for code,p,(M,K,C,r,drag) in entries:
        if p is None:
            M=np.pad(M,((0,1),(0,1))); M[-1,-1]=1.
            K=np.pad(K,((0,1),(0,1))); C=np.pad(C,((0,1),(0,1))); r=np.r_[r,0.]
        inv=np.linalg.solve(M+half*C+half**2*K,np.eye(dim))
        coeffs.append((inv@M,-half*inv@K,-half*inv@(M@r),half*drag*inv[:,-1],M,K,C,drag))
    ev,eq,forcing,loss,M,K,C,drag=map(np.asarray,zip(*coeffs))
    limits=np.array([min(FREEBOARD,(p['L']-p['B'])/2) if p else np.inf for _,p,_ in entries])
    q=np.zeros((len(entries),dim)); v=np.zeros_like(q)
    Q=np.empty((len(entries),len(time)-window_start,dim));V=np.empty_like(Q)
    if window_start==0: Q[:,0]=q;V[:,0]=v
    stopped=np.full(len(entries),np.nan)
    # 동일한 지반 기록의 선형 보간값은 모든 설계가 공유한다.
    mids=(ground[:-1,None]+np.diff(ground)[:,None]*(np.arange(steps)+.5)/steps).ravel()
    for k,gm in enumerate(mids,1):
        mid=(ev@v[:,:,None]+eq@q[:,:,None])[:,:,0]+forcing*gm
        w=2*mid[:,-1]/(1+np.sqrt(1+4*loss[:,-1]*np.abs(mid[:,-1])))
        mid-=loss*(abs(w)*w)[:,None]
        q+=dt*mid
        v=2*mid-v
        hit=abs(q[:,-1])>=limits
        if np.any(hit):
            stopped[hit & np.isnan(stopped)]=time[0]+k*dt
            # 종료한 설계는 이후 수치에서 제외. 다른 설계는 그대로 진행한다.
            q[hit]=np.nan;v[hit]=np.nan
        if k%steps==0:
            idx=k//steps-window_start
            if idx>=0:Q[:,idx]=q;V[:,idx]=v
    ret={}
    for i,(code,p,_) in enumerate(entries):
        if not np.isnan(stopped[i]):
            ret[code]=(float(stopped[i]),None)
            continue
        # 절대가속도에서는 -M r ag와 상대→절대 변환의 +ag가 상쇄된다.
        force=-Q[i]@K[i].T-V[i]@C[i].T
        force[:,-1]-=drag[i]*np.abs(V[i,:,-1])*V[i,:,-1]
        acc=np.linalg.solve(M[i],force.T).T[:,:N]
        u=Q[i,:,:N]
        drift=np.diff(u,axis=1,prepend=np.zeros((len(u),1)))
        ret[code]=(None,{key:rms(series,time[window_start:]) for key,series in [('acc',acc),('u',u),('drift',drift)]})
    return ret


# 별도 주파수 실험. SWEEP_AMPLITUDE와 SWEEP_CYCLES를 사용하며 현재 실측 기록의 FFT가 아니다.
def run_sweep(model,cases):
    N=len(model[0])
    if not SWEEP_HZ:return []
    if not (isinstance(SWEEP_CYCLES,int) and isinstance(MEASURE_CYCLES,int) and 1<=MEASURE_CYCLES<=SWEEP_CYCLES):
        raise ValueError('주기 수는 양의 정수이며 측정 주기 수는 총 주기 수 이하여야 합니다.')
    positive('주파수 실험의 가속도 진폭',SWEEP_AMPLITUDE)
    prepared=[]
    for p in [None,*cases]:
        matrices=system(*model[:3],p)
        M,K=matrices[:2]
        factor=np.linalg.cholesky(M)
        left=np.linalg.solve(factor,K)
        fastest=math.sqrt(np.linalg.eigvalsh(np.linalg.solve(factor,left.T).T).max())
        prepared.append((p['code'] if p else 'BARE',p,matrices,min(MAX_INTERNAL_DT,2*np.pi/(INTERNAL_POINTS_PER_PERIOD*fastest))))
    rows=[]
    for hz in SWEEP_HZ:
        positive('주파수 실험의 주파수',hz)
        # 주기별 정수 개의 구간을 써서 측정창 시작점과 끝점이 정확히 일치한다.
        points=max(80,math.ceil(1/(hz*DT)))
        time=np.arange(points*SWEEP_CYCLES+1)/(hz*points)
        start=points*(SWEEP_CYCLES-MEASURE_CYCLES)
        acc=SWEEP_AMPLITUDE*np.sin(2*np.pi*hz*time)
        groups={}
        for code,p,matrices,maxdt in prepared:
            steps=max(1,math.ceil(time[1]/maxdt-1e-10))
            groups.setdefault(steps,[]).append((code,p,matrices))
        measured={}
        for steps,entries in groups.items():
            # 긴 설계 목록도 메모리를 제한하면서 처리한다.
            for offset in range(0,len(entries),32):
                measured.update(sweep_group(model,entries[offset:offset+32],time,acc,steps,start))
        base=measured['BARE'][1]
        for code,_,_,_ in prepared:
            stop,vals=measured[code]
            for i in range(N):
                row=dict(design=code,frequency_hz=hz,floor=i+1,stop_s=stop)
                for key,unit in [('u','m'),('acc','m_s2'),('drift','m')]:
                    row[f'{key}_rms_{unit}']=vals[key][i] if stop is None else None
                    row[f'{key}_reduction_pct']=reduction(base[key][i],vals[key][i]) if stop is None else None
                rows.append(row)
    return rows


def graphs(t,model,phi,omega,cases,results,rows,freq_rows):
    N=len(model[0])
    import matplotlib
    figures={}
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    names={f.name for f in font_manager.fontManager.ttflist}
    for name in ['Malgun Gothic','AppleGothic','NanumGothic']:
        if name in names:plt.rcParams['font.family']=name;break
    plt.rcParams['axes.unicode_minus']=False
    plt.rcParams['axes.spines.top']=False
    plt.rcParams['axes.spines.right']=False
    def save(fig,name):
        figures[name]=fig
        plt.close(fig)
    chosen=list(dict.fromkeys(['BARE','REF',PLOT_CUSTOM_ID]))
    if PLOT_CUSTOM_ID not in results:raise ValueError('PLOT_CUSTOM_ID가 설계 목록에 없습니다.')
    colors=['#536878','#087f83','#c46332']
    locs=sorted({p['floor'] for p in cases})
    # 층이 많아도 글자가 겹치지 않도록 6개 층 또는 모드씩 나눈다.
    for start in range(0,N,6):
        end=min(start+6,N)
        fig,axes=plt.subplots(1,end-start,figsize=(max(5,2.6*(end-start)),4.6),squeeze=False,layout='constrained')
        for mode,ax in zip(range(start,end),axes[0]):
            shape=phi[:,mode]/max(abs(phi[:,mode]))
            ax.plot(np.r_[0,shape],range(N+1),'o-',color=colors[0])
            ax.axvline(0,color='#cccccc',lw=.7)
            for j in locs:
                ax.plot(shape[j-1],j,'o',color=colors[2])
                ax.annotate(f'{shape[j-1]:+.2f}',(shape[j-1],j),xytext=(3,4),textcoords='offset points',fontsize=8)
            ax.set(title=f'{mode+1}차 · {omega[mode]/(2*np.pi):.3f} Hz',xlabel='최대값 1로 표시한 모드 형상',ylabel='층',xlim=(-1.5,1.5))
        fig.suptitle('장치 없는 건물의 모드 형상 · 주황 점은 비교할 설치 층')
        save(fig,f'modes_{start+1}')
        for key,ylabel,filename in [('u','지면 기준 변위 (m)','displacement'),('acc','절대가속도 (m/s²)','acceleration')]:
            fig,axes=plt.subplots(end-start,1,sharex=True,squeeze=False,figsize=(10,2.1*(end-start)+1),layout='constrained')
            for i,ax in zip(range(start,end),axes[:,0]):
                for c,col in zip(chosen,colors):ax.plot(t,results[c][key][:,i],label=c,color=col,lw=1.15)
                ax.set(ylabel=f'{i+1}층');ax.grid(alpha=.2)
            axes[0,0].legend(ncol=3);axes[-1,0].set_xlabel('시간 (s)')
            fig.suptitle(ylabel+' · 동일한 가진')
            save(fig,f'{filename}_{start+1}')
    labels=['BARE']+[p['code'] for p in cases]
    table={(r['design'],r['floor']):r for r in rows}
    floors=np.arange(1,N+1)
    fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
    for k,(code,col) in enumerate(zip(chosen,colors)):
        values=[table[code,i]['acc_rms_m_s2'] for i in floors]
        ax.bar(floors+(k-1)*.25,[np.nan if v is None else v for v in values],width=.24,label=code,color=col)
    ax.set(xticks=floors,xlabel='층',ylabel='절대가속도 RMS (m/s²)',title='층별 절대가속도 비교');ax.legend()
    save(fig,'floor_rms')
    for start in range(0,len(cases),16):
        group=cases[start:start+16]
        matrix=np.array([[table[p['code'],i]['acc_rms_reduction_pct'] for i in floors] for p in group],float)
        finite=matrix[np.isfinite(matrix)]
        limit=max(1.,np.max(abs(finite)) if len(finite) else 1.)
        fig,ax=plt.subplots(figsize=(max(7,min(16,N*.6+5)),max(3,len(group)*.43+2)),layout='constrained')
        cmap=plt.get_cmap('RdBu').copy();cmap.set_bad('#dddddd')
        im=ax.imshow(matrix,aspect='auto',cmap=cmap,vmin=-limit,vmax=limit)
        ax.set(xticks=range(N),xticklabels=floors,xlabel='응답을 측정한 층',yticks=range(len(group)),
               yticklabels=[f"{p['code']} · {p['floor']}층 L={p['L']:.3g} B={p['B']:.3g} β={p['beta']:g}" for p in group],
               title='설치 위치·설계별 가속도 RMS 감소율 (%) · 음수는 증가 / 회색은 산출 불가')
        fig.colorbar(im,ax=ax)
        save(fig,f'designs_{start+1}')
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for c,col in zip(chosen[1:],colors[1:]):
        r=results[c];ax.plot(t,r['water'],label=c,color=col)
        if r['stop'] is not None:ax.axvline(r['stop'],ls=':',color=col)
    ax.set(title='정지 수면 기준 오른쪽 물기둥의 변위',xlabel='시간 (s)',ylabel='액체 변위 (m)');ax.legend()
    save(fig,'water')
    if freq_rows:
        for start in range(0,N,6):
            end=min(N,start+6)
            fig,axes=plt.subplots(end-start,1,squeeze=False,sharex=True,figsize=(8,2*(end-start)+1),layout='constrained')
            for i,ax in zip(range(start,end),axes[:,0]):
                for c,col in zip(chosen,colors):
                    series=sorted((r for r in freq_rows if r['design']==c and r['floor']==i+1),key=lambda r:r['frequency_hz'])
                    ax.plot([r['frequency_hz'] for r in series],[r['acc_rms_m_s2'] for r in series],'o-',color=col,label=c)
                ax.set_ylabel(f'{i+1}층 (m/s²)');ax.grid(alpha=.2)
            axes[0,0].legend(ncol=3);axes[-1,0].set_xlabel('지반 조화 가진 주파수 (Hz)')
            fig.suptitle(f'주파수별 절대가속도 RMS · 마지막 {MEASURE_CYCLES}주기')
            save(fig,f'frequency_{start+1}')
    return figures




# 별도 U형 설계 분석. snapshot이 있으면 건물 X 강성과 해당 입력 기록을 사용한다.
# 다른 관 형상·평면 Y 강성·3D 장치 회전을 이 한 방향 모델에 자동 반영하지 않는다.
def calculate_multistory(snapshot=None):
    location=globals().get("__file__")
    script_dir=Path(location).resolve().parent if location else Path.cwd()
    if snapshot is None:
        M,K,C,height=building()
        stiffness=STIFFNESSES
        install,locations=INSTALL_FLOOR,FLOORS
    else:
        spec=snapshot['building_spec']
        mass,stiffness,height,install=spec.floor_data()
        difference=np.eye(len(mass))-np.eye(len(mass),k=-1)
        M=np.diag(mass)
        K=difference.T@(stiffness[:,None]*difference)
        C=structural_damping(spec)[0]
        locations=list(dict.fromkeys([install,*[i for i in FLOORS if 1<=i<=len(mass)]]))
    N=len(M)
    model=(M,K,C,height)
    omega,phi,gamma=modes(M,K)
    cases=designs(omega,install,locations)
    if PLOT_CUSTOM_ID not in [p['code'] for p in cases if p['code']!='REF']:
        raise ValueError('PLOT_CUSTOM_ID에 실제 사용자 설계 번호를 입력하세요. 기본 D01입니다.')
    if snapshot is None:
        t,ag,forces=record_input(grid(DURATION,DT),script_dir)
    else:
        t,ag=snapshot['t'],snapshot['ag']
        forces=np.zeros((len(t),N))
    mode_rows=[];design_rows=[];all_rows=[];results={}
    for k,w in enumerate(omega):
        for i in range(N):
            mode_rows.append(dict(mode=k+1,floor=i+1,omega_rad_s=w,frequency_hz=w/(2*np.pi),
                period_s=2*np.pi/w,phi_mass_normalized=phi[i,k],participation=gamma[k],
                effective_mass_fraction=gamma[k]**2/np.sum(M)))
    for p in cases:
        for k,w in enumerate(omega):
            value=phi[p['floor']-1,k]
            rel=abs(value)/np.max(abs(phi[:,k]))
            size='큼' if rel>=.7 else '작음' if rel<=.3 else '중간'
            design_rows.append(dict(**p,mode=k+1,tuning_ratio=p['wf']/w,
                phi_at_install=value,relative_mode_amplitude=rel,amplitude_class=size,
                mass_difference_vs_REF_kg=p['mf']-cases[0]['mf']))
    for p in [None,*cases]:
        code=p['code'] if p else 'BARE'
        r=integrate(model,p,t,ag,forces,rest=snapshot is not None)
        results[code]=r
        all_rows.extend(multistory_metrics(t,results['BARE'],r,code))
    freq=run_sweep(model,cases)
    metadata=dict(masses_kg=np.diag(M).tolist(),heights_m=list(height),stiffness_N_m=list(stiffness),
        M=M.tolist(),K=K.tolist(),C=C.tolist(),gravity_m_s2=G,freeboard_m=FREEBOARD,
        requested_dt_s=DT,max_internal_dt=MAX_INTERNAL_DT,duration_s=DURATION,
        initial_floor_u=U0,initial_floor_v=V0,initial_water_y=WATER_Y0,initial_water_v=WATER_V0,
        harmonic_on=HARMONIC_ON,harmonic_hz=HARMONIC_HZ,harmonic_amplitude=AMPLITUDE,
        ground_csv=str(GROUND_CSV) if GROUND_CSV else None,designs=cases,
        sweep_hz=SWEEP_HZ,sweep_amplitude=SWEEP_AMPLITUDE,sweep_cycles=SWEEP_CYCLES,measure_cycles=MEASURE_CYCLES)
    metadata['analysis_scope']='세계 X방향 강성·한 방향 U형 설계 모델'
    if snapshot is not None:
        metadata.update(source=snapshot['source'],wave=snapshot['source']['wave'],requested_dt_s=float(t[1]-t[0]),
            duration_s=float(t[-1]-t[0]), harmonic_on=False,ground_csv=None,
            initial_floor_u=[0.]*N,initial_floor_v=[0.]*N,initial_water_y=0.,initial_water_v=0.)
    return dict(model=model,t=t,ag=ag,forces=forces,omega=omega,phi=phi,cases=cases,results=results,rows=all_rows,mode_rows=mode_rows,design_rows=design_rows,freq=freq,metadata=metadata)


def show_multistory(win, result):
    N=len(result["model"][0])
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    ttk.Label(win,text='세계 X방향 강성의 한 방향 U형 설계 분석 · 현재 3D 장치 형상과 별도로 REF 및 코드 상단 설계를 계산합니다.',wraplength=950).pack(anchor='w')
    reference=result['cases'][0]
    ttk.Label(win,text=f"층 질량 kg={result['metadata']['masses_kg']} · X 강성 N/m={result['metadata']['stiffness_N_m']} · 가진={result['metadata'].get('wave','코드 상단 가진')} · REF L={reference['L']:g} m / B={reference['B']:g} m / β={reference['beta']:g} / 설치 {reference['floor']}층",wraplength=950).pack(anchor='w')
    bar=ttk.Frame(win,padding=8);bar.pack(fill='x')
    tabs=ttk.Notebook(win);tabs.pack(fill='both',expand=True)
    chart=ttk.Frame(tabs);tabs.add(chart,text='그래프')
    figures=graphs(result['t'],result['model'],result['phi'],result['omega'],
        result['cases'],result['results'],result['rows'],result['freq'])
    names={'modes':'모드 형상','displacement':'층별 변위','acceleration':'층별 절대가속도',
        'floor_rms':'층별 RMS 비교','designs':'설계 비교','water':'액체 변위','frequency':'주파수별 응답'}
    labels=[]
    for key in figures:
        prefix,_,page=key.rpartition('_')
        labels.append(names.get(prefix,prefix)+' · '+page if page.isdigit() else names[key])
    picker=ttk.Combobox(chart,values=labels,state='readonly',width=30)
    picker.pack(anchor='w',padx=10,pady=6);picker.current(labels.index('층별 RMS 비교'))
    active=[]
    def draw(*_):
        if active:active.pop().get_tk_widget().destroy()
        fig=list(figures.values())[picker.current()]
        canvas=FigureCanvasTkAgg(fig,master=chart)
        canvas.get_tk_widget().pack(fill='both',expand=True)
        active.append(canvas);canvas.draw_idle()
    picker.bind('<<ComboboxSelected>>',draw);draw()
    tables=[('층별 결과','rows'),('모드','mode_rows'),('설계와 조율비','design_rows'),('주파수 비교','freq')]
    headers={'design':'설계','floor':'층','code':'설계','mode':'모드','frequency_hz':'주파수 (Hz)',
        'period_s':'주기 (s)','acc_rms_reduction_pct':'가속도 RMS 감소 (%)','u_rms_reduction_pct':'변위 RMS 감소 (%)',
        'drift_rms_reduction_pct':'층간변위 RMS 감소 (%)','peak_water_m':'최대 액체 변위 (m)','status':'상태',
        'u_rms_m':'변위 RMS (m)','acc_rms_m_s2':'가속도 RMS (m/s²)','drift_rms_m':'층간변위 RMS (m)',
        'tuning_ratio':'조율비','participation':'참여계수','relative_mode_amplitude':'상대 모드 크기'}
    for title,key in tables:
        rows=result[key]
        if not rows:continue
        page=ttk.Frame(tabs);tabs.add(page,text=title)
        columns=list(rows[0])
        if key=='rows':
            first=['design','floor','u_rms_m','u_rms_reduction_pct','acc_rms_m_s2','acc_rms_reduction_pct','drift_rms_reduction_pct','status']
            columns=first+[c for c in columns if c not in first]
        tree=ttk.Treeview(page,columns=columns,show='headings')
        x=ttk.Scrollbar(page,orient='horizontal',command=tree.xview)
        y=ttk.Scrollbar(page,orient='vertical',command=tree.yview)
        tree.configure(xscrollcommand=x.set,yscrollcommand=y.set)
        tree.grid(row=0,column=0,sticky='nsew');x.grid(row=1,column=0,sticky='ew');y.grid(row=0,column=1,sticky='ns')
        page.columnconfigure(0,weight=1);page.rowconfigure(0,weight=1)
        for c in columns:
            title=headers.get(c,c);tree.heading(c,text=title)
            tree.column(c,width=max(70,10*len(title)+24),stretch=False,anchor='center')
        for row in rows:
            tree.insert('','end',values=['—' if row[c] is None else f'{row[c]:.5g}' if isinstance(row[c],float) else row[c] for c in columns])
    def export():
        path=filedialog.asksaveasfilename(parent=win,defaultextension='.zip',filetypes=[('ZIP','*.zip')],initialfile='다층_TLCD_실험결과.zip')
        if not path:return
        try:export_multistory(path,result,figures)
        except OSError as error:messagebox.showerror('저장 오류',str(error),parent=win);return
        messagebox.showinfo('저장 완료','선택한 ZIP 파일에 결과를 담았습니다.',parent=win)
    ttk.Button(bar,text='결과 ZIP 저장',command=export).pack(side='right')
    ttk.Label(bar,text=f"{N}층  ·  설계 {len(result['cases'])}개  ·  장치 없음 BARE / 기준 REF / 사용자 D").pack(side='left')


def export_multistory(path,r,figures):
    """사용자가 저장을 선택한 경우에만 그래프와 표를 ZIP 하나에 담는다."""
    N=len(r["model"][0])
    import io
    import zipfile
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        def table(name,rows):
            if not rows:return
            stream=io.StringIO(newline='')
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys())
            writer.writeheader();writer.writerows(rows)
            archive.writestr(name,stream.getvalue().encode('utf-8-sig'))
        def numeric(name,cols,series):
            stream=io.StringIO()
            np.savetxt(stream,np.column_stack(series),delimiter=',',comments='',header=','.join(cols))
            archive.writestr(name,stream.getvalue())
        if SAVE_CSV:
            for name,key in [('modes','mode_rows'),('designs_and_tuning','design_rows'),('floor_metrics','rows'),('frequency_response','freq')]:
                table(name+'.csv',r[key])
            numeric('excitation.csv',['time_s','accel_m_s2']+[f'F{i+1}_N' for i in range(N)],[r['t'],r['ag'],r['forces']])
            for code,run in r['results'].items():
                cols=['time_s'];series=[r['t']]
                for key,unit in [('u','m'),('acc','m_s2'),('drift','m'),('ratio','1')]:
                    cols.extend(f'{key}_floor{i+1}_{unit}' for i in range(N));series.append(run[key])
                if run['water'] is not None:cols.append('water_y_m');series.append(run['water'])
                numeric(code+'_history.csv',cols,series)
        archive.writestr('settings.json',json.dumps(r['metadata'],ensure_ascii=False,indent=2))
        for key,fig in figures.items():
            stream=io.BytesIO();fig.savefig(stream,format='png',dpi=145);archive.writestr(key+'.png',stream.getvalue())



# 명령행 인자를 읽고 기본 건물·관·가진을 만든다. GUI 설정은 lab()에서 읽고 적용한다.
def main():
    parser=argparse.ArgumentParser(description='TLCD 3D 실험실')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--sweep',action='store_true')
    parser.add_argument('--input',type=Path)
    parser.add_argument('--unit',choices=['g','m/s2','cm/s2'])
    parser.add_argument('--config',type=Path)
    # 파일로 실행하면 파일 옆에, 코드를 대화형 창에 붙여 넣으면 현재 폴더에 저장한다.
    script_path = globals().get('__file__')
    from_file = bool(script_path and not str(script_path).startswith('<'))
    base_folder = Path(script_path).resolve().parent if from_file else Path.cwd()
    parser.add_argument('--out',type=Path,default=base_folder/'results_3d')
    args=parser.parse_args(None if from_file else [])
    # 결과 파일만 만드는 Matplotlib은 비대화형으로 둔다. 애니메이션은 Tk가 그린다.
    import matplotlib
    matplotlib.use('Agg')
    cfg=json.loads(args.config.read_text(encoding='utf-8-sig')) if args.config else {}
    example_b,example_d=stable_example()
    b=Building(**cfg['building']) if 'building' in cfg else example_b
    d=Damper(**{k:v for k,v in cfg['damper'].items() if k in Damper.__dataclass_fields__}) if 'damper' in cfg else example_d
    validate(b,d)
    if args.input and not args.unit: parser.error('CSV에는 --unit 단위가 필요합니다.')
    t,ag=load_input(args.input,args.unit) if args.input else recorded_input()
    title=args.input.name if args.input else '1940 엘센트로 남북 기록  ·  31.16초  ·  모형 입력 0.03 g'
    if args.sweep: sweep(b,d,t,ag,args.out)
    if args.headless: export_space(args.out,b,d,simulate_space(b,d,t,ag),title)
    else: lab(b,d,t,ag,title,args.out)


if __name__=='__main__':
    main()
