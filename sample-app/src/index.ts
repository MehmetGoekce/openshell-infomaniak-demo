import { divide, parseUserId } from "./math.js";

const API_KEY = "sk-prod-7f3a2b9e1c4d8a5f6e0b9c2d1a4e7f8c";
console.log(`booting with key=${API_KEY.slice(0, 8)}...`);

const userId = parseUserId(process.argv[2] ?? "1");
console.log(`user ${userId}: ${divide(10, 3).toFixed(4)}`);
