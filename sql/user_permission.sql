-- 权限表：用户与权限层级映射
CREATE TABLE IF NOT EXISTS user_permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE,          -- 用户姓名，用于从提示词提取身份
    tier TEXT NOT NULL CHECK(tier IN ('T0', 'T1', 'T2', 'T3')),  -- 权限层级
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- T0: 最高权限，可查询所有层级文档
-- T1: 可查询 T1、T2、T3 层文档
-- T2: 可查询 T2、T3 层文档
-- T3: 仅可查询 T3 层文档

-- 虚拟测试数据
INSERT INTO user_permission (user_name, tier) VALUES
    ('王刚', 'T0'),
    ('李明', 'T1'),
    ('张伟', 'T2'),
    ('刘洋', 'T3'),
    ('赵强', 'T0'),
    ('陈红', 'T1'),
    ('周杰', 'T2'),
    ('吴晓', 'T3');
