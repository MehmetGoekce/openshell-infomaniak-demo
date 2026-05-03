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
