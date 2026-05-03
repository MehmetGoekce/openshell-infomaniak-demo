import { divide, parseUserId } from "./math.js";

const userId = parseUserId(process.argv[2] ?? "1");
console.log(`user ${userId}: ${divide(10, 3).toFixed(4)}`);
