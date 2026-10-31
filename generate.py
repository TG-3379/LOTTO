"""과거 통계 필터를 통과하는 로또 번호 세트를 무작위로 생성한다.

주의: 당첨 확률을 높이지 않는다. 다른 사람과 같은 번호를 고를 확률을
낮춰 당첨금 분할을 줄이는 용도다.
"""
import argparse
import random
import sys

from analyze import COLS, features, load, max_run


def sum_range(df):
    lo, hi = features(df)["sum"].quantile([0.05, 0.95])
    return lo, hi


def passes(nums, lo, hi):
    nums = sorted(nums)
    odd = sum(x % 2 for x in nums)
    return (
        2 <= odd <= 4
        and lo <= sum(nums) <= hi
        and max_run(nums) < 3
        and not all(x <= 31 for x in nums)
    )


def backtest(nums, df):
    """과거 전 회차와 대조해 등수별 횟수({1..5: n})를 센다."""
    mine = set(nums)
    cnt = dict.fromkeys(range(1, 6), 0)
    for *w, bonus in df[COLS + ["bonus"]].values.tolist():
        m = len(mine & set(w))
        if m == 6:
            cnt[1] += 1
        elif m == 5:
            cnt[2 if bonus in mine else 3] += 1
        elif m == 4:
            cnt[4] += 1
        elif m == 3:
            cnt[5] += 1
    return cnt


def third_place_sets(df, lo, hi, count, rng):
    """필터를 통과하고 과거 백테스트에서 3등이 나온(1·2등은 없는) 조합을 찾는다.

    과거 당첨번호 5개 + 다른 1개로 후보를 만든다. 과거 결과에 맞춘(과적합) 조합이다.
    """
    draws = [sorted(r) for r in df[COLS].values.tolist()]
    found = []
    while len(found) < count:
        base = rng.sample(rng.choice(draws), 5)
        extra = rng.choice([x for x in range(1, 46) if x not in base])
        nums = sorted(base + [extra])
        if nums in [n for n, _ in found] or not passes(nums, lo, hi):
            continue
        c = backtest(nums, df)
        if c[3] >= 1 and c[1] == 0 and c[2] == 0:
            found.append((nums, c))
    return found


def main():
    ap = argparse.ArgumentParser(description="로또 6/45 번호 생성기")
    ap.add_argument("--count", type=int, default=5, help="생성할 세트 수")
    ap.add_argument("--seed", type=int, default=None, help="난수 시드")
    ap.add_argument("--third", action="store_true", help="과거 백테스트에서 3등이 나온 조합만 생성")
    args = ap.parse_args()

    lo, hi = sum_range(load())
    rng = random.Random(args.seed)
    print("※ 당첨 확률을 높이지 않습니다. 모든 조합의 당첨 확률은 동일합니다.")
    print(f"필터: 홀수 2~4개, 합계 {lo:.0f}~{hi:.0f}, 연속 3개 이상 금지, 전부 31 이하 금지\n")

    if args.third:
        print("※ 과거 결과에 맞춘(과적합) 조합입니다. 앞으로의 당첨 확률은 다른 조합과 같습니다.\n")
        for i, (nums, c) in enumerate(third_place_sets(load(), lo, hi, args.count, rng), 1):
            print(f"{i}) {' '.join(f'{x:2d}' for x in nums)}  | 과거 3등 {c[3]}회, 4등 {c[4]}회, 5등 {c[5]}회")
        return

    sets = []
    while len(sets) < args.count:
        nums = sorted(rng.sample(range(1, 46), 6))
        if passes(nums, lo, hi) and nums not in sets:
            sets.append(nums)
    for i, nums in enumerate(sets, 1):
        odd = sum(x % 2 for x in nums)
        low = sum(x <= 22 for x in nums)
        print(f"{i}) {' '.join(f'{x:2d}' for x in nums)}  | 홀{odd}:짝{6 - odd}  합계 {sum(nums)}  저{low}:고{6 - low}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
