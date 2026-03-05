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
    baseArea: number;
    originalVolume: number;
    zoneType: string;
    volumeRatio: number;
    rules: Rules;
    readonly statutoryVolume: number;
    readonly maxAllowedReward: number;
    readonly totalRewardArea: number;
    resetForm: () => void;
}

interface Window {
    __volumeCalcDefaults?: VolumeCalcDefaults;
    volumeCalculator: () => VolumeCalculatorState;
    lucide?: LucideApi;
}

const DEFAULT_ZONE_TYPE = "ç¬¬ä?ç¨®ä?å®…å?";
const REWARD_RULE_KEYS = [
    "rule_0", "rule_1", "rule_2", "rule_3", "rule_4", "rule_5", "rule_6", "rule_7", "rule_8", "rule_9",
    "rule_10", "rule_11", "rule_12", "rule_14", "rule_15", "rule_16", "rule_17", "rule_18", "rule_19", "rule_20",
    "rule_21", "rule_22", "rule_25", "rule_26", "rule_27", "rule_28", "rule_29", "rule_30", "rule_32", "rule_33"
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

function getDefaults(): VolumeCalcDefaults {
    const defaults = window.__volumeCalcDefaults;

    if (!defaults) {
        return {
            baseArea: 1029,
            originalVolume: 2000,
            zoneType: DEFAULT_ZONE_TYPE,
            volumeRatio: 2.25
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
        baseArea: defaults.baseArea,
        originalVolume: defaults.originalVolume,
        zoneType: defaults.zoneType,
        volumeRatio: defaults.volumeRatio,
        rules: createDefaultRules(),

        get statutoryVolume(): number {
            return this.baseArea * this.volumeRatio;
        },

        get maxAllowedReward(): number {
            const c1 = Math.max(0, this.originalVolume * 1.2 - this.originalVolume);
            const c2 = Math.max(0, (this.originalVolume + this.statutoryVolume * 0.3) - this.statutoryVolume);
            const c3 = Math.max(0, (this.statutoryVolume + this.statutoryVolume * 0.5) - this.statutoryVolume);
            return Math.max(c1, c2, c3);
        },

        get totalRewardArea(): number {
            return REWARD_RULE_KEYS.reduce((sum, key) => {
                const value = this.rules[key] ?? 0;
                return sum + (this.statutoryVolume * (value / 100));
            }, 0);
        },

        resetForm(): void {
            this.baseArea = defaults.baseArea;
            this.originalVolume = defaults.originalVolume;
            this.zoneType = defaults.zoneType;
            this.volumeRatio = defaults.volumeRatio;
            this.rules = createDefaultRules();
        }
    };
}

window.volumeCalculator = createVolumeCalculator;

document.addEventListener("DOMContentLoaded", () => {
    window.lucide?.createIcons();
});
