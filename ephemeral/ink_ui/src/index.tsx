import React, {useEffect, useMemo, useState} from 'react';
import {Box, render, Text, useApp, useInput, useStdin, useStdout} from 'ink';
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';

type ActionId =
	| 'help'
	| 'shortcuts'
	| 'keys'
	| 'ask'
	| 'quote'
	| 'news'
	| 'compare'
	| 'chart'
	| 'backtest'
	| 'portfolio'
	| 'strategy'
	| 'report'
	| 'alert'
	| 'status'
	| 'doctor'
	| 'models'
	| 'tools'
	| 'reload'
	| 'setup-help'
	| 'set-provider'
	| 'set-model'
	| 'set-key'
	| 'export'
	| 'legacy-ui';

type FocusPane = 'actions' | 'history' | 'output' | 'input';
type DetailMode = 'rendered' | 'raw';
type LayoutMode = 'desktop' | 'stacked';

type BridgeRequest = {
	action: ActionId;
	[key: string]: unknown;
};

type BridgeEnvelope = {
	ok: boolean;
	id?: string;
	action?: string;
	data?: any;
	error?: string;
};

type HistoryEntry = {
	id: string;
	label: string;
	input: string;
	body: string;
	result?: BridgeEnvelope;
	error?: string;
	createdAt: string;
};

type ActionDefinition = {
	id: ActionId;
	label: string;
	description: string;
	hint: string;
	promptPlaceholder?: string;
	group: 'Research' | 'Build' | 'Ops';
};

type ActivityRow = {
	id: string;
	label: string;
	timestamp: string;
	selected: boolean;
	error?: boolean;
};

type LineRow = {
	text: string;
	color?: string;
	bold?: boolean;
};

type LineSegment = {
	text: string;
	color?: string;
	bold?: boolean;
};

const APP_VERSION = '3.8.0';

const actions: ActionDefinition[] = [
	{
		id: 'ask',
		label: 'Ask',
		description: 'LLM research with tool use',
		hint: 'Ask for catalysts, thesis work, risk analysis, or quick synthesis.',
		promptPlaceholder: 'Why is NVDA moving and what changes the thesis?',
		group: 'Research',
	},
	{
		id: 'quote',
		label: 'Quote',
		description: 'Live quote snapshots',
		hint: 'Enter one or more tickers separated by spaces.',
		promptPlaceholder: 'AAPL MSFT NVDA',
		group: 'Research',
	},
	{
		id: 'news',
		label: 'News',
		description: 'Headline digest and catalysts',
		hint: 'Ticker and optional limit, like `AAPL 12`.',
		promptPlaceholder: 'TSLA 8',
		group: 'Research',
	},
	{
		id: 'compare',
		label: 'Compare',
		description: 'Relative performance and quality',
		hint: 'Compare multiple tickers side by side.',
		promptPlaceholder: 'META GOOGL AMZN',
		group: 'Research',
	},
	{
		id: 'chart',
		label: 'Chart',
		description: 'Generate a chart artifact',
		hint: 'Symbol and optional period, like `QQQ 1y`.',
		promptPlaceholder: 'SPY 6mo',
		group: 'Research',
	},
	{
		id: 'backtest',
		label: 'Backtest',
		description: 'Run a built-in strategy',
		hint: 'Ticker, strategy, period. Example: `AAPL sma_crossover 2y`.',
		promptPlaceholder: 'IWM breakout 3y',
		group: 'Research',
	},
	{
		id: 'portfolio',
		label: 'Portfolio',
		description: 'Portfolio construction workflow',
		hint: 'Describe a basket, objective, or optimization need.',
		promptPlaceholder: 'Build a lower-vol growth portfolio with MSFT NVDA TSM ASML',
		group: 'Build',
	},
	{
		id: 'strategy',
		label: 'Strategy',
		description: 'Generate research-driven trade ideas',
		hint: 'Ask for a strategy concept, regime fit, or implementation direction.',
		promptPlaceholder: 'Strategy ideas for GLD in a falling real-yield regime',
		group: 'Build',
	},
	{
		id: 'report',
		label: 'Report',
		description: 'Produce a memo artifact bundle',
		hint: 'Describe the company or thesis you want turned into a report.',
		promptPlaceholder: 'Create an AI infrastructure memo for AMD',
		group: 'Build',
	},
	{
		id: 'alert',
		label: 'Alert',
		description: 'Draft watch levels and triggers',
		hint: 'Describe the name or setup you want monitored.',
		promptPlaceholder: 'Draft pullback and breakout levels for PLTR',
		group: 'Build',
	},
	{
		id: 'status',
		label: 'Status',
		description: 'Provider and routing state',
		hint: 'Refresh provider, model, and health information.',
		group: 'Ops',
	},
	{
		id: 'doctor',
		label: 'Doctor',
		description: 'Dependency and install health',
		hint: 'Check Python, Node, Ollama, and registered backends.',
		group: 'Ops',
	},
	{
		id: 'models',
		label: 'Models',
		description: 'Provider model catalog',
		hint: 'Inspect bundled model suggestions by provider.',
		group: 'Ops',
	},
	{
		id: 'tools',
		label: 'Tools',
		description: 'Registered tool inventory',
		hint: 'List all callable tools available to the model.',
		group: 'Ops',
	},
	{
		id: 'keys',
		label: 'Keys',
		description: 'Key presence overview',
		hint: 'See which providers are configured without exposing secrets.',
		group: 'Ops',
	},
	{
		id: 'shortcuts',
		label: 'Shortcuts',
		description: 'Keyboard map',
		hint: 'Show navigation and control shortcuts.',
		group: 'Ops',
	},
	{
		id: 'setup-help',
		label: 'Setup',
		description: 'Configuration guidance',
		hint: 'Get setup steps for providers, keys, and local models.',
		group: 'Ops',
	},
	{
		id: 'set-provider',
		label: 'Provider',
		description: 'Set the default provider',
		hint: 'Enter a provider id like `openai`, `google`, or `ollama`.',
		promptPlaceholder: 'openai',
		group: 'Ops',
	},
	{
		id: 'set-model',
		label: 'Model',
		description: 'Set the default model',
		hint: 'Enter the exact model id you want persisted.',
		promptPlaceholder: 'gpt-5.4',
		group: 'Ops',
	},
	{
		id: 'set-key',
		label: 'API Key',
		description: 'Persist a provider key',
		hint: 'Enter `provider key`.',
		promptPlaceholder: 'openai sk-...',
		group: 'Ops',
	},
	{
		id: 'reload',
		label: 'Reload',
		description: 'Reload the router from config',
		hint: 'Refresh the in-process routing state after config changes.',
		group: 'Ops',
	},
	{
		id: 'export',
		label: 'Export',
		description: 'Save the current session',
		hint: 'Write a markdown export to `~/.ephemeral/exports`.',
		group: 'Ops',
	},
	{
		id: 'legacy-ui',
		label: 'Legacy UI',
		description: 'Open the Textual shell',
		hint: 'Switch to the older Textual interface.',
		group: 'Ops',
	},
	{
		id: 'help',
		label: 'Help',
		description: 'Show slash commands and tips',
		hint: 'Display the built-in command map.',
		group: 'Ops',
	},
];

