-- PostgreSQL初始化脚本
-- 为MaiMBot创建数据库和配置

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 设置时区
SET timezone = 'UTC';

-- 创建索引优化配置
-- 这些将在表创建后由应用程序处理

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '数据库 % 初始化完成', 'ai_saas';
END $$;
