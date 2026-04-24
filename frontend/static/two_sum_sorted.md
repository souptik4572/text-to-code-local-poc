# Two Sum II — Input Array Is Sorted

Given a **1-indexed** array of integers `numbers` sorted in non-decreasing order, find two numbers that add up to `target` and return their indices as `[index1, index2]` where `index1 < index2`.

The tests are generated such that there is **exactly one solution**. You may not use the same element twice.

Your solution must use only **O(1) extra space**.

---

## Examples

**Example 1**

```
Input:  numbers = [2, 7, 11, 15], target = 9
Output: [1, 2]
```
*numbers[1] + numbers[2] == 2 + 7 == 9*

**Example 2**

```
Input:  numbers = [2, 3, 4], target = 6
Output: [1, 3]
```

**Example 3**

```
Input:  numbers = [-1, 0], target = -1
Output: [1, 2]
```

---

## Constraints

- `2 ≤ numbers.length ≤ 3 × 10⁴`
- `-1000 ≤ numbers[i] ≤ 1000`
- `numbers` is sorted in non-decreasing order.
- `-1000 ≤ target ≤ 1000`
- Exactly one valid answer exists.

---

## Hint

Because the array is sorted, you can use a **two-pointer** approach — one pointer at the start and one at the end — to achieve O(n) time and O(1) space.
