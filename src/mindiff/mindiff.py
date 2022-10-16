"""
This script is based on the source code of Differ class in difflib. The
necessary parts have been extracted from the original code and partially
modified to simplify the diff output.

https://github.com/python/cpython/blob/f6b1e4048dc353aecfbfbae07de8212900632098/Lib/difflib.py#L833-L997
"""

import os
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Final, Generator, Sequence, Union

PATH_TYPE = Union[str, bytes, os.PathLike]


def usage():
    cmd = Path(__file__).name
    print(f"Usage: {cmd} <file1> <file2>")


def main():
    if len(sys.argv) != 3:
        usage()
        exit()
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    for line in compare_file(file1, file2):
        print(line, end="")


def _dump(lines: Sequence[str], lo: int, hi: int, prefix: str = " ") -> Generator[str, None, None]:
    for i in range(lo, hi):
        yield f"{prefix} {lines[i]}"


def _dump_replace(
    a: Sequence[str], alo: int, ahi: int, b: Sequence[str], blo: int, bhi: int
) -> Generator[str, None, None]:
    g = []
    if alo < ahi:
        if blo < bhi:
            # tag: "replace"
            g = _sync_point_replace(a, alo, ahi, b, blo, bhi)
        else:
            # tag: "delete"
            g = _dump(a, alo, ahi, "-")
    elif blo < bhi:
        # tag: "insert"
        g = _dump(b, blo, bhi, "+")
    yield from g


def _sync_point_replace(
    a: Sequence[str], alo: int, ahi: int, b: Sequence[str], blo: int, bhi: int
) -> Generator[str, None, None]:

    # 類似行と判定する基準
    CUTOFF: Final[float] = 0.75

    # 類似度がもっとも高い行ペアの情報
    best_ratio = 0.0
    best_i, best_j = None, None

    # 最初に見つかった同一行のインデックス
    eqi, eqj = None, None

    # 対応する範囲内でもっとも類似度の高い行ペアを探す
    matcher = SequenceMatcher()
    for j in range(blo, bhi):
        bj = b[j]
        matcher.set_seq2(bj)  # seq2 の値はキャッシュされる
        for i in range(alo, ahi):
            ai = a[i]
            # まったく同一の行はスキップ
            if ai == bj:
                # 最初に見つかった同一行を保存しておく
                if eqi is None:
                    eqi, eqj = i, j
                continue
            matcher.set_seq1(ai)

            # 行ペアの類似度を計算して，これまでの最大値よりも高ければ更新する
            # ratio() は計算コストが非常に高いため，近似値を求める簡便法を先に試す
            if matcher.real_quick_ratio() > best_ratio and matcher.quick_ratio() > best_ratio:
                r = matcher.ratio()
                if r > best_ratio:
                    best_ratio = r
                    best_i, best_j = i, j

    # 類似度の基準を満たす行ペアが存在しなかった場合
    if best_ratio < CUTOFF:
        # さらに同一の行もなかった場合
        # 置換される行にマーカーをつけるだけにして終了
        if eqi is None or eqj is None:
            yield from _dump(a, alo, ahi, "-")
            yield from _dump(b, blo, bhi, "+")
            return
        # 同一行があった場合はそれを最良の行ペアとする
        best_i, best_j, best_ratio = eqi, eqj, 1.0
    else:
        # 類似度の高い行ペアが見つかったので同一行は無視する
        eqi = None
        eqj = None

    # この時点で同期点となる行ペアが見つかっているはず
    if best_i is None or best_j is None:
        raise RuntimeError("Could not determine synchronization point.")

    # 同期点よりも前を再帰的に処理
    yield from _dump_replace(a, alo, best_i, b, blo, best_j)

    # 同期点を出力
    # a から b へどのように変化したかを出力する
    # 差異行にはマーカーをつけて，同一行にはつけないだけの違い
    if eqi is None:
        yield from _dump(b, best_j, best_j + 1, "!")
    else:
        yield from _dump(b, best_j, best_j + 1)

    # 同期点よりも後ろを再帰的に処理
    yield from _dump_replace(a, best_i + 1, ahi, b, best_j + 1, bhi)


def compare(a: Sequence[str], b: Sequence[str]) -> Generator[str, None, None]:
    matcher = SequenceMatcher(None, a, b)
    for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
        if tag == "replace":
            g = _dump_replace(a, alo, ahi, b, blo, bhi)
        elif tag == "delete":
            g = _dump(a, alo, ahi, "-")
        elif tag == "insert":
            g = _dump(b, blo, bhi, "+")
        elif tag == "equal":
            g = _dump(a, alo, ahi, " ")
        else:
            raise ValueError("unknown tag: {tag}")
        yield from g


def compare_file(file1: PATH_TYPE, file2: PATH_TYPE) -> Generator[str, None, None]:
    with open(file1, "r", encoding="utf-8") as f:
        a = f.readlines()
    with open(file2, "r", encoding="utf-8") as f:
        b = f.readlines()
    yield from compare(a, b)


if __name__ == "__main__":
    main()
