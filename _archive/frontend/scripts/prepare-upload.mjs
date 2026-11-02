import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(here, '../..');
const [sdkGameArg, frontendDistArg] = process.argv.slice(2);
if (!sdkGameArg || !frontendDistArg) {
  console.error('Usage: node scripts/prepare-upload.mjs <SDK-game-directory> <frontend-dist-directory>');
  process.exit(2);
}
const sdkGame = path.resolve(sdkGameArg);
const frontendDist = path.resolve(frontendDistArg);
const lib = path.join(sdkGame, 'library');
const publish = path.join(lib, 'publish_files');
const configs = path.join(lib, 'configs');
const forces = path.join(lib, 'forces');
const expectedModes = {
  base: 1,
  ante: 3,
  bonus: 100,
  super_bonus: 500,
};
const fail = (message) => { throw new Error(`Release gate blocked: ${message}`); };

for (const dir of [sdkGame, publish, configs, forces, frontendDist]) {
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) fail(`missing directory: ${dir}`);
}
if (!fs.existsSync(path.join(frontendDist, 'index.html'))) fail('frontend dist/index.html is missing; run the Web SDK production build first');

const requiredPublish = ['index.json', 'books_base.jsonl.zst', 'books_ante.jsonl.zst', 'books_bonus.jsonl.zst', 'books_super_bonus.jsonl.zst', 'lookUpTable_base_0.csv', 'lookUpTable_ante_0.csv', 'lookUpTable_bonus_0.csv', 'lookUpTable_super_bonus_0.csv'];
for (const file of requiredPublish) if (!fs.existsSync(path.join(publish, file))) fail(`missing official SDK output ${file}`);

const index = JSON.parse(fs.readFileSync(path.join(publish, 'index.json'), 'utf8'));
const manifestModes = new Map((index.modes ?? []).map((mode) => [mode.name, mode]));
for (const [mode, cost] of Object.entries(expectedModes)) {
  const item = manifestModes.get(mode);
  if (!item) fail(`manifest is missing ${mode}`);
  if (Number(item.cost) !== cost) fail(`${mode} cost is ${item.cost}, expected ${cost}`);
}

const beConfigPath = path.join(configs, 'config.json');
const feConfigPath = fs.readdirSync(configs).filter((name) => name.startsWith('config_fe_') && name.endsWith('.json')).map((name) => path.join(configs, name))[0];
const statsPath = path.join(sdkGame, 'library', 'stats_summary.json');
if (!fs.existsSync(beConfigPath) || !feConfigPath || !fs.existsSync(feConfigPath)) fail('SDK backend/frontend configs are missing');
if (!fs.existsSync(statsPath)) fail('stats_summary.json is missing; run official SDK verification');
const beConfig = JSON.parse(fs.readFileSync(beConfigPath, 'utf8'));
const feConfig = JSON.parse(fs.readFileSync(feConfigPath, 'utf8'));
const stats = JSON.parse(fs.readFileSync(statsPath, 'utf8'));
if (!Number.isInteger(beConfig.providerNumber) || beConfig.providerNumber <= 0) fail('providerNumber is still a placeholder; use the KingWin portal-issued provider number');
if (feConfig.providerName !== 'KingWin') fail(`providerName must be KingWin, got ${feConfig.providerName}`);

const rtpTarget = 0.965;
const rtpTolerance = 0.002;
for (const [mode, cost] of Object.entries(expectedModes)) {
  const result = stats[mode];
  if (!result) fail(`stats_summary is missing ${mode}`);
  if (!Number.isFinite(result.rtp) || Math.abs(result.rtp - rtpTarget) > rtpTolerance) fail(`${mode} optimized RTP ${result.rtp} is outside ${rtpTarget} ± ${rtpTolerance}`);
  if (!Number.isFinite(result.max_win) || result.max_win > 1_000_000) fail(`${mode} max-win exceeds 10,000x`);
  if ((result.prob10k ?? 0) > 0.005) fail(`${mode} prob10k limit exceeded`);
  if ((result.etl40b ?? 0) > 0.9) fail(`${mode} ETL40b limit exceeded`);
  if ((result.etl10k ?? 0) > 0.8) fail(`${mode} ETL10k limit exceeded`);
  if ((result.cvar ?? 0) > 800) fail(`${mode} CVaR limit exceeded`);
}

const release = path.join(packageRoot, 'release-candidate');
if (fs.existsSync(release)) fs.rmSync(release, { recursive: true, force: true });
fs.mkdirSync(path.join(release, 'math', 'publish_files'), { recursive: true });
fs.mkdirSync(path.join(release, 'math', 'configs'), { recursive: true });
fs.mkdirSync(path.join(release, 'math', 'forces'), { recursive: true });
fs.mkdirSync(path.join(release, 'frontend'), { recursive: true });
for (const name of fs.readdirSync(publish)) fs.copyFileSync(path.join(publish, name), path.join(release, 'math', 'publish_files', name));
for (const name of fs.readdirSync(configs)) fs.copyFileSync(path.join(configs, name), path.join(release, 'math', 'configs', name));
for (const name of fs.readdirSync(forces)) fs.copyFileSync(path.join(forces, name), path.join(release, 'math', 'forces', name));
fs.cpSync(frontendDist, path.join(release, 'frontend'), { recursive: true });
fs.copyFileSync(statsPath, path.join(release, 'math', 'stats_summary.json'));
console.log(`Release candidate staged at ${release}`);
console.log('This local gate does not replace KingWin/Stake Engine portal approval or external RGS verification.');
