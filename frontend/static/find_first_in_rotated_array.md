# Find Minimum in Rotated Sorted Array

Suppose an array of length `n` sorted in ascending order is **rotated** between `1` and `n` times. For example, `[0, 1, 2, 4, 5, 6, 7]` might become `[4, 5, 6, 7, 0, 1, 2]` (rotated 4 times) or `[0, 1, 2, 4, 5, 6, 7]` (rotated 7 times, back to original).

Given the sorted rotated array `nums` of **unique** elements, return the **minimum element** (i.e. the first element of the original sorted array).

You must write an algorithm that runs in **O(log n)** time.

---

## Examples

**Example 1**

```
Input:  nums = [3, 4, 5, 1, 2]
Output: 1
```
*Original array: [1, 2, 3, 4, 5], rotated 3 times.*

**Example 2**

```
Input:  nums = [4, 5, 6, 7, 0, 1, 2]
Output: 0
```
*Original array: [0, 1, 2, 4, 5, 6, 7], rotated 4 times.*

**Example 3**

```
Input:  nums = [11, 13, 15, 17]
Output: 11
```
*Original array already sorted (rotated 4 times).*

---

## Constraints

- `n == nums.length`
- `1 ≤ n ≤ 5000`
- `-5000 ≤ nums[i] ≤ 5000`
- All integers in `nums` are **unique**.
- `nums` is sorted and rotated between `1` and `n` times.

---

## Hint

Use **binary search**. At each step, compare `nums[mid]` with `nums[right]`:
- If `nums[mid] > nums[right]`, the minimum is in the right half.
- Otherwise, it is in the left half (including `mid`).
