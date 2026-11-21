// news-image-20261121 entrypoint (Node 22, standard library only).
//
// The entry is the broadsheet in entry.png, drawn by tools/render21.py
// from news.json and three CC-licensed file photos. This program only
// checks that file against the competition's limits and writes it to
// the grader's output directory as entry.png. It writes nothing else
// and reads no clock or network, so two runs produce the same bytes.
//
// Outside the grader, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PNG_SIG = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
// A whole PNG ends with the 12-byte IEND chunk: zero length, the
// ASCII type "IEND", and the fixed CRC ae 42 60 82.
const PNG_IEND = Buffer.from([
  0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82,
]);
const BYTE_CAP = 1024 * 1024;
const SIDE_CAP = 1024;
const WANT_W = 680;
const WANT_H = 1024;

function reject(why) {
  throw new Error(`entry.png rejected: ${why}`);
}

function checkPng(bytes) {
  if (bytes.length > BYTE_CAP) {
    reject(`is ${bytes.length} bytes, over the ${BYTE_CAP} byte cap`);
  }
  for (let i = 0; i < PNG_SIG.length; i++) {
    if (bytes[i] !== PNG_SIG[i]) {
      reject("does not start with the PNG signature");
    }
  }
  // IHDR stores width at bytes 16-19 and height at 20-23, big-endian.
  const w = bytes.readUInt32BE(16);
  const h = bytes.readUInt32BE(20);
  if (w > SIDE_CAP || h > SIDE_CAP) {
    reject(`is ${w}x${h}, over the ${SIDE_CAP}x${SIDE_CAP} cap`);
  }
  if (w !== WANT_W || h !== WANT_H) {
    reject(`is ${w}x${h}, expected ${WANT_W}x${WANT_H}`);
  }
  if (bytes.length < PNG_IEND.length ||
      !bytes.subarray(bytes.length - PNG_IEND.length).equals(PNG_IEND)) {
    reject("does not end with the IEND chunk: not a whole PNG");
  }
}

function main() {
  const here = dirname(fileURLToPath(import.meta.url));
  const bytes = readFileSync(join(here, "entry.png"));
  checkPng(bytes);

  const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "entry.png"), bytes);
}

main();