const sourceDir = path.dirname(fileURLToPath(import.meta.url));
const defaultProjectRoot = path.resolve(sourceDir, '..', '..', '..');
const bundledPython = path.resolve(
	defaultProjectRoot,
	'.venv',
	process.platform === 'win32' ? path.join('Scripts', 'python.exe') : path.join('bin', 'python'),
);
const pythonExecutable =
	process.env.EPHEMERAL_PYTHON_EXECUTABLE ?? (fs.existsSync(bundledPython) ? bundledPython : 'python3');
const projectRoot = process.env.EPHEMERAL_PROJECT_ROOT ?? defaultProjectRoot;
const smokeTest = process.argv.includes('--smoke-test');
const animationFrames = ['·', '•', '◦', '•'];

const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));
const truncate = (value: string, max: number) => (value.length > max ? `${value.slice(0, max - 1)}…` : value);
const previewValue = (value: unknown, max = 100) => {
	const raw = typeof value === 'string' ? value : JSON.stringify(value);
	return truncate((raw || '').replace(/\s+/g, ' ').trim(), max);
};
const titleCase = (value: string) =>
	value
		.replace(/[_-]+/g, ' ')
		.replace(/\s+/g, ' ')
		.trim()
		.replace(/\b\w/g, character => character.toUpperCase());
const primitiveValue = (value: unknown) => {
	if (value === null || value === undefined || value === '') {
		return 'n/a';
	}
	if (typeof value === 'boolean') {
		return value ? 'yes' : 'no';
	}
	if (typeof value === 'number') {
		return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
	}
	return String(value);
};
const formatStructuredLines = (value: unknown, indent = 0): string[] => {
	const pad = ' '.repeat(indent);
	if (value === null || value === undefined || value === '') {
		return [`${pad}n/a`];
	}
	if (typeof value === 'string') {
		return value.split('\n').map(line => `${pad}${line}`);
	}
	if (typeof value === 'number' || typeof value === 'boolean') {
		return [`${pad}${primitiveValue(value)}`];
	}
	if (Array.isArray(value)) {
		if (!value.length) {
			return [`${pad}none`];
		}
		return value.flatMap(item => {
			if (item === null || item === undefined || typeof item !== 'object') {
				return [`${pad}- ${primitiveValue(item)}`];
			}

			const rows = Object.entries(item).filter(([, child]) => child !== undefined && child !== null && child !== '');
			if (!rows.length) {
				return [`${pad}- n/a`];
			}

			const [[firstKey, firstValue], ...rest] = rows;
			return [
				`${pad}- ${titleCase(firstKey)}: ${primitiveValue(firstValue)}`,
				...rest.flatMap(([childKey, childValue]) => {
					if (childValue === undefined || childValue === null || childValue === '') {
						return [];
					}
					if (typeof childValue === 'object') {
						return [`${pad}  ${titleCase(childKey)}`, ...formatStructuredLines(childValue, indent + 4)];
					}
					return [`${pad}  ${titleCase(childKey)}: ${primitiveValue(childValue)}`];
				}),
			];
		});
	}

	const rows = Object.entries(value as Record<string, unknown>).filter(([, child]) => child !== undefined && child !== null && child !== '');
	if (!rows.length) {
		return [`${pad}n/a`];
	}

	return rows.flatMap(([key, child]) => {
		if (typeof child === 'object') {
			return [`${pad}${titleCase(key)}`, ...formatStructuredLines(child, indent + 2)];
		}
		return [`${pad}${titleCase(key)}: ${primitiveValue(child)}`];
	});
};
const formatStructuredBlock = (value: unknown) => formatStructuredLines(value).join('\n');
const joinSections = (...sections: Array<string | undefined>) => sections.filter(Boolean).join('\n\n');
const repeat = (character: string, count: number) => character.repeat(Math.max(0, count));
const padRows = (rows: LineRow[], height: number) => {
	const padded = [...rows];
	while (padded.length < height) {
		padded.push({text: ''});
	}
	return padded.slice(0, height);
};
const pickGroupColor = (group: ActionDefinition['group']) => {
	if (group === 'Research') return 'cyanBright';
	if (group === 'Build') return 'yellow';
	return 'green';
};
const renderStyledLine = (line: string, accentColor = 'cyanBright'): React.ReactNode => {
	const trimmed = line.trim();
	if (!trimmed) {
		return <Text wrap="truncate-end">{' '}</Text>;
	}

	if (/^\[ok\]/i.test(trimmed)) {
		return (
			<Text wrap="truncate-end">
				<Text color="green" bold>
					[ok]
				</Text>
				<Text color="gray"> {trimmed.replace(/^\[ok\]\s*/i, '')}</Text>
			</Text>
		);
	}

	if (/^\[x\]/i.test(trimmed)) {
		return (
			<Text wrap="truncate-end">
				<Text color="red" bold>
					[x]
				</Text>
				<Text color="gray"> {trimmed.replace(/^\[x\]\s*/i, '')}</Text>
			</Text>
		);
	}

	if (/^\d+\.\s/.test(trimmed)) {
		const [, marker, rest] = trimmed.match(/^(\d+\.)\s+(.*)$/) ?? [];
		if (marker && rest) {
			return (
				<Text wrap="truncate-end">
					<Text color={accentColor} bold>
						{marker}
					</Text>
					<Text color="white"> {rest}</Text>
				</Text>
			);
		}
	}

	if (/^-\s/.test(trimmed)) {
		return (
			<Text wrap="truncate-end">
				<Text color={accentColor} bold>
					{'>'}
				</Text>
				<Text color="white"> {trimmed.replace(/^-\s*/, '')}</Text>
			</Text>
				);
	}

	if (/^[A-Z][A-Za-z ]+$/.test(trimmed) && trimmed.length < 28) {
		return (
			<Text color={accentColor} bold wrap="truncate-end">
				{trimmed}
			</Text>
		);
	}

	const keyValueMatch = line.match(/^(\s*[A-Za-z][A-Za-z0-9 /_-]{1,20})(\s{2,}|\s*:\s)(.+)$/);
	if (keyValueMatch) {
		const [, label, separator, value] = keyValueMatch;
		return (
			<Text wrap="truncate-end">
				<Text color="gray">{label.trimEnd()}</Text>
				<Text color="gray">{separator.includes(':') ? ': ' : '  '}</Text>
				<Text color="white">{value}</Text>
			</Text>
		);
	}

	const slashIndex = line.indexOf('/');
	if (slashIndex >= 0 && /\/[a-z]/i.test(line.slice(slashIndex))) {
		const match = line.match(/(.*?)(\/[A-Za-z0-9_-]+.*)/);
		if (match) {
			return (
				<Text wrap="truncate-end">
					<Text color="white">{match[1]}</Text>
					<Text color={accentColor} bold>
						{match[2]}
					</Text>
				</Text>
			);
		}
	}

	return <Text color="white" wrap="truncate-end">{line}</Text>;
};

