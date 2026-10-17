// Colour classes for verdict words in terminal output (PASS green, FAIL red, INCONCLUSIVE amber).
export function verdictClass(line: string): 'pass' | 'fail' | 'inc' | null {
  if (/\[PASS\]|RESULT: PASS/.test(line)) return 'pass';
  if (/\[FAIL\]|RESULT: FAIL/.test(line)) return 'fail';
  if (/\[INCONCLUSIVE\]|RESULT: INCONCLUSIVE/.test(line)) return 'inc';
  return null;
}

/** Split a line so that only the verdict word is highlighted. */
export function highlightParts(line: string): { text: string; cls: string | null }[] {
  const match = /(\[(?:PASS|FAIL|INCONCLUSIVE)\]|RESULT: (?:PASS|FAIL|INCONCLUSIVE))/.exec(line);
  if (!match) return [{ text: line, cls: null }];
  const cls = verdictClass(match[0]);
  const start = match.index;
  return [
    { text: line.slice(0, start), cls: null },
    { text: match[0], cls },
    { text: line.slice(start + match[0].length), cls: null },
  ].filter((p) => p.text !== '');
}
