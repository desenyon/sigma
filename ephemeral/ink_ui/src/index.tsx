import React, {useEffect, useMemo, useState} from 'react';
import {Box, Newline, render, Text, useApp, useInput, useStdin, useStdout} from 'ink';
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

const actionRowsForGroup = (group: ActionDefinition['group'], selectedIndex: number) =>
	actions
		.filter(action => action.group === group)
		.map(action => {
			const index = actions.findIndex(candidate => candidate.id === action.id);
			return {
				id: action.id,
				label: `${index === selectedIndex ? '▸' : ' '} ${action.label}`,
				selected: index === selectedIndex,
			};
		});

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

const invokeBridge = async (request: BridgeRequest): Promise<BridgeEnvelope> =>
	new Promise((resolve, reject) => {
		const child = spawn(pythonExecutable, ['-m', 'ephemeral.ink_bridge'], {
			cwd: projectRoot,
			env: process.env,
			stdio: ['pipe', 'pipe', 'pipe'],
		});

		let stdout = '';
		let stderr = '';

		child.stdout.on('data', chunk => {
			stdout += String(chunk);
		});

		child.stderr.on('data', chunk => {
			stderr += String(chunk);
		});

		child.on('error', reject);
		child.on('close', code => {
			if (!stdout.trim()) {
				reject(new Error(stderr.trim() || `Bridge exited with code ${code ?? 'unknown'}`));
				return;
			}

			try {
				const parsed = JSON.parse(stdout) as BridgeEnvelope;
				if (code && !parsed.ok) {
					reject(new Error(parsed.error ?? (stderr.trim() || `Bridge exited with code ${code}`)));
					return;
				}

				resolve(parsed);
			} catch {
				reject(new Error(`Invalid bridge response: ${stdout}\n${stderr}`));
			}
		});

		child.stdin.write(JSON.stringify(request));
		child.stdin.end();
	});

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

type CardProps = {
	title: string;
	accent?: string;
	subtitle?: string;
	focused?: boolean;
	children: React.ReactNode;
};