const wrapText = (input: string, width: number): string[] => {
	const lines = input.replace(/\t/g, '  ').split('\n');
	const output: string[] = [];
	const safeWidth = Math.max(12, width);

	for (const line of lines) {
		if (!line) {
			output.push('');
			continue;
		}

		let remaining = line;
		while (remaining.length > safeWidth) {
			const slice = remaining.slice(0, safeWidth);
			const breakAt = slice.lastIndexOf(' ');
			const boundary = breakAt > safeWidth * 0.55 ? breakAt : safeWidth;
			output.push(remaining.slice(0, boundary).trimEnd());
			remaining = remaining.slice(boundary).trimStart();
		}
		output.push(remaining);
	}

	return output;
};

const viewportLines = (input: string, width: number, height: number, scrollOffset: number) => {
	const allLines = wrapText(input, width);
	const safeHeight = Math.max(1, height);
	const maxOffset = Math.max(0, allLines.length - safeHeight);
	const start = clamp(scrollOffset, 0, maxOffset);
	const visible = allLines.slice(start, start + safeHeight);
	const padded = [...visible];

	while (padded.length < safeHeight) {
		padded.push('');
	}

	return {
		lines: padded,
		total: allLines.length,
		offset: start,
		maxOffset,
	};
};

const buildExportHistory = (history: HistoryEntry[]) =>
	history
		.slice()
		.reverse()
		.map(entry => ({
			label: entry.label,
			input: entry.input,
			body: entry.body,
			error: entry.error ?? '',
		}));

const parseSlashCommand = (raw: string): BridgeRequest | null => {
	const trimmed = raw.trim();
	if (!trimmed.startsWith('/')) {
		return null;
	}

	const [command, ...rest] = trimmed.slice(1).split(/\s+/);
	const joined = rest.join(' ');
	switch (command) {
		case 'help':
			return {action: 'help'};
		case 'shortcuts':
			return {action: 'shortcuts'};
		case 'keys':
			return {action: 'keys'};
		case 'ask':
			return {action: 'ask', query: joined};
		case 'quote':
			return {action: 'quote', symbols: rest};
		case 'news':
		case 'digest': {
			const maybeLimit = Number(rest.at(-1));
			return {
				action: 'news',
				symbol: rest[0] ?? '',
				limit: Number.isFinite(maybeLimit) ? maybeLimit : 10,
				query: '',
			};
		}
		case 'compare':
			return {action: 'compare', symbols: rest};
		case 'chart':
			return {action: 'chart', symbol: rest[0] ?? '', period: rest[1] ?? '6mo'};
		case 'backtest':
			return {
				action: 'backtest',
				symbol: rest[0] ?? '',
				strategy: rest[1] ?? 'sma_crossover',
				period: rest[2] ?? '1y',
			};
		case 'portfolio':
			return {action: 'portfolio', query: joined || 'Build a resilient growth portfolio with MSFT NVDA TSM ASML'};
		case 'strategy':
			return {action: 'strategy', query: joined || 'Generate strategy ideas for GLD in a falling real-yield regime'};
		case 'report':
			return {action: 'report', query: joined || 'Create an AI infrastructure memo for AMD'};
		case 'alert':
		case 'watchlist':
			return {action: 'alert', query: joined || 'Draft pullback and breakout levels for PLTR'};
		case 'status':
			return {action: 'status'};
		case 'doctor':
			return {action: 'doctor'};
		case 'models':
			return {action: 'models'};
		case 'tools':
			return {action: 'tools'};
		case 'provider':
			return rest.length > 0 ? {action: 'set-provider', provider: rest[0] ?? ''} : {action: 'status'};
		case 'model':
			return rest.length > 0 ? {action: 'set-model', model: joined} : {action: 'models'};
		case 'setkey':
			return {action: 'set-key', provider: rest[0] ?? '', key: rest.slice(1).join(' ')};
		case 'reload':
			return {action: 'reload'};
		case 'setup-help':
		case 'preset':
			return {action: 'setup-help'};
		case 'export':
			return {action: 'export'};
		case 'legacy':
			return {action: 'legacy-ui'};
		default:
			return {action: 'ask', query: trimmed.slice(1)};
	}
};

const requestForAction = (selectedAction: ActionDefinition, rawInput: string): BridgeRequest => {
	const input = rawInput.trim();
	switch (selectedAction.id) {
		case 'help':
		case 'shortcuts':
		case 'keys':
		case 'status':
		case 'doctor':
		case 'models':
		case 'tools':
		case 'reload':
		case 'setup-help':
		case 'export':
		case 'legacy-ui':
			return {action: selectedAction.id};
		case 'ask':
			return {action: 'ask', query: input};
		case 'quote':
			return {action: 'quote', symbols: input.split(/[,\s]+/).filter(Boolean)};
		case 'news': {
			const parts = input.split(/[,\s]+/).filter(Boolean);
			const maybeLimit = Number(parts.at(-1));
			return {
				action: 'news',
				symbol: parts[0] ?? '',
				limit: Number.isFinite(maybeLimit) ? maybeLimit : 10,
				query: '',
			};
		}
		case 'compare':
			return {action: 'compare', symbols: input.split(/[,\s]+/).filter(Boolean)};
		case 'chart': {
			const parts = input.split(/[,\s]+/).filter(Boolean);
			return {action: 'chart', symbol: parts[0] ?? '', period: parts[1] ?? '6mo'};
		}
		case 'backtest': {
			const parts = input.split(/[,\s]+/).filter(Boolean);
			return {
				action: 'backtest',
				symbol: parts[0] ?? '',
				strategy: parts[1] ?? 'sma_crossover',
				period: parts[2] ?? '1y',
			};
		}
		case 'portfolio':
		case 'strategy':
		case 'report':
		case 'alert':
			return {action: selectedAction.id, query: input};
		case 'set-provider':
			return {action: 'set-provider', provider: input};
		case 'set-model':
			return {action: 'set-model', model: input};
		case 'set-key': {
			const [provider, ...rest] = input.split(/\s+/);
			return {action: 'set-key', provider: provider ?? '', key: rest.join(' ')};
		}
	}
};

