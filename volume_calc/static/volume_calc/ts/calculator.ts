interface VolumeCalcDefaults {
    baseArea: number;
    originalVolume: number;
    zoneType: string;
    volumeRatio: number;
}

interface Rules {
    [key: string]: number;
}

interface LucideApi {
    createIcons: () => void;
}

interface VolumeCalculatorState {
    baseArea: string;
    originalVolume: string;
    zoneType: string;
    volumeRatioPercent: string;
    activeRightTab: string;
    readonly originalVolumeValue: number;
    readonly volumeRatio: number;
    rules: Rules;
    readonly statutoryVolume: number;
    readonly capOptionOneTotal: number;
    readonly capOptionOneApply: number;
    readonly capOptionTwoTotal: number;
    readonly capOptionTwoApply: number;
    readonly capOptionThreeTotal: number;
    readonly capOptionThreeApply: number;
    readonly maxAllowedReward: number;
    readonly totalRewardPercent: number;
    readonly totalRewardArea: number;
    resetForm: () => void;
}

type CellValue = number | string | null;

interface BuildingMassSheetEngine {
    key: string;
    title: string;
    row_count: number;
    col_count: number;
    formulas: Record<string, string>;
    cell_values: Record<string, CellValue>;
    input_cells: string[];
    percent_cells: string[];
}

interface BuildingMassEnginePayload {
    sheets: Record<string, BuildingMassSheetEngine>;
    external_values: Record<string, CellValue>;
}

interface Window {
    __volumeCalcDefaults?: VolumeCalcDefaults;
    volumeCalculator: () => VolumeCalculatorState;
    lucide?: LucideApi;
}

const DEFAULT_ZONE_TYPE = "";
const TOTAL_REWARD_RULE_KEYS = [
    "rule_0", "rule_1", "rule_2", "rule_3", "rule_4", "rule_5", "rule_6", "rule_7", "rule_8", "rule_9", "rule_10",
    "rule_11", "rule_12", "rule_14", "rule_15", "rule_16", "rule_17", "rule_18", "rule_19", "rule_20",
    "rule_21", "rule_22", "rule_26", "rule_27", "rule_28", "rule_29", "rule_30", "rule_32", "rule_33"
] as const;

const DEFAULT_RULES: Readonly<Rules> = {
    rule_0: 0,
    rule_1: 8.0,
    rule_2: 0,
    rule_3: 0,
    rule_4: 0,
    rule_5: 6.0,
    rule_6: 6.0,
    rule_7: 3.0,
    rule_8: 2.0,
    rule_9: 5.0,
    rule_10: 0,
    rule_11: 0,
    rule_12: 0,
    rule_14: 0,
    rule_15: 1.0,
    rule_16: 0,
    rule_17: 3.0,
    rule_18: 0,
    rule_19: 0,
    rule_20: 1.0,
    rule_21: 0,
    rule_22: 2.0,
    rule_25: 30.0,
    rule_26: 0,
    rule_27: 0,
    rule_28: 0,
    rule_29: 0,
    rule_30: 0,
    rule_32: 0,
    rule_33: 0
};

function createDefaultRules(): Rules {
    return { ...DEFAULT_RULES };
}

function sumRuleValues(rules: Rules, keys: readonly string[]): number {
    return keys.reduce((sum, key) => sum + (rules[key] ?? 0), 0);
}

function formatInputValue(value: number): string {
    return value.toFixed(2);
}

function getInitialNumericInput(value: number): string {
    return value === 0 ? "" : formatInputValue(value);
}

function parseInputValue(value: string): number {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}

function roundToTwo(value: number): number {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}

function getDefaults(): VolumeCalcDefaults {
    const defaults = window.__volumeCalcDefaults;

    if (!defaults) {
        return {
            baseArea: 0,
            originalVolume: 0,
            zoneType: DEFAULT_ZONE_TYPE,
            volumeRatio: 0
        };
    }

    return {
        baseArea: defaults.baseArea,
        originalVolume: defaults.originalVolume,
        zoneType: defaults.zoneType,
        volumeRatio: defaults.volumeRatio
    };
}