const Card = ({title, accent = 'cyan', subtitle, focused = false, children}: CardProps) => (
	<Box borderStyle="round" borderColor={focused ? accent : 'gray'} paddingX={1} flexDirection="column">
		<Text color={focused ? accent : 'gray'}>{title}</Text>
		{subtitle ? <Text color="gray" wrap="truncate-end">{subtitle}</Text> : null}
		{children}
	</Box>
);

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

	const layoutMode: LayoutMode = terminalWidth >= 136 && terminalHeight >= 28 ? 'desktop' : 'stacked';
	const sidebarWidth = layoutMode === 'desktop' ? clamp(Math.floor(terminalWidth * 0.27), 30, 38) : terminalWidth - 2;
	const mainWidth = layoutMode === 'desktop' ? Math.max(74, terminalWidth - sidebarWidth - 5) : terminalWidth - 2;
	const desktopOutputHeight = clamp(terminalHeight - 11, 16, 34);
	const stackedOutputHeight = clamp(Math.floor((terminalHeight - 15) * 0.48), 10, 16);
	const outputViewportHeight = (layoutMode === 'desktop' ? desktopOutputHeight : stackedOutputHeight) - 4;
	const outputViewportWidth = Math.max(32, (layoutMode === 'desktop' ? mainWidth : terminalWidth - 2) - 4);
	const activityVisible = layoutMode === 'desktop' ? 6 : 4;

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

	const groupRows = useMemo(() => actionRowsForGroup(selectedAction.group, selectedActionIndex), [selectedAction.group, selectedActionIndex]);

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
					'Ephemeral 3.8 follows a Claude-Code-style command workflow.',
					'Use the navigator for workflows, keep one active result in the canvas, and treat the composer as the place to type.',
					'',
					'Controls',
					'- Enter runs the current action.',
					'- Up and down switch actions when the composer is empty.',
					'- Tab changes pane and slash commands bypass the selected action.',
					'',
					'Try',
					'- Why is NVDA moving and what changes the thesis?',
					'- Compare META GOOGL AMZN or run /status',
				].join('\n');
	const viewport = viewportLines(selectedBody, outputViewportWidth, outputViewportHeight, outputScroll);

	const workspaceStatus = selectedEntry ? selectedEntry.label : pendingLabel ?? 'Workspace';
	const workspaceSubtitle = selectedEntry?.input
		? `input · ${truncate(selectedEntry.input, Math.max(28, outputViewportWidth - 10))}`
		: detailMode === 'raw'
			? 'raw payload'
			: selectedAction.hint;

	const promptCursor = focusPane === 'input' ? '▏' : '';
	const promptCursorColor = frameIndex % 2 === 0 ? 'cyanBright' : 'blue';
	const promptStatus = busy ? 'running' : 'ready';
	const promptHint = input.trim()
		? selectedAction.hint
		: selectedAction.promptPlaceholder ?? 'Use natural language or slash commands like /quote AAPL';
	const shellStatus = busy ? `running ${pendingLabel ?? 'request'}` : statusLoading ? 'syncing state' : `${metrics.provider} · ${metrics.model}`;
	const sidebarFocused = focusPane === 'actions' || focusPane === 'history';

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

			<Box justifyContent="space-between" flexDirection={layoutMode === 'desktop' ? 'row' : 'column'} marginBottom={1}>
				<Box flexDirection="column" marginBottom={layoutMode === 'desktop' ? 0 : 1}>
					<Text color="cyanBright">Ephemeral {APP_VERSION}</Text>
					<Text color="gray">Research shell for market analysis, execution workflows, and local-or-cloud model routing.</Text>
				</Box>
				<Box flexDirection="column" alignItems={layoutMode === 'desktop' ? 'flex-end' : 'flex-start'}>
					<Text color={busy ? 'yellow' : statusLoading ? 'blue' : 'green'}>{`${animationFrames[frameIndex]} ${shellStatus}`}</Text>
					<Text color="gray">Enter run · Tab panes · arrows choose · [ ] scroll · d raw</Text>
				</Box>
			</Box>

			{layoutMode === 'desktop' ? (
				<Box marginBottom={1}>
					<Box width={sidebarWidth} marginRight={1}>
						<Card title="Navigator" subtitle={`${metrics.provider} · ${truncate(String(metrics.model), 20)}`} focused={sidebarFocused} accent="cyan">
							<Text color="gray">Session</Text>
							<Text color="gray">State   {metrics.state}</Text>
							<Text color="gray">Local   {metrics.installedModels.length ? `${metrics.installedModels.length} models ready` : 'not ready'}</Text>
							{metrics.host !== 'n/a' ? <Text color="gray">Host    {truncate(String(metrics.host), 20)}</Text> : null}
							<Box>
								<Text color={selectedAction.group === 'Research' ? 'cyanBright' : 'gray'}>Research</Text>
								<Text color="gray"> · </Text>
								<Text color={selectedAction.group === 'Build' ? 'yellow' : 'gray'}>Build</Text>
								<Text color="gray"> · </Text>
								<Text color={selectedAction.group === 'Ops' ? 'green' : 'gray'}>Ops</Text>
							</Box>
							<Text color="gray">Actions</Text>
							{groupRows.map(row => (
								<Text key={row.id} color={row.selected ? 'cyanBright' : 'white'} bold={row.selected} wrap="truncate-end">
									{row.label}
								</Text>
							))}
							<Text color="gray">Recent Runs</Text>
							{activityRows.length ? (
								activityRows.map(row => (
									<Text key={row.id} color={row.selected ? 'cyanBright' : row.error ? 'red' : 'gray'} bold={row.selected} wrap="truncate-end">
										{`${row.selected ? '▸' : ' '} ${truncate(row.label, 16)} · ${row.timestamp}`}
									</Text>
								))
							) : (
								<Text color="gray">No runs yet</Text>
							)}
							<Text color="gray">Focus   {focusPane}</Text>
							<Text color="gray">Inspect {selectedEntry ? detailMode : 'workspace'}</Text>
						</Card>
					</Box>

					<Box width={mainWidth}>
						<Card title={workspaceStatus} subtitle={workspaceSubtitle} focused={focusPane === 'output'} accent="cyan">
							{viewport.lines.map((line, index) => (
								<Text key={`${workspaceStatus}-${index}`}>{line || ' '}</Text>
							))}
							<Newline />
							<Text color="gray">
								{viewport.total > viewport.lines.length
									? `scroll ${viewport.offset + 1}-${Math.min(viewport.offset + viewport.lines.length, viewport.total)} of ${viewport.total}`
									: `detail ${detailMode} · rendered for human scanning`}
							</Text>
						</Card>
					</Box>
				</Box>
			) : (
				<Box flexDirection="column" marginBottom={1}>
					<Box marginBottom={1}>
						<Card title={workspaceStatus} subtitle={workspaceSubtitle} focused={focusPane === 'output'} accent="cyan">
							{viewport.lines.map((line, index) => (
								<Text key={`${workspaceStatus}-${index}`}>{line || ' '}</Text>
							))}
							<Newline />
							<Text color="gray">
								{viewport.total > viewport.lines.length
									? `scroll ${viewport.offset + 1}-${Math.min(viewport.offset + viewport.lines.length, viewport.total)} of ${viewport.total}`
									: `detail ${detailMode} · rendered for human scanning`}
							</Text>
						</Card>
					</Box>

					<Card title="Navigator" subtitle={`${metrics.provider} · ${truncate(String(metrics.model), 24)}`} focused={sidebarFocused} accent="cyan">
						<Text color="gray">Session</Text>
						<Text color="gray">State   {metrics.state}</Text>
						<Text color="gray">Local   {metrics.installedModels.length ? `${metrics.installedModels.length} models ready` : 'not ready'}</Text>
						{metrics.host !== 'n/a' ? <Text color="gray">Host    {truncate(String(metrics.host), 36)}</Text> : null}
						<Box>
							<Text color={selectedAction.group === 'Research' ? 'cyanBright' : 'gray'}>Research</Text>
							<Text color="gray"> · </Text>
							<Text color={selectedAction.group === 'Build' ? 'yellow' : 'gray'}>Build</Text>
							<Text color="gray"> · </Text>
							<Text color={selectedAction.group === 'Ops' ? 'green' : 'gray'}>Ops</Text>
						</Box>
						<Text color="gray">Actions</Text>
						{groupRows.map(row => (
							<Text key={row.id} color={row.selected ? 'cyanBright' : 'white'} bold={row.selected} wrap="truncate-end">
								{row.label}
							</Text>
						))}
						<Text color="gray">Recent Runs</Text>
						{activityRows.length ? (
							activityRows.map(row => (
								<Text key={row.id} color={row.selected ? 'cyanBright' : row.error ? 'red' : 'gray'} bold={row.selected} wrap="truncate-end">
									{`${row.selected ? '▸' : ' '} ${truncate(row.label, 40)} · ${row.timestamp}`}
								</Text>
							))
						) : (
							<Text color="gray">No runs yet</Text>
						)}
						<Text color="gray">Focus   {focusPane}</Text>
						<Text color="gray">Inspect {selectedEntry ? detailMode : 'workspace'}</Text>
					</Card>
				</Box>
			)}

			<Card title={`Composer · ${selectedAction.label}`} subtitle={selectedAction.hint} focused={focusPane === 'input'} accent="cyan">
				<Text>
					<Text color={busy ? 'yellow' : 'green'}>{promptStatus.padEnd(7)}</Text>
					<Text color={focusPane === 'input' ? 'cyanBright' : 'gray'}> ▸ </Text>
					<Text>{input}</Text>
					{focusPane === 'input' ? <Text color={promptCursorColor}>{promptCursor}</Text> : null}
				</Text>
				<Text color="gray" wrap="truncate-end">{promptHint}</Text>
				<Text color="gray">Enter run · Up/Down choose action when empty · Tab switch pane · /status for routing info</Text>
			</Card>
		</Box>
	);
};

render(<App />);