type PendingBridgeRequest = {
	resolve: (result: BridgeEnvelope) => void;
	reject: (error: Error) => void;
};

class PersistentBridgeClient {
	private child = spawn(pythonExecutable, ['-m', 'ephemeral.ink_bridge', '--server'], {
		cwd: projectRoot,
		env: process.env,
		stdio: ['pipe', 'pipe', 'pipe'],
	});

	private buffer = '';
	private stderr = '';
	private nextId = 0;
	private closed = false;
	private pending = new Map<string, PendingBridgeRequest>();

	constructor() {
		this.child.stdout.on('data', chunk => {
			this.buffer += String(chunk);
			this.flushBuffer();
		});

		this.child.stderr.on('data', chunk => {
			this.stderr += String(chunk);
		});

		this.child.on('error', error => {
			this.failAll(error.message);
		});

		this.child.on('close', code => {
			this.closed = true;
			if (bridgeClient === this) {
				bridgeClient = null;
			}
			this.failAll(this.stderr.trim() || `Bridge exited with code ${code ?? 'unknown'}`);
		});
	}

	isClosed() {
		return this.closed;
	}

	request(request: BridgeRequest): Promise<BridgeEnvelope> {
		if (this.closed || this.child.stdin.destroyed) {
			return Promise.reject(new Error('Bridge is not available.'));
		}

		const id = `bridge-${++this.nextId}`;
		return new Promise((resolve, reject) => {
			this.pending.set(id, {resolve, reject});
			this.child.stdin.write(`${JSON.stringify({id, payload: request})}\n`, error => {
				if (!error) {
					return;
				}
				this.pending.delete(id);
				reject(error);
			});
		});
	}

	close() {
		if (this.closed) {
			return;
		}

		this.closed = true;
		this.child.kill();
	}

	private flushBuffer() {
		let newlineIndex = this.buffer.indexOf('\n');
		while (newlineIndex >= 0) {
			const line = this.buffer.slice(0, newlineIndex).trim();
			this.buffer = this.buffer.slice(newlineIndex + 1);
			if (line) {
				this.resolvePacket(line);
			}
			newlineIndex = this.buffer.indexOf('\n');
		}
	}

	private resolvePacket(line: string) {
		let packet: BridgeEnvelope;
		try {
			packet = JSON.parse(line) as BridgeEnvelope;
		} catch {
			this.failAll(`Invalid bridge response: ${line}\n${this.stderr}`);
			return;
		}

		const packetId = packet.id;
		if (!packetId) {
			return;
		}

		const pending = this.pending.get(packetId);
		if (!pending) {
			return;
		}
		this.pending.delete(packetId);

		if (!packet.ok) {
			pending.reject(new Error(packet.error ?? 'Bridge request failed.'));
			return;
		}

		pending.resolve(packet);
	}

	private failAll(message: string) {
		if (bridgeClient === this) {
			bridgeClient = null;
		}

		for (const [id, pending] of this.pending.entries()) {
			this.pending.delete(id);
			pending.reject(new Error(message));
		}
	}
}

let bridgeClient: PersistentBridgeClient | null = null;
let bridgeCleanupRegistered = false;

const getBridgeClient = () => {
	if (!bridgeClient || bridgeClient.isClosed()) {
		bridgeClient = new PersistentBridgeClient();
	}

	if (!bridgeCleanupRegistered) {
		bridgeCleanupRegistered = true;
		process.on('exit', () => {
			bridgeClient?.close();
		});
	}

	return bridgeClient;
};

const invokeBridge = async (request: BridgeRequest): Promise<BridgeEnvelope> => getBridgeClient().request(request);

const renderToolCalls = (toolCalls: any[]) => {
	if (!toolCalls?.length) {
		return '';
	}

	return [
		'Tool calls',
		...toolCalls.map((toolCall, index) => {
			const name = toolCall?.name ?? `tool-${index + 1}`;
			const args = previewValue(toolCall?.args ?? {}, 78);
			const result = previewValue(toolCall?.result ?? {}, 110);
			return `${index + 1}. ${name}\n   args   ${args}\n   result ${result}`;
		}),
	].join('\n');
};

const summarizeEnvelope = (result: BridgeEnvelope): string => {
	const action = result.action;
	const payload = result.data ?? {};

	switch (action) {
		case 'ask':
			return truncate(String(payload?.response ?? 'No response returned.'), 160);
		case 'status':
			return `Provider ${payload?.provider ?? 'n/a'}\nModel ${payload?.model ?? 'n/a'}\nState ${payload?.needs_setup ? 'setup needed' : 'ready'}`;
		case 'doctor':
			return `Doctor checks ${(payload?.checks ?? []).length}\nBackends ${(payload?.router_backends ?? []).join(', ') || 'none'}`;
		case 'quote':
			return (payload?.quotes ?? []).map((quote: any) => `${quote.symbol} ${quote.price}`).join('\n');
		case 'news':
			return (payload?.articles ?? []).slice(0, 3).map((article: any) => article.title ?? 'Untitled').join('\n');
		case 'compare':
			return `Best ${payload?.best_performer ?? 'n/a'}\nWorst ${payload?.worst_performer ?? 'n/a'}`;
		case 'chart':
			return `Chart saved to ${payload?.chart_path ?? 'n/a'}`;
		case 'backtest':
			return `Strategy ${payload?.result?.strategy ?? 'n/a'}\nReturn ${payload?.result?.performance?.total_return ?? 'n/a'}`;
		case 'export':
			return `Exported to ${payload?.path ?? 'unknown path'}`;
		case 'set-key':
			return `Saved key for ${payload?.provider ?? 'provider'}`;
		case 'set-provider':
		case 'set-model':
			return 'Updated configuration';
		default:
			return previewValue(payload, 160);
	}
};

