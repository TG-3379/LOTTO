"""data/lotto_history.csv 를 분석해 reports/summary.md 를 만든다."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
COLS = [f"n{i}" for i in range(1, 7)]
RECENT = 50


def load():
    return pd.read_csv(ROOT / "data" / "lotto_history.csv")


def max_run(nums):
    best = run = 1
    for a, b in zip(nums, nums[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best


def features(df):
    n = df[COLS]
    f = pd.DataFrame(index=df.index)
    f["odd"] = n.apply(lambda r: sum(x % 2 for x in r), axis=1)
    f["low"] = (n <= 22).sum(axis=1)
    f["sum"] = n.sum(axis=1)
    f["run"] = n.apply(lambda r: max_run(sorted(r)), axis=1)
    f["all_le31"] = (n <= 31).all(axis=1)
    return f


def dist_table(series, label):
    t = series.value_counts().sort_index()
    pct = (t / len(series) * 100).round(1)
    lines = [f"| {label} | 회차 수 | 비율 |", "|---|---|---|"]
    lines += [f"| {k} | {v} | {pct[k]}% |" for k, v in t.items()]
    return "\n".join(lines)


def main():
    df = load()
    f = features(df)
    n = df[COLS]
    total = len(df)
    freq = pd.Series(n.values.ravel()).value_counts().reindex(range(1, 46), fill_value=0)
    recent = pd.Series(n.tail(RECENT).values.ravel()).value_counts().reindex(range(1, 46), fill_value=0)
    ends = pd.Series(n.values.ravel() % 10).value_counts().sort_index()
    p5, p95 = f["sum"].quantile([0.05, 0.95])

    out = [
        "# 로또 6/45 과거 데이터 요약",
        "",
        "> 로또 추첨은 회차마다 독립적이고 무작위입니다. 이 통계는 참고용이며 당첨 확률을 높이지 않습니다.",
        "",
        f"- 분석 회차: {total}회 (1회 ~ {int(df.draw_no.max())}회, 마지막 추첨일 {df.date.iloc[-1]})",
        "",
        "## 번호별 출현 빈도",
        "",
        f"| 번호 | 전체 | 최근 {RECENT}회 |",
        "|---|---|---|",
    ]
    out += [f"| {i} | {freq[i]} | {recent[i]} |" for i in range(1, 46)]
    out += [
        "",
        f"- 전체 최다: {freq.idxmax()}번({freq.max()}회), 최소: {freq.idxmin()}번({freq.min()}회)",
        f"- 번호당 기대값(균등): {total * 6 / 45:.1f}회",
        "",
        "## 홀수 개수 분포 (6개 중)",
        "",
        dist_table(f["odd"], "홀수 개수"),
        "",
        "## 저(1~22)·고(23~45) 분포 (저번호 개수)",
        "",
        dist_table(f["low"], "저번호 개수"),
        "",
        "## 당첨번호 합계",
        "",
        f"- 평균 {f['sum'].mean():.1f}, 표준편차 {f['sum'].std():.1f}",
        f"- 5~95 백분위수: {p5:.0f} ~ {p95:.0f}",
        "",
        "## 연속번호",
        "",
        f"- 연속 2개 이상 포함: {(f['run'] >= 2).mean() * 100:.1f}%",
        f"- 연속 3개 이상 포함: {(f['run'] >= 3).mean() * 100:.1f}%",
        f"- 6개 모두 31 이하: {f['all_le31'].mean() * 100:.1f}%",
        "",
        "## 끝자리 분포",
        "",
        "| 끝자리 | 출현 수 |",
        "|---|---|",
    ]
    out += [f"| {k} | {v} |" for k, v in ends.items()]

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"reports/summary.md 저장 완료 ({total}회차 분석)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
