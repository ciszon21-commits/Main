"use strict";
const DEFAULT_ZONE_TYPE = "";
const TOTAL_REWARD_RULE_KEYS = [
    "rule_0", "rule_1", "rule_2", "rule_3", "rule_4", "rule_5", "rule_6", "rule_7", "rule_8", "rule_9", "rule_10",
    "rule_11", "rule_12", "rule_14", "rule_15", "rule_16", "rule_17", "rule_18", "rule_19", "rule_20",
    "rule_21", "rule_22", "rule_26", "rule_27", "rule_28", "rule_29", "rule_30", "rule_32", "rule_33"
];
const DEFAULT_RULES = {
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
function createDefaultRules() {
    return { ...DEFAULT_RULES };
}
function sumRuleValues(rules, keys) {
    return keys.reduce((sum, key) => {
        var _a;
        return sum + ((_a = rules[key]) !== null && _a !== void 0 ? _a : 0);
    }, 0);
}
function formatInputValue(value) {
    return value.toFixed(2);
}
function getInitialNumericInput(value) {
    return value === 0 ? "" : formatInputValue(value);
}
function parseInputValue(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
}
function roundToTwo(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}
function getDefaults() {
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
function createVolumeCalculator() {
    const defaults = getDefaults();
    return {
        baseArea: getInitialNumericInput(defaults.baseArea),
        originalVolume: getInitialNumericInput(defaults.originalVolume),
        zoneType: defaults.zoneType,
        volumeRatioPercent: getInitialNumericInput(defaults.volumeRatio * 100),
        activeRightTab: "limits",
        rules: createDefaultRules(),
        get volumeRatio() {
            return roundToTwo(parseInputValue(this.volumeRatioPercent) / 100);
        },
        get originalVolumeValue() {
            return roundToTwo(parseInputValue(this.originalVolume));
        },
        get statutoryVolume() {
            return roundToTwo(parseInputValue(this.baseArea) * this.volumeRatio);
        },
        get capOptionOneTotal() {
            return roundToTwo(this.originalVolumeValue * 1.2);
        },
        get capOptionOneApply() {
            return roundToTwo(Math.max(0, this.capOptionOneTotal - this.originalVolumeValue));
        },
        get capOptionTwoTotal() {
            return roundToTwo(this.originalVolumeValue + this.statutoryVolume * 0.3);
        },
        get capOptionTwoApply() {
            return roundToTwo(Math.max(0, this.capOptionTwoTotal - this.statutoryVolume));
        },
        get capOptionThreeTotal() {
            return roundToTwo(this.statutoryVolume + this.statutoryVolume * 0.5);
        },
        get capOptionThreeApply() {
            return roundToTwo(Math.max(0, this.capOptionThreeTotal - this.statutoryVolume));
        },
        get maxAllowedReward() {
            return roundToTwo(Math.max(this.capOptionOneApply, this.capOptionTwoApply, this.capOptionThreeApply));
        },
        get totalRewardPercent() {
            return roundToTwo(sumRuleValues(this.rules, TOTAL_REWARD_RULE_KEYS));
        },
        get totalRewardArea() {
            return roundToTwo(this.statutoryVolume * (this.totalRewardPercent / 100));
        },
        resetForm() {
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
    constructor(payload) {
        var _a, _b;
        this.sheets = (_a = payload.sheets) !== null && _a !== void 0 ? _a : {};
        this.externalValues = (_b = payload.external_values) !== null && _b !== void 0 ? _b : {};
        this.runtimeValues = {};
        Object.keys(this.sheets).forEach((sheetKey) => {
            this.runtimeValues[sheetKey] = { ...this.sheets[sheetKey].cell_values };
        });
    }
    recalculateAll() {
        Object.keys(this.sheets).forEach((sheetKey) => this.recalculateSheet(sheetKey));
    }
    setInputValue(sheetKey, address, rawInput) {
        const isPercent = this.isPercentCell(sheetKey, address);
        const val = rawInput.trim() === "" ? 0 : Number(rawInput);
        const normalized = Number.isFinite(val) ? val : 0;
        this.runtimeValues[sheetKey][address] = isPercent ? normalized / 100 : normalized;
        this.recalculateSheet(sheetKey);
    }
    renderSheet(sheetKey) {
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
    renderAll() {
        Object.keys(this.sheets).forEach((sheetKey) => this.renderSheet(sheetKey));
    }
    recalculateSheet(sheetKey) {
        const sheet = this.sheets[sheetKey];
        if (!sheet) {
            return;
        }
        const memo = new Map();
        const stack = new Set();
        Object.keys(sheet.formulas).forEach((address) => {
            const value = this.computeCell(sheetKey, address, memo, stack);
            this.runtimeValues[sheetKey][address] = value;
        });
    }
    computeCell(sheetKey, address, memo, stack) {
        var _a, _b, _c, _d;
        const cacheKey = `${sheetKey}!${address}`;
        if (memo.has(cacheKey)) {
            return (_a = memo.get(cacheKey)) !== null && _a !== void 0 ? _a : 0;
        }
        if (stack.has(cacheKey)) {
            return (_b = this.runtimeValues[sheetKey][address]) !== null && _b !== void 0 ? _b : 0;
        }
        const formula = (_c = this.sheets[sheetKey]) === null || _c === void 0 ? void 0 : _c.formulas[address];
        if (!formula) {
            const directVal = (_d = this.runtimeValues[sheetKey][address]) !== null && _d !== void 0 ? _d : 0;
            memo.set(cacheKey, directVal);
            return directVal;
        }
        stack.add(cacheKey);
        const value = this.evaluateFormula(sheetKey, formula, memo, stack);
        stack.delete(cacheKey);
        memo.set(cacheKey, value);
        return value;
    }
    evaluateFormula(currentSheetKey, formula, memo, stack) {
        var _a;
        let expr = formula.slice(1);
        expr = expr.replace(/\$/g, "");
        // Handle sheet-qualified refs first.
        expr = expr.replace(/'([^']+)'!([A-Z]{1,3}\d+)/g, (_m, sheetName, addr) => {
            return `REF(${JSON.stringify(sheetName)}, ${JSON.stringify(addr)})`;
        });
        expr = expr.replace(/\[[^\]]+\]([^!]+)!([A-Z]{1,3}\d+)/g, (_m, sheetName, addr) => {
            return `REF(${JSON.stringify(sheetName)}, ${JSON.stringify(addr)})`;
        });
        expr = expr.replace(/([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)/g, (_m, start, end) => {
            return `RANGE(${JSON.stringify(currentSheetKey)}, ${JSON.stringify(start)}, ${JSON.stringify(end)})`;
        });
        expr = expr.replace(/\b([A-Z]{1,3}\d+)\b/g, (_m, addr) => {
            return `REF(${JSON.stringify(currentSheetKey)}, ${JSON.stringify(addr)})`;
        });
        expr = expr.replace(/<>/g, "!=");
        expr = expr.replace(/(?<![<>=])=(?![<>=])/g, "==");
        expr = expr.replace(/&/g, "+");
        const REF = (sheetName, addr) => {
            const mappedSheetKey = this.getSheetKeyByName(sheetName);
            if (!mappedSheetKey) {
                const ext = this.externalValues[`${sheetName}!${addr}`];
                return ext !== null && ext !== void 0 ? ext : 0;
            }
            return this.computeCell(mappedSheetKey, addr, memo, stack);
        };
        const RANGE = (sheetName, start, end) => {
            const mappedSheetKey = this.getSheetKeyByName(sheetName);
            if (!mappedSheetKey) {
                return [];
            }
            return this.expandRange(start, end).map((addr) => this.computeCell(mappedSheetKey, addr, memo, stack));
        };
        const flatten = (items) => {
            const out = [];
            items.forEach((item) => {
                if (Array.isArray(item)) {
                    out.push(...flatten(item));
                }
                else {
                    out.push(item);
                }
            });
            return out;
        };
        const toNumber = (value) => {
            if (value === null || value === undefined || value === "") {
                return 0;
            }
            if (typeof value === "number") {
                return Number.isFinite(value) ? value : 0;
            }
            const parsed = Number(value);
            return Number.isFinite(parsed) ? parsed : 0;
        };
        const SUM = (...args) => flatten(args).reduce((sum, x) => sum + toNumber(x), 0);
        const COUNTA = (...args) => flatten(args).filter((x) => x !== null && x !== undefined && x !== "").length;
        const IF = (cond, whenTrue, whenFalse) => (cond ? whenTrue : whenFalse);
        const ROUND = (num, digits = 0) => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            return Math.round(n * factor) / factor;
        };
        const ROUNDUP = (num, digits = 0) => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            if (n >= 0) {
                return Math.ceil(n * factor) / factor;
            }
            return Math.floor(n * factor) / factor;
        };
        const ROUNDDOWN = (num, digits = 0) => {
            const n = toNumber(num);
            const d = toNumber(digits);
            const factor = 10 ** d;
            if (n >= 0) {
                return Math.floor(n * factor) / factor;
            }
            return Math.ceil(n * factor) / factor;
        };
        const MIN = (...args) => {
            const vals = flatten(args).map((x) => toNumber(x));
            return vals.length ? Math.min(...vals) : 0;
        };
        try {
            const fn = new Function("REF", "RANGE", "SUM", "COUNTA", "IF", "ROUND", "ROUNDUP", "ROUNDDOWN", "MIN", `return (${expr});`);
            const result = fn(REF, RANGE, SUM, COUNTA, IF, ROUND, ROUNDUP, ROUNDDOWN, MIN);
            return result;
        }
        catch (_b) {
            return (_a = this.runtimeValues[currentSheetKey][this.findFormulaAddress(currentSheetKey, formula)]) !== null && _a !== void 0 ? _a : 0;
        }
    }
    findFormulaAddress(sheetKey, formula) {
        var _a, _b;
        const formulas = (_b = (_a = this.sheets[sheetKey]) === null || _a === void 0 ? void 0 : _a.formulas) !== null && _b !== void 0 ? _b : {};
        const pair = Object.entries(formulas).find(([, f]) => f === formula);
        return pair ? pair[0] : "";
    }
    getSheetKeyByName(sheetName) {
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
    expandRange(start, end) {
        const [c1, r1] = this.splitAddress(start);
        const [c2, r2] = this.splitAddress(end);
        const colStart = Math.min(this.colToNumber(c1), this.colToNumber(c2));
        const colEnd = Math.max(this.colToNumber(c1), this.colToNumber(c2));
        const rowStart = Math.min(r1, r2);
        const rowEnd = Math.max(r1, r2);
        const result = [];
        for (let row = rowStart; row <= rowEnd; row += 1) {
            for (let col = colStart; col <= colEnd; col += 1) {
                result.push(`${this.numberToCol(col)}${row}`);
            }
        }
        return result;
    }
    splitAddress(addr) {
        const match = addr.match(/^([A-Z]{1,3})(\d+)$/);
        if (!match) {
            return ["A", 1];
        }
        return [match[1], Number(match[2])];
    }
    colToNumber(col) {
        return col.split("").reduce((n, ch) => n * 26 + (ch.charCodeAt(0) - 64), 0);
    }
    numberToCol(num) {
        let n = num;
        let out = "";
        while (n > 0) {
            const rem = (n - 1) % 26;
            out = String.fromCharCode(65 + rem) + out;
            n = Math.floor((n - 1) / 26);
        }
        return out || "A";
    }
    isPercentCell(sheetKey, address) {
        var _a, _b;
        const cells = (_b = (_a = this.sheets[sheetKey]) === null || _a === void 0 ? void 0 : _a.percent_cells) !== null && _b !== void 0 ? _b : [];
        return cells.includes(address);
    }
    formatDisplay(value, isPercent = false) {
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
function initBuildingMassEngine() {
    const node = document.getElementById("building-mass-engine-data");
    if (!(node === null || node === void 0 ? void 0 : node.textContent)) {
        return;
    }
    const payload = JSON.parse(node.textContent);
    const engine = new BuildingMassFormulaEngine(payload);
    engine.recalculateAll();
    engine.renderAll();
    const inputs = document.querySelectorAll("input[data-sheet-key][data-cell-address]");
    inputs.forEach((input) => {
        input.addEventListener("input", () => {
            var _a, _b;
            const sheetKey = (_a = input.dataset.sheetKey) !== null && _a !== void 0 ? _a : "";
            const cellAddress = (_b = input.dataset.cellAddress) !== null && _b !== void 0 ? _b : "";
            if (!sheetKey || !cellAddress) {
                return;
            }
            engine.setInputValue(sheetKey, cellAddress, input.value);
            engine.renderSheet(sheetKey);
        });
    });
}
window.volumeCalculator = createVolumeCalculator;
document.addEventListener("alpine:init", () => {
    if (typeof Alpine !== "undefined") {
        Alpine.data("volumeCalculator", createVolumeCalculator);
    }
});
document.addEventListener("DOMContentLoaded", () => {
    var _a;
    (_a = window.lucide) === null || _a === void 0 ? void 0 : _a.createIcons();
    initBuildingMassEngine();
});