const detailBodyForEntry = (entry: HistoryEntry, detailMode: DetailMode): string => {
	if (entry.error) {
		return `Request failed\n\n${entry.error}`;
	}

	if (!entry.result) {
		return entry.body;
	}

	if (detailMode === 'raw') {
		return JSON.stringify(entry.result.data ?? {}, null, 2);
	}

	const action = entry.result.action;
	const payload = entry.result.data ?? {};

	switch (action) {
		case 'help':
			return joinSections(
				payload?.body ?? 'Ephemeral help',
				['Slash commands', ...((payload?.slash_commands ?? []) as string[])].join('\n'),
				['Tips', ...((payload?.tips ?? []) as string[]).map((tip: string) => `- ${tip}`)].join('\n'),
			);
		case 'shortcuts':
			return ((payload?.items ?? []) as any[]).map(item => `${item.key.padEnd(12)} ${item.action}`).join('\n');
		case 'keys':
			return joinSections(
				`Configured providers: ${payload?.configured ?? 0}`,
				((payload?.rows ?? []) as any[]).map(row => `${String(row.provider).padEnd(14)} ${row.status}`).join('\n'),
			);
		case 'status':
			return [
				`Provider      ${payload?.provider ?? 'n/a'}`,
				`Model         ${payload?.model ?? 'n/a'}`,
				`Setup         ${payload?.needs_setup ? 'required' : 'ready'}`,
				`Backends      ${(payload?.health?.router_backends ?? []).join(', ') || 'none'}`,
				payload?.ollama?.reachable ? `Ollama       ${payload?.ollama?.host ?? 'reachable'}` : `Ollama       unavailable`,
				payload?.ollama?.installed_models?.length ? `Installed    ${payload.ollama.installed_models.join(', ')}` : '',
				'',
				'Checks',
				...((payload?.health?.checks ?? []) as any[]).map(check => `${check.ok ? '[ok]' : '[x] '} ${check.name} ${check.detail ?? ''}`.trim()),
			]
				.filter(Boolean)
				.join('\n');
		case 'doctor':
			return [
				'Doctor',
				...((payload?.checks ?? []) as any[]).map(check => `${check.ok ? '[ok]' : '[x] '} ${check.name} ${check.detail ?? ''}`.trim()),
				'',
				`Router backends: ${(payload?.router_backends ?? []).join(', ') || 'none'}`,
			].join('\n');
		case 'ask':
			return joinSections(String(payload?.response ?? 'No response returned.').trim(), renderToolCalls(payload?.tool_calls ?? []));
		case 'quote':
			return ((payload?.quotes ?? []) as any[])
				.map(quote => {
					if (quote.error) {
						return `${quote.symbol ?? 'symbol'}\n  error   ${quote.error}`;
					}

					const change = Number(quote.change_percent ?? 0);
					const prefix = change >= 0 ? '+' : '';
					return `${quote.symbol}\n  price   $${Number(quote.price ?? 0).toFixed(2)}\n  move    ${prefix}${change.toFixed(2)}%\n  volume  ${Number(quote.volume ?? 0).toLocaleString()}`;
				})
				.join('\n\n');
		case 'news':
			return joinSections(
				`Source: ${payload?.source_used ?? 'unknown'}`,
				((payload?.articles ?? []) as any[])
					.slice(0, 10)
					.map(
						(article, index) =>
							`${index + 1}. ${article.title ?? 'Untitled'}\n   ${(article.source ?? article.publisher ?? 'unknown source').toString()}${article.url ? ` · ${article.url}` : ''}`,
					)
					.join('\n\n'),
			);
		case 'compare':
			return [
				`Period: ${payload?.period ?? 'n/a'}`,
				`Best:   ${payload?.best_performer ?? 'n/a'}`,
				`Worst:  ${payload?.worst_performer ?? 'n/a'}`,
				'',
				...((payload?.comparison ?? []) as any[]).map(
					row =>
						`${String(row.symbol ?? '').padEnd(6)} return ${String(Number(row.total_return ?? 0).toFixed(2)).padStart(7)}%  sharpe ${String(Number(row.sharpe ?? 0).toFixed(2)).padStart(5)}`,
				),
			].join('\n');
		case 'chart':
			return [
				`Chart path: ${payload?.chart_path ?? 'n/a'}`,
				payload?.symbol ? `Symbol:     ${payload.symbol}` : '',
				payload?.symbols ? `Symbols:    ${payload.symbols.join(', ')}` : '',
				`Period:     ${payload?.period ?? 'n/a'}`,
			]
				.filter(Boolean)
				.join('\n');
		case 'backtest':
			return formatStructuredBlock(payload?.result ?? payload);
		case 'portfolio':
		case 'strategy':
		case 'report':
		case 'alert':
			return formatStructuredBlock(payload?.engine_result ?? payload);
		case 'models':
			return [
				`Default provider ${payload?.default_provider ?? 'n/a'}`,
				`Default model    ${payload?.default_model ?? 'n/a'}`,
				'',
				...Object.entries(payload?.providers ?? {}).flatMap(([provider, models]) => [
					`${titleCase(provider)}`,
					...((models as string[]).map(model => `  - ${model}`) || ['  - none']),
					'',
				]),
			].join('\n');
		case 'tools':
			return ((payload?.tools ?? []) as string[]).map((tool, index) => `${index + 1}. ${tool}`).join('\n');
		case 'setup-help':
			return [
				'Setup',
				...((payload?.steps ?? []) as string[]).map((step, index) => `${index + 1}. ${step}`),
				'',
				payload?.docs_url ?? '',
			].join('\n');
		case 'reload':
			return joinSections('Router reloaded', formatStructuredBlock(payload?.status ?? payload));
		case 'export':
			return `Export complete\n\nPath: ${payload?.path ?? 'n/a'}\nCharacters: ${payload?.characters ?? 0}`;
		default:
			return entry.body || JSON.stringify(payload, null, 2);
	}
};

const useTerminalSize = () => {
	const {stdout} = useStdout();
	const [dimensions, setDimensions] = useState(() => ({
		width: stdout?.columns ?? process.stdout.columns ?? 120,
		height: stdout?.rows ?? process.stdout.rows ?? 40,
	}));

	useEffect(() => {
		const stream = stdout ?? process.stdout;
		const update = () => {
			setDimensions({
				width: stream?.columns ?? process.stdout.columns ?? 120,
				height: stream?.rows ?? process.stdout.rows ?? 40,
			});
		};

		update();
		stream?.on?.('resize', update);
		return () => {
			stream?.off?.('resize', update);
		};
	}, [stdout]);

	return dimensions;
};

const useRawMode = () => {
	const stdinControls = useStdin();

	useEffect(() => {
		const supportCheck = stdinControls?.isRawModeSupported;
		const supported = typeof supportCheck === 'boolean' ? supportCheck : true;

		if (smokeTest || !supported || typeof stdinControls?.setRawMode !== 'function') {
			return;
		}

		stdinControls.setRawMode(true);
		return () => {
			stdinControls.setRawMode(false);
		};
	}, [stdinControls]);
};

type KeyboardControllerProps = {
	busy: boolean;
	focusPane: FocusPane;
	historyLength: number;
	input: string;
	onRun: (currentInput: string) => void;
	outputViewportHeight: number;
	setDetailMode: React.Dispatch<React.SetStateAction<DetailMode>>;
	setFocusPane: React.Dispatch<React.SetStateAction<FocusPane>>;
	setInput: React.Dispatch<React.SetStateAction<string>>;
	setOutputScroll: React.Dispatch<React.SetStateAction<number>>;
	setSelectedActionIndex: React.Dispatch<React.SetStateAction<number>>;
	setSelectedHistoryIndex: React.Dispatch<React.SetStateAction<number>>;
	exit: () => void;
};

