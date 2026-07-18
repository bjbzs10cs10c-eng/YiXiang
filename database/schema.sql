-- 易象数据库建表脚本

-- 六十四卦表
CREATE TABLE IF NOT EXISTS hexagrams (
    id INTEGER PRIMARY KEY,
    sequence INTEGER NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT,
    binary_code TEXT NOT NULL UNIQUE,
    upper_trigram TEXT,
    lower_trigram TEXT,
    gua_ci TEXT,
    tuan_ci TEXT,
    xiang_ci TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 爻辞表（64卦 × 6爻 = 384爻）
CREATE TABLE IF NOT EXISTS yao_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hexagram_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    yao_name TEXT,
    yao_type TEXT,
    original_text TEXT,
    translation TEXT,
    FOREIGN KEY(hexagram_id) REFERENCES hexagrams(id)
);

-- 多版本解释表
CREATE TABLE IF NOT EXISTS interpretations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    source TEXT,
    title TEXT,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 占卜记录表
CREATE TABLE IF NOT EXISTS divination_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    question TEXT,
    original_hexagram INTEGER,
    changed_hexagram INTEGER,
    moving_lines TEXT,
    yao_values TEXT,
    notes TEXT,
    ai_interpretation TEXT,
    ai_model TEXT,
    FOREIGN KEY(original_hexagram) REFERENCES hexagrams(id),
    FOREIGN KEY(changed_hexagram) REFERENCES hexagrams(id)
);

-- 设置表
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_hex_binary ON hexagrams(binary_code);
CREATE INDEX IF NOT EXISTS idx_hex_name ON hexagrams(name);
CREATE INDEX IF NOT EXISTS idx_interpretation_target ON interpretations(target_type, target_id);
