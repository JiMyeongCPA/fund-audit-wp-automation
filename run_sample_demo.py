"""sample_data/의 표본 입력으로 조립 파이프라인을 실행한다 -- 클론한 뒤
별도 자료 없이 바로 돌려볼 수 있는 진입점(결과: sample_output/조립결과.xlsx).
"""
from pathlib import Path

from core.assemble import build_workpaper

SAMPLE_DATA = Path(__file__).parent / "sample_data"
CSV_PATH = SAMPLE_DATA / "기준가격대장(결산후).csv"
GUNGNAEYUDONG_CSV_PATH = SAMPLE_DATA / "국내유동명세.csv"
GUNGNAEJUSIK_CSV_PATH = SAMPLE_DATA / "국내주식명세.csv"
PUNDBYEOLMYEONGSE_CSV_PATH = SAMPLE_DATA / "펀드별명세.csv"
SOOIKJEUNGGWON_CSV_PATH = SAMPLE_DATA / "국내집합투자증권명세.csv"
SEONMUL_CSV_PATH = SAMPLE_DATA / "국내선물명세.csv"
CHAEGWON_CSV_PATH = SAMPLE_DATA / "채권명세.csv"
GAJUNGPYEONGGYUNJWASU_CSV_PATH = SAMPLE_DATA / "일별좌수순자산현황.csv"
BOSUBUNBAE_CSV_PATH = SAMPLE_DATA / "판매보수내역.csv"
ILBYEOLJASAN_CSV_PATH = SAMPLE_DATA / "일별자산내역.csv"
SEOLJEONGHEJI_CSV_PATH = SAMPLE_DATA / "설정해지내역.csv"
REFERENCE_WORKPAPER = SAMPLE_DATA / "전기조서.xlsx"

OUTPUT_DIR = Path(__file__).parent / "sample_output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "조립결과.xlsx"

if __name__ == "__main__":
    report = build_workpaper(
        CSV_PATH,
        GUNGNAEYUDONG_CSV_PATH,
        GUNGNAEJUSIK_CSV_PATH,
        PUNDBYEOLMYEONGSE_CSV_PATH,
        SOOIKJEUNGGWON_CSV_PATH,
        SEONMUL_CSV_PATH,
        CHAEGWON_CSV_PATH,
        GAJUNGPYEONGGYUNJWASU_CSV_PATH,
        BOSUBUNBAE_CSV_PATH,
        ILBYEOLJASAN_CSV_PATH,
        SEOLJEONGHEJI_CSV_PATH,
        REFERENCE_WORKPAPER,
        OUTPUT_PATH,
    )
    print(f"저장됨: {OUTPUT_PATH}")
    print(f"통합기준가격대장에 없는 계정코드: {report['missing_account_codes']}")
    print(f"정산표 전기 데이터 중 구조 어긋남(drift) 감지: {report['drifted_prior_year_rows']}")
    print(f"검토 필요 항목: {report['needs_review']}")