const InteractiveKeyboardController = ({
	busy,
	focusPane,
	historyLength,
	input,
	onRun,
	outputViewportHeight,
	setDetailMode,
	setFocusPane,
	setInput,
	setOutputScroll,
	setSelectedActionIndex,
	setSelectedHistoryIndex,
	exit,
}: KeyboardControllerProps) => {
	useInput((value, key) => {
		if (key.ctrl && value === 'c') {
			exit();
			return;
		}

		if (key.tab) {
			setFocusPane(previous => {
				if (previous === 'actions') return 'history';
				if (previous === 'history') return 'output';
				if (previous === 'output') return 'input';
				return 'actions';
			});
			return;
		}

		if (key.leftArrow) {
			if (focusPane === 'input' && input.length > 0) {
				return;
			}
			setFocusPane(previous => {
				if (previous === 'input') return 'output';
				if (previous === 'output') return 'history';
				if (previous === 'history') return 'actions';
				return 'actions';
			});
			return;
		}

		if (key.rightArrow) {
			if (focusPane === 'input' && input.length > 0) {
				return;
			}
			setFocusPane(previous => {
				if (previous === 'actions') return 'history';
				if (previous === 'history') return 'output';
				if (previous === 'output') return 'input';
				return 'input';
			});
			return;
		}

		if (key.ctrl && value === 'l') {
			setSelectedHistoryIndex(0);
			setOutputScroll(0);
			return;
		}

		if (key.escape) {
			setInput('');
			setFocusPane('input');
			return;
		}

		if (key.downArrow && focusPane === 'input' && !input.trim()) {
			setSelectedActionIndex(previous => (previous + 1) % actions.length);
			return;
		}

		if (key.upArrow && focusPane === 'input' && !input.trim()) {
			setSelectedActionIndex(previous => (previous - 1 + actions.length) % actions.length);
			return;
		}

		if ((value === 'j' || key.downArrow) && focusPane !== 'input') {
			if (focusPane === 'actions') {
				setSelectedActionIndex(previous => (previous + 1) % actions.length);
				return;
			}
			if (focusPane === 'history') {
				setSelectedHistoryIndex(previous => Math.min(Math.max(historyLength - 1, 0), previous + 1));
				return;
			}
			if (focusPane === 'output') {
				setOutputScroll(previous => previous + Math.max(1, Math.floor(outputViewportHeight / 3)));
				return;
			}
		}

		if ((value === 'k' || key.upArrow) && focusPane !== 'input') {
			if (focusPane === 'actions') {
				setSelectedActionIndex(previous => (previous - 1 + actions.length) % actions.length);
				return;
			}
			if (focusPane === 'history') {
				setSelectedHistoryIndex(previous => Math.max(0, previous - 1));
				return;
			}
			if (focusPane === 'output') {
				setOutputScroll(previous => Math.max(0, previous - Math.max(1, Math.floor(outputViewportHeight / 3))));
				return;
			}
		}

		if (value === '[') {
			setOutputScroll(previous => Math.max(0, previous - Math.max(1, outputViewportHeight - 2)));
			return;
		}

		if (value === ']') {
			setOutputScroll(previous => previous + Math.max(1, outputViewportHeight - 2));
			return;
		}

		if (value.toLowerCase() === 'd' && !input.trim()) {
			setDetailMode(previous => (previous === 'rendered' ? 'raw' : 'rendered'));
			return;
		}

		if (key.return) {
			if (busy) {
				return;
			}
			onRun(input);
			return;
		}

		if (key.backspace || key.delete) {
			setFocusPane('input');
			setInput(previous => previous.slice(0, -1));
			return;
		}

		if (!key.ctrl && !key.meta && value && !/[\r\n\t]/.test(value)) {
			setFocusPane('input');
			setInput(previous => previous + value);
		}
	});

	return null;
};

const Divider = ({width}: {width: number}) => <Text color="gray">{repeat('-', Math.max(8, width))}</Text>;