function createVolumeCalculator(): VolumeCalculatorState {
    const defaults = getDefaults();

    return {
        baseArea: getInitialNumericInput(defaults.baseArea),
        originalVolume: getInitialNumericInput(defaults.originalVolume),
        zoneType: defaults.zoneType,
        volumeRatioPercent: getInitialNumericInput(defaults.volumeRatio * 100),
        activeRightTab: "limits",
        rules: createDefaultRules(),

        get volumeRatio(): number {
            return roundToTwo(parseInputValue(this.volumeRatioPercent) / 100);
        },

        get originalVolumeValue(): number {
            return roundToTwo(parseInputValue(this.originalVolume));
        },

        get statutoryVolume(): number {
            return roundToTwo(parseInputValue(this.baseArea) * this.volumeRatio);
        },

        get capOptionOneTotal(): number {
            return roundToTwo(this.originalVolumeValue * 1.2);
        },

        get capOptionOneApply(): number {
            return roundToTwo(Math.max(0, this.capOptionOneTotal - this.originalVolumeValue));
        },

        get capOptionTwoTotal(): number {
            return roundToTwo(this.originalVolumeValue + this.statutoryVolume * 0.3);
        },

        get capOptionTwoApply(): number {
            return roundToTwo(Math.max(0, this.capOptionTwoTotal - this.statutoryVolume));
        },

        get capOptionThreeTotal(): number {
            return roundToTwo(this.statutoryVolume + this.statutoryVolume * 0.5);
        },

        get capOptionThreeApply(): number {
            return roundToTwo(Math.max(0, this.capOptionThreeTotal - this.statutoryVolume));
        },

        get maxAllowedReward(): number {
            return roundToTwo(Math.max(this.capOptionOneApply, this.capOptionTwoApply, this.capOptionThreeApply));
        },

        get totalRewardPercent(): number {
            return roundToTwo(sumRuleValues(this.rules, TOTAL_REWARD_RULE_KEYS));
        },

        get totalRewardArea(): number {
            return roundToTwo(this.statutoryVolume * (this.totalRewardPercent / 100));
        },

        resetForm(): void {
            this.baseArea = getInitialNumericInput(defaults.baseArea);
            this.originalVolume = getInitialNumericInput(defaults.originalVolume);
            this.zoneType = defaults.zoneType;
            this.volumeRatioPercent = getInitialNumericInput(defaults.volumeRatio * 100);
            this.activeRightTab = "limits";
            this.rules = createDefaultRules();
        }
    };
}

class BuildingMassFormulaEngine {
    private readonly sheets: Record<string, BuildingMassSheetEngine>;
    private readonly externalValues: Record<string, CellValue>;
    private runtimeValues: Record<string, Record<string, CellValue>>;

    constructor(payload: BuildingMassEnginePayload) {
        this.sheets = payload.sheets ?? {};
        this.externalValues = payload.external_values ?? {};
        this.runtimeValues = {};

        Object.keys(this.sheets).forEach((sheetKey) => {
            this.runtimeValues[sheetKey] = { ...this.sheets[sheetKey].cell_values };
        });
    }

    public recalculateAll(): void {
        Object.keys(this.sheets).forEach((sheetKey) => this.recalculateSheet(sheetKey));
    }

    public setInputValue(sheetKey: string, address: string, rawInput: string): void {
        const isPercent = this.isPercentCell(sheetKey, address);
        const val = rawInput.trim() === "" ? 0 : Number(rawInput);
        const normalized = Number.isFinite(val) ? val : 0;
        this.runtimeValues[sheetKey][address] = isPercent ? normalized / 100 : normalized;
        this.recalculateSheet(sheetKey);
    }

    public renderSheet(sheetKey: string): void {
        const sheet = this.sheets[sheetKey];
        if (!sheet) {
            return;
        }

        Object.keys(this.runtimeValues[sheetKey]).forEach((address) => {
            const value = this.runtimeValues[sheetKey][address];
            const text = this.formatDisplay(value, this.isPercentCell(sheetKey, address));
            const selector = `span[data-sheet-key="${sheetKey}"][data-cell-address="${address}"]`;
            const node = document.querySelector(selector);
            if (node) {
                node.textContent = text;
            }
        });
    }

    public renderAll(): void {
        Object.keys(this.sheets).forEach((sheetKey) => this.renderSheet(sheetKey));
    }

    private recalculateSheet(sheetKey: string): void {
        const sheet = this.sheets[sheetKey];
        if (!sheet) {
            return;
        }

        const memo = new Map<string, CellValue>();
        const stack = new Set<string>();

        Object.keys(sheet.formulas).forEach((address) => {
            const value = this.computeCell(sheetKey, address, memo, stack);
            this.runtimeValues[sheetKey][address] = value;
        });
    }

