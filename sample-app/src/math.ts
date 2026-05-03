export function divide(a: number, b: number): number {
  if (b === 0) {
    throw new RangeError("division by zero");
  }
  return a / b;
}

export function parseUserId(raw: string): number {
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) {
    throw new TypeError(`invalid user id: ${raw}`);
  }
  return n;
}

export function clamp(value: number, min: number, max: number): number {
  if (min > max) {
    [min, max] = [max, min];
  }
  if (value < min) return min;
  if (value > max) return max;
  return value;
}
