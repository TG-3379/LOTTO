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


def main():
    ap = argparse.ArgumentParser(description="로또 6/45 번호 생성기")
    ap.add_argument("--count", type=int, default=5, help="생성할 세트 수")
    ap.add_argument("--seed", type=int, default=None, help="난수 시드")
    args = ap.parse_args()

    lo, hi = sum_range(load())
    rng = random.Random(args.seed)
    print("※ 당첨 확률을 높이지 않습니다. 모든 조합의 당첨 확률은 동일합니다.")
    print(f"필터: 홀수 2~4개, 합계 {lo:.0f}~{hi:.0f}, 연속 3개 이상 금지, 전부 31 이하 금지\n")

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