const App = () => {
	const {exit} = useApp();
	useRawMode();

	const {width: terminalWidth, height: terminalHeight} = useTerminalSize();
	const [frameIndex, setFrameIndex] = useState(0);
	const [selectedActionIndex, setSelectedActionIndex] = useState(0);
	const [selectedHistoryIndex, setSelectedHistoryIndex] = useState(0);
	const [focusPane, setFocusPane] = useState<FocusPane>('input');
	const [detailMode, setDetailMode] = useState<DetailMode>('rendered');
	const [input, setInput] = useState('');
	const [busy, setBusy] = useState(false);
	const [history, setHistory] = useState<HistoryEntry[]>([]);
	const [statusSnapshot, setStatusSnapshot] = useState<any>(null);
	const [outputScroll, setOutputScroll] = useState(0);
	const [pendingLabel, setPendingLabel] = useState<string | null>(null);
	const [statusLoading, setStatusLoading] = useState(true);

	const selectedAction = actions[selectedActionIndex]!;
	const selectedEntry = history[selectedHistoryIndex] ?? null;

	useEffect(() => {
		if (smokeTest) {
			return;
		}

		const timer = setInterval(() => {
			setFrameIndex(previous => (previous + 1) % animationFrames.length);
		}, 220);
		return () => clearInterval(timer);
	}, []);

	const pushEntry = (entry: HistoryEntry) => {
		setHistory(previous => [entry, ...previous].slice(0, 18));
		setSelectedHistoryIndex(0);
		setOutputScroll(0);
	};

	const runRequest = async (request: BridgeRequest, sourceLabel: string, currentInput: string) => {
		const effectiveRequest = request.action === 'export' ? {...request, history: buildExportHistory(history)} : request;
		setBusy(true);
		setPendingLabel(sourceLabel);

		try {
			if (effectiveRequest.action === 'legacy-ui') {
				exit();
				const child = spawn(pythonExecutable, ['-m', 'ephemeral.cli', '--legacy-ui'], {
					cwd: projectRoot,
					env: process.env,
					stdio: 'inherit',
				});
				child.on('close', code => process.exit(code ?? 0));
				return;
			}

			const result = await invokeBridge(effectiveRequest);
			pushEntry({
				id: `${Date.now()}-${Math.random()}`,
				label: sourceLabel,
				input: currentInput.trim(),
				body: summarizeEnvelope(result),
				result,
				createdAt: new Date().toLocaleTimeString(),
			});

			if (
				effectiveRequest.action === 'status' ||
				effectiveRequest.action === 'doctor' ||
				effectiveRequest.action === 'reload' ||
				effectiveRequest.action === 'set-provider' ||
				effectiveRequest.action === 'set-model'
			) {
				setStatusSnapshot(result.data);
			}

			if (smokeTest) {
				process.exit(0);
			}
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);
			pushEntry({
				id: `${Date.now()}-${Math.random()}`,
				label: sourceLabel,
				input: currentInput.trim(),
				body: errorMessage,
				error: errorMessage,
				createdAt: new Date().toLocaleTimeString(),
			});
			if (smokeTest) {
				console.error(`Smoke test failed: ${errorMessage}`);
				process.exit(1);
			}
		} finally {
			setBusy(false);
			setPendingLabel(null);
		}
	};

	const handleRun = (currentInput: string) => {
		const slashRequest = parseSlashCommand(currentInput);
		const request = slashRequest ?? requestForAction(selectedAction, currentInput);
		const sourceLabel = slashRequest ? `Command ${currentInput.trim()}` : selectedAction.label;
		void runRequest(request, sourceLabel, currentInput);
		setInput('');
		setFocusPane('output');
	};

	useEffect(() => {
		if (smokeTest) {
			return;
		}

		setStatusLoading(true);
		void invokeBridge({action: 'status'})
			.then(result => {
				setStatusSnapshot(result.data);
			})
			.catch(() => undefined)
			.finally(() => {
				setStatusLoading(false);
			});
	}, []);

	const layoutMode: LayoutMode = terminalWidth >= 120 && terminalHeight >= 24 ? 'desktop' : 'stacked';
	const sidebarWidth = layoutMode === 'desktop' ? clamp(Math.floor(terminalWidth * 0.24), 26, 30) : terminalWidth - 2;
	const mainWidth = layoutMode === 'desktop' ? Math.max(terminalWidth - sidebarWidth - 5, 60) : terminalWidth - 2;
	const bodyHeight = clamp(terminalHeight - (layoutMode === 'desktop' ? 9 : 14), 10, 40);
	const outputViewportHeight = Math.max(6, bodyHeight - 5);
	const outputViewportWidth = Math.max(32, mainWidth - 2);
	const activityVisible = layoutMode === 'desktop' ? 5 : 4;

	const metrics = useMemo(() => {
		const snapshot = statusSnapshot?.status ?? statusSnapshot ?? {};
		const routerBackends = (snapshot.health?.router_backends ?? snapshot.router_backends ?? []) as string[];
		return {
			provider: snapshot.provider ?? 'n/a',
			model: snapshot.model ?? 'n/a',
			backends: String(routerBackends.length || 0),
			state: snapshot.needs_setup ? 'setup' : 'ready',
			installedModels: snapshot.ollama?.installed_models ?? [],
			host: snapshot.ollama?.host ?? 'n/a',
			localReady: Boolean(snapshot.local_ready ?? snapshot.ollama?.current_model_available),
		};
	}, [statusSnapshot]);

	const activityRows: ActivityRow[] = useMemo(() => {
		if (history.length === 0) {
			return [];
		}
		return history.slice(0, activityVisible).map((entry, index) => ({
			id: entry.id,
			label: truncate(entry.label, 24),
			timestamp: entry.error ? 'error' : entry.createdAt,
			selected: index === selectedHistoryIndex,
			error: Boolean(entry.error),
		}));
	}, [activityVisible, history, selectedHistoryIndex]);

	const selectedBody = selectedEntry
		? detailBodyForEntry(selectedEntry, detailMode)
		: busy && pendingLabel
			? [
					`${pendingLabel} is running.`,
					'',
					'The request is executing in the background while the shell stays interactive.',
					'Recent runs stay in the sidebar and the prompt becomes available again as soon as the job completes.',
				].join('\n')
			: [
					'Ephemeral turns one command into market context, tools, and execution.',
					'Use the left rail to move between workflows, keep the workspace focused on one result, and let the composer drive the session.',
					'',
					'Best starting points',
					'- Ask for a catalyst read, thesis update, or risk check',
					'- Compare a basket, open live news, or chart a setup',
					'- Draft a portfolio, memo, strategy, or alert without leaving the shell',
					'',
					'Fast paths',
					'- /status for routing health and local model readiness',
					`- ${selectedAction.promptPlaceholder ?? selectedAction.hint}`,
				].join('\n');
	const viewport = viewportLines(selectedBody, outputViewportWidth, outputViewportHeight, outputScroll);

	const workspaceStatus = selectedEntry ? selectedEntry.label : pendingLabel ?? selectedAction.label;
	const workspaceSubtitle = selectedEntry?.input
		? `input · ${truncate(selectedEntry.input, Math.max(28, outputViewportWidth - 10))}`
		: detailMode === 'raw'
			? 'raw payload'
			: selectedAction.description;

	const promptCursor = focusPane === 'input' ? '▏' : '';
	const promptCursorColor = frameIndex % 2 === 0 ? 'cyanBright' : 'blue';
	const promptStatus = busy ? 'running' : 'ready';
	const promptHint = input.trim()
		? selectedAction.hint
		: selectedAction.promptPlaceholder ?? 'Use natural language or slash commands like /quote AAPL';
	const shellStatus = busy ? `running ${pendingLabel ?? 'request'}` : statusLoading ? 'syncing state' : `${metrics.provider} · ${metrics.model}`;
	const sidebarFocused = focusPane === 'actions' || focusPane === 'history';
	const dividerWidth = Math.min(terminalWidth - 8, 72);
	const headerTone = busy ? 'yellow' : statusLoading ? 'blue' : 'green';
	const actionAccent = pickGroupColor(selectedAction.group);
	const topStatusLine = `${selectedAction.group} · ${selectedAction.label} · ${metrics.localReady ? 'local ready' : 'setup path'}`;

	const sidebarRows = useMemo(() => {
		const rows: LineRow[] = [
			{text: 'NAVIGATOR', color: sidebarFocused ? actionAccent : 'gray', bold: true},
			{text: `${metrics.provider} · ${truncate(String(metrics.model), 20)}`, color: 'gray'},
			{text: ''},
		];

		for (const group of ['Research', 'Build', 'Ops'] as const) {
			rows.push({
				text: group.toUpperCase(),
				color: selectedAction.group === group ? pickGroupColor(group) : 'gray',
				bold: true,
			});
			for (const action of actions.filter(item => item.group === group)) {
				const selected = action.id === selectedAction.id;
				rows.push({
					text: `${selected ? '>' : ' '} ${action.label}`,
					color: selected ? pickGroupColor(group) : 'white',
					bold: selected,
				});
			}
			rows.push({text: ''});
		}

		rows.push({text: 'RECENT', color: focusPane === 'history' ? 'cyanBright' : 'gray', bold: true});
		if (activityRows.length) {
			for (const row of activityRows) {
				rows.push({
					text: `${row.selected ? '>' : ' '} ${truncate(row.label, 16)} · ${row.timestamp}`,
					color: row.selected ? 'cyanBright' : row.error ? 'red' : 'gray',
					bold: row.selected,
				});
			}
		} else {
			rows.push({text: 'No runs yet', color: 'gray'});
		}

		rows.push({text: ''});
		rows.push({text: `${metrics.localReady ? 'Local ready' : 'Local warming'} · ${metrics.state}`, color: metrics.localReady ? 'green' : 'yellow'});
		if (metrics.host !== 'n/a') {
			rows.push({text: truncate(metrics.host, sidebarWidth - 1), color: 'gray'});
		}
		rows.push({text: `Focus ${focusPane} · ${selectedEntry ? detailMode : 'workspace'}`, color: 'gray'});
		return padRows(rows, bodyHeight);
	}, [actionAccent, activityRows, bodyHeight, focusPane, metrics.host, metrics.localReady, metrics.model, metrics.provider, metrics.state, selectedAction.group, selectedAction.id, selectedEntry, detailMode, sidebarFocused, sidebarWidth]);

	const workspaceRows = useMemo(
		() =>
			padRows(
				[
					{text: workspaceStatus, color: focusPane === 'output' ? 'cyanBright' : 'white', bold: true},
					{text: workspaceSubtitle, color: 'gray'},
					{text: ''},
					...viewport.lines.map(line => ({text: line || ' '})),
					{text: ''},
					{
						text:
							viewport.total > viewport.lines.length
								? `scroll ${viewport.offset + 1}-${Math.min(viewport.offset + viewport.lines.length, viewport.total)} of ${viewport.total} · ${detailMode}`
								: `${detailMode} view · ${busy ? 'request running' : 'ready for next command'}`,
						color: 'gray',
					},
				],
				bodyHeight,
			),
		[bodyHeight, busy, detailMode, focusPane, viewport.lines, viewport.offset, viewport.total, workspaceStatus, workspaceSubtitle],
	);

	return (
		<Box flexDirection="column" paddingX={1}>
			{!smokeTest && process.stdin.isTTY ? (
				<InteractiveKeyboardController
					busy={busy}
					focusPane={focusPane}
					historyLength={history.length}
					input={input}
					onRun={handleRun}
					outputViewportHeight={outputViewportHeight}
					setDetailMode={setDetailMode}
					setFocusPane={setFocusPane}
					setInput={setInput}
					setOutputScroll={setOutputScroll}
					setSelectedActionIndex={setSelectedActionIndex}
					setSelectedHistoryIndex={setSelectedHistoryIndex}
					exit={exit}
				/>
			) : null}

			<Box justifyContent="space-between" flexDirection={layoutMode === 'desktop' ? 'row' : 'column'}>
				<Box flexDirection="column" marginBottom={layoutMode === 'desktop' ? 0 : 1}>
					<Text color="cyanBright" bold>
						Ephemeral {APP_VERSION}
					</Text>
					<Text color="gray">Market intelligence, research workflows, and execution surfaces in one terminal shell.</Text>
				</Box>
				<Box flexDirection="column" alignItems={layoutMode === 'desktop' ? 'flex-end' : 'flex-start'}>
					<Text color={headerTone}>{`${animationFrames[frameIndex]} ${shellStatus}`}</Text>
					<Text color="gray">{topStatusLine}</Text>
				</Box>
			</Box>

			<Divider width={dividerWidth} />

			{layoutMode === 'desktop' ? (
				<Box height={bodyHeight}>
					<Box width={sidebarWidth} flexDirection="column">
						{sidebarRows.map((row, index) => (
							<Text key={`sidebar-${index}`} color={row.color} bold={row.bold} wrap="truncate-end">
								{row.text || ' '}
							</Text>
						))}
					</Box>
					<Box width={3} alignItems="center" flexDirection="column">
						{Array.from({length: bodyHeight}, (_, index) => (
							<Text key={`rule-${index}`} color="gray">
								│
							</Text>
						))}
					</Box>
					<Box width={mainWidth} flexDirection="column">
						{workspaceRows.map((row, index) => (
							<Box key={`workspace-${index}`} height={1}>
								{row.color || row.bold ? (
									<Text color={row.color} bold={row.bold} wrap="truncate-end">
										{row.text || ' '}
									</Text>
								) : (
									renderStyledLine(row.text, actionAccent)
								)}
							</Box>
						))}
					</Box>
				</Box>
			) : (
				<Box flexDirection="column">
					{workspaceRows.map((row, index) => (
						<Box key={`workspace-stacked-${index}`} height={1}>
							{row.color || row.bold ? (
								<Text color={row.color} bold={row.bold} wrap="truncate-end">
									{row.text || ' '}
								</Text>
							) : (
								renderStyledLine(row.text, actionAccent)
							)}
						</Box>
					))}
					<Divider width={dividerWidth} />
					{sidebarRows.slice(0, Math.min(sidebarRows.length, 16)).map((row, index) => (
						<Text key={`sidebar-stacked-${index}`} color={row.color} bold={row.bold} wrap="truncate-end">
							{row.text || ' '}
						</Text>
					))}
				</Box>
			)}

			<Divider width={dividerWidth} />

			<Box flexDirection="column">
				<Box justifyContent="space-between">
					<Text color={focusPane === 'input' ? actionAccent : 'white'} bold>
						{selectedAction.label}
					</Text>
					<Text>
						<Text color={busy ? 'yellow' : 'gray'}>{promptStatus}</Text>
						{!busy && (
							<>
								<Text color="gray"> · </Text>
								<Text color="white" bold>Enter</Text>
								<Text color="gray"> run</Text>
							</>
						)}
					</Text>
				</Box>
				<Text>
					<Text color={focusPane === 'input' ? actionAccent : 'gray'}>{'> '}</Text>
					{input ? <Text>{input}</Text> : null}
					{focusPane === 'input' ? <Text color={promptCursorColor}>{promptCursor}</Text> : null}
					{!input ? <Text color="gray">{promptHint}</Text> : null}
				</Text>
				<Text color="gray">{selectedAction.description} · {selectedAction.hint}</Text>
				<Text>
					<Text color="white" bold>Tab</Text>
					<Text color="gray"> switch pane · </Text>
					<Text color="white" bold>↑/↓</Text>
					<Text color="gray"> choose action when empty · </Text>
					<Text color="white" bold>d</Text>
					<Text color="gray"> toggles raw output</Text>
				</Text>
			</Box>
		</Box>
	);
};

render(<App />);