    private computeCell(
        sheetKey: string,
        address: string,
        memo: Map<string, CellValue>,
        stack: Set<string>
    ): CellValue {
        const cacheKey = `${sheetKey}!${address}`;
        if (memo.has(cacheKey)) {
            return memo.get(cacheKey) ?? 0;
        }

        if (stack.has(cacheKey)) {
            return this.runtimeValues[sheetKey][address] ?? 0;
        }

        const formula = this.sheets[sheetKey]?.formulas[address];
        if (!formula) {
            const directVal = this.runtimeValues[sheetKey][address] ?? 0;
            memo.set(cacheKey, directVal);
            return directVal;
        }

        stack.add(cacheKey);
        const value = this.evaluateFormula(sheetKey, formula, memo, stack);
        stack.delete(cacheKey);

        memo.set(cacheKey, value);
        return value;
    }

    private evaluateFormula(
        currentSheetKey: string,
        formula: string,
        memo: Map<string, CellValue>,
        stack: Set<string>
    ): CellValue {
        let expr = formula.slice(1);
        expr = expr.replace(/\$/g, "");

        // Handle sheet-qualified refs first.
        expr = expr.replace(/'([^']+)'!([A-Z]{1,3}\d+)/g, (_m, sheetName: string, addr: string) => {
            return `REF(${JSON.stringify(sheetName)}, ${JSON.stringify(addr)})`;
        });
        expr = expr.replace(/\[[^\]]+\]([^!]+)!([A-Z]{1,3}\d+)/g, (_m, sheetName: string, addr: string) => {
            return `REF(${JSON.stringify(sheetName)}, ${JSON.stringify(addr)})`;
        });

        expr = expr.replace(/([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)/g, (_m, start: string, end: string) => {
            return `RANGE(${JSON.stringify(currentSheetKey)}, ${JSON.stringify(start)}, ${JSON.stringify(end)})`;
        });

        expr = expr.replace(/\b([A-Z]{1,3}\d+)\b/g, (_m, addr: string) => {
            return `REF(${JSON.stringify(currentSheetKey)}, ${JSON.stringify(addr)})`;
        });

        expr = expr.replace(/<>/g, "!=");
        expr = expr.replace(/(?<![<>=])=(?![<>=])/g, "==");
        expr = expr.replace(/&/g, "+");

        const REF = (sheetName: string, addr: string): CellValue => {
            const mappedSheetKey = this.getSheetKeyByName(sheetName);
            if (!mappedSheetKey) {
                const ext = this.externalValues[`${sheetName}!${addr}`];
                return ext ?? 0;
            }
            return this.computeCell(mappedSheetKey, addr, memo, stack);
        };

        const RANGE = (sheetName: string, start: string, end: string): CellValue[] => {
            const mappedSheetKey = this.getSheetKeyByName(sheetName);
            if (!mappedSheetKey) {
                return [];
            }
            return this.expandRange(start, end).map((addr) => this.computeCell(mappedSheetKey, addr, memo, stack));
        };

        const flatten = (items: unknown[]): unknown[] => {
            const out: unknown[] = [];
            items.forEach((item) => {
                if (Array.isArray(item)) {
                    out.push(...flatten(item));
                } else {
                    out.push(item);
                }
            });
            return out;
        };

        const toNumber = (value: unknown): number => {
            if (value === null || value === undefined || value === "") {
                return 0;
            }
            if (typeof value === "number") {
                return Number.isFinite(value) ? value : 0;
            }
            const parsed = Number(value);
            return Number.isFinite(parsed) ? parsed : 0;
        };

        const SUM = (...args: unknown[]): number =>
            flatten(args).reduce<number>((sum, x) => sum + toNumber(x), 0);
        const COUNTA = (...args: unknown[]): number => flatten(args).filter((x) => x !== null && x !== undefined && x !== "").length;
        const IF = (cond: unknown, whenTrue: unknown, whenFalse: unknown): unknown => (cond ? whenTrue : whenFalse);
        const ROUND = (num: unknown, digits: unknown = 0): number => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            return Math.round(n * factor) / factor;
        };
        const ROUNDUP = (num: unknown, digits: unknown = 0): number => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            if (n >= 0) {
                return Math.ceil(n * factor) / factor;
            }
            return Math.floor(n * factor) / factor;
        };
        const ROUNDDOWN = (num: unknown, digits: unknown = 0): number => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            if (n >= 0) {
                return Math.floor(n * factor) / factor;
            }
            return Math.ceil(n * factor) / factor;
        };
        const MIN = (...args: unknown[]): number => {
            const vals = flatten(args).map((x) => toNumber(x));
            return vals.length ? Math.min(...vals) : 0;
        };

        try {
            const fn = new Function(
                "REF",
                "RANGE",
                "SUM",
                "COUNTA",
                "IF",
                "ROUND",
                "ROUNDUP",
                "ROUNDDOWN",
                "MIN",
                `return (${expr});`
            ) as (
                refFn: typeof REF,
                rangeFn: typeof RANGE,
                sumFn: typeof SUM,
                countaFn: typeof COUNTA,
                ifFn: typeof IF,
                roundFn: typeof ROUND,
                roundupFn: typeof ROUNDUP,
                rounddownFn: typeof ROUNDDOWN,
                minFn: typeof MIN
            ) => unknown;

            const result = fn(REF, RANGE, SUM, COUNTA, IF, ROUND, ROUNDUP, ROUNDDOWN, MIN);
            return result as CellValue;
        } catch {
            return this.runtimeValues[currentSheetKey][this.findFormulaAddress(currentSheetKey, formula)] ?? 0;
        }
    }

    private findFormulaAddress(sheetKey: string, formula: string): string {
        const formulas = this.sheets[sheetKey]?.formulas ?? {};
        const pair = Object.entries(formulas).find(([, f]) => f === formula);
        return pair ? pair[0] : "";
    }

    private getSheetKeyByName(sheetName: string): string | null {
        const entries = Object.values(this.sheets);
        const exact = entries.find((s) => s.title === sheetName || s.key === sheetName);
        if (exact) {
            return exact.key;
        }

        // Map common workbook names to our keys.
        if (sheetName.includes("北市建築量體")) {
            return "taipei";
        }
        if (sheetName.includes("新北建築量體")) {
            return "new_taipei";
        }

        return null;
    }

    private expandRange(start: string, end: string): string[] {
        const [c1, r1] = this.splitAddress(start);
        const [c2, r2] = this.splitAddress(end);

        const colStart = Math.min(this.colToNumber(c1), this.colToNumber(c2));
        const colEnd = Math.max(this.colToNumber(c1), this.colToNumber(c2));
        const rowStart = Math.min(r1, r2);
        const rowEnd = Math.max(r1, r2);

        const result: string[] = [];
        for (let row = rowStart; row <= rowEnd; row += 1) {
            for (let col = colStart; col <= colEnd; col += 1) {
                result.push(`${this.numberToCol(col)}${row}`);
            }
        }
        return result;
    }

    private splitAddress(addr: string): [string, number] {
        const match = addr.match(/^([A-Z]{1,3})(\d+)$/);
        if (!match) {
            return ["A", 1];
        }
        return [match[1], Number(match[2])];
    }

    private colToNumber(col: string): number {
        return col.split("").reduce((n, ch) => n * 26 + (ch.charCodeAt(0) - 64), 0);
    }

    private numberToCol(num: number): string {
        let n = num;
        let out = "";
        while (n > 0) {
            const rem = (n - 1) % 26;
            out = String.fromCharCode(65 + rem) + out;
            n = Math.floor((n - 1) / 26);
        }
        return out || "A";
    }

    private isPercentCell(sheetKey: string, address: string): boolean {
        const cells = this.sheets[sheetKey]?.percent_cells ?? [];
        return cells.includes(address);
    }

    private formatDisplay(value: CellValue, isPercent = false): string {
        if (value === null || value === undefined || value === "") {
            return "";
        }
        if (typeof value === "number") {
            if (isPercent) {
                return `${(value * 100).toFixed(2)}%`;
            }
            if (Number.isInteger(value)) {
                return `${value}`;
            }
            return value.toFixed(2);
        }
        const parsed = Number(value);
        if (!Number.isNaN(parsed) && `${value}`.trim() !== "") {
            if (isPercent) {
                return `${(parsed * 100).toFixed(2)}%`;
            }
            if (Number.isInteger(parsed)) {
                return `${parsed}`;
            }
            return parsed.toFixed(2);
        }
        return `${value}`;
    }
}

function initBuildingMassEngine(): void {
    const node = document.getElementById("building-mass-engine-data");
    if (!node?.textContent) {
        return;
    }

    const payload = JSON.parse(node.textContent) as BuildingMassEnginePayload;
    const engine = new BuildingMassFormulaEngine(payload);

    engine.recalculateAll();
    engine.renderAll();

    const inputs = document.querySelectorAll<HTMLInputElement>(
        "input[data-sheet-key][data-cell-address]"
    );

    inputs.forEach((input) => {
        input.addEventListener("input", () => {
            const sheetKey = input.dataset.sheetKey ?? "";
            const cellAddress = input.dataset.cellAddress ?? "";
            if (!sheetKey || !cellAddress) {
                return;
            }
            engine.setInputValue(sheetKey, cellAddress, input.value);
            engine.renderSheet(sheetKey);
        });
    });
}

window.volumeCalculator = createVolumeCalculator;

document.addEventListener("DOMContentLoaded", () => {
    window.lucide?.createIcons();
    initBuildingMassEngine();
});
