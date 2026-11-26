import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '../..');
const input = await fs.readFile(path.join(root, 'office_practice_clean.csv'), 'utf8');
const workbook = await Workbook.fromCSV(input, { sheetName: '정리데이터' });
const clean = workbook.worksheets.getItem('정리데이터');
const summary = workbook.worksheets.add('집계');
const cross = workbook.worksheets.add('교차표');
const types = ['문서작성', '비품신청', '시스템문의', '자료요청', '비용정산', '일정조율', '계정문의'];
const departments = ['경영지원팀', '총무팀', 'IT지원팀', '재무팀', '기획팀', '미분류'];
const statuses = ['접수', '진행중', '완료', '보류', '미분류'];

// Keep all six source columns as text, as requested in the original import.
clean.getRange('A1:F35').setNumberFormat('@');
summary.getRange('A1:B9').values = [
  ['업무유형', '건수'], ...types.map(name => [name, null]), ['전체 합계', null],
];
summary.getRange('B2:B8').formulas = types.map((_, i) => [
  `=COUNTIFS('정리데이터'!$C$2:$C$35,A${i + 2})`,
]);
summary.getRange('B9').formulas = [['=SUM(B2:B8)']];
cross.getRange('A1:G8').values = [
  ['담당부서', ...statuses, '전체 합계'],
  ...departments.map(name => [name, null, null, null, null, null, null]),
  ['전체 합계', null, null, null, null, null, null],
];
cross.getRange('B2:F7').formulas = departments.map((_, i) => statuses.map((__, j) =>
  `=COUNTIFS('정리데이터'!$F$2:$F$35,$A${i + 2},'정리데이터'!$D$2:$D$35,${String.fromCharCode(66 + j)}$1)`));
cross.getRange('G2:G7').formulas = departments.map((_, i) => [`=SUM(B${i + 2}:F${i + 2})`]);
cross.getRange('B8:G8').formulas = [[...Array.from({ length: 6 }, (_, i) => {
  const col = String.fromCharCode(66 + i);
  return `=SUM(${col}2:${col}7)`;
})]];

for (const [sheet, area, header] of [
  [clean, 'A1:F35', 'A1:F1'], [summary, 'A1:B9', 'A1:B1'], [cross, 'A1:G8', 'A1:G1'],
]) {
  sheet.showGridLines = false;
  sheet.getRange(area).format.font = { name: 'Malgun Gothic', size: 11, color: '#17243B' };
  sheet.getRange(area).format.rowHeight = 25;
  sheet.getRange(area).format.columnWidthPx = 132;
  sheet.getRange(area).format.verticalAlignment = 'center';
  sheet.getRange(header).format.fill = '#243B60';
  sheet.getRange(header).format.font = { name: 'Malgun Gothic', size: 11, color: '#FFFFFF', bold: true };
  sheet.getRange(header).format.horizontalAlignment = 'center';
  sheet.getRange(header).format.rowHeight = 30;
}
clean.getRange('A:A').format.columnWidthPx = 142;
clean.getRange('B:F').format.columnWidthPx = 145;
clean.freezePanes.freezeRows(1);
summary.getRange('A:A').format.columnWidthPx = 155;
summary.getRange('B2:B9').setNumberFormat('#,##0');
summary.getRange('B2:B9').format.horizontalAlignment = 'right';
cross.getRange('A:A').format.columnWidthPx = 155;
cross.getRange('B:G').format.columnWidthPx = 100;
cross.getRange('B2:G8').setNumberFormat('#,##0');
cross.getRange('B2:G8').format.horizontalAlignment = 'right';
for (const [sheet, range] of [[summary, 'A9:B9'], [cross, 'A8:G8']]) {
  sheet.getRange(range).format.fill = '#E8EDF5';
  sheet.getRange(range).format.font.bold = true;
  sheet.getRange(range).format.borders = { top: { style: 'thin', color: '#A6B4C8' } };
}
cross.getRange('G2:G7').format.font.bold = true;
workbook.recalculate();

if (summary.getRange('B9').values[0][0] !== 34 || cross.getRange('G8').values[0][0] !== 34) {
  throw new Error('Workbook totals failed reconciliation');
}
const expectedTypes = [3, 6, 5, 5, 5, 5, 5];
if (JSON.stringify(summary.getRange('B2:B8').values.flat()) !== JSON.stringify(expectedTypes)) {
  throw new Error('Type counts do not match CSV');
}
console.log((await workbook.inspect({ kind: 'table', range: '교차표!A1:G8', include: 'values,formulas', tableMaxRows: 8, tableMaxCols: 7, maxChars: 3000 })).ndjson);
console.log((await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 20 }, maxChars: 1000 })).ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(dir, 'office_practice_result.xlsx'));
for (const [sheetName, range, filename] of [
  ['정리데이터', 'A1:F35', 'preview_clean.png'],
  ['집계', 'A1:B9', 'preview_summary.png'],
  ['교차표', 'A1:G8', 'preview_cross.png'],
]) {
  const preview = await workbook.render({ sheetName, autoCrop: 'all', scale: 1, format: 'png' });
  await fs.writeFile(path.join(dir, filename), new Uint8Array(await preview.arrayBuffer()));
}
console.log(JSON.stringify({ exported: true, sheets: ['정리데이터', '집계', '교차표'], cleanRows: 34, summaryTotal: 34, crosstabTotal: 34 }));
