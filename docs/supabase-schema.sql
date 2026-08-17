-- meansights learning · 持久层建表
--
-- ✅ 已于 2026-08-17 应用到项目 meansights-learning（ref udesghhdryhchzvluoxx，
--    新加坡 ap-southeast-1，与 Render 后端同区）。本文件保留为建表真相源：
--    重建环境、灾后恢复、或再开一套时照跑即可。
--
-- 用法：Supabase 控制台 → SQL Editor → 整份粘贴 → Run。
-- 然后把 Project Settings → API 里的 URL 和 service_role key 填进 Render 的
-- SUPABASE_URL / SUPABASE_KEY，重启服务即自动切换（backend/store.py 会打日志确认模式）。
--
-- ⚠️ 这个项目要用**新建的**，别跟 meansights 主站的库混在一起。
-- ⚠️ 用 service_role key（服务端持有，永不下发到浏览器）。下面的 RLS 策略是双保险：
--    即便 key 泄漏成 anon，也只能写不能读——读要走后端带 ADMIN_CODE 的 insights 端点。

-- 课程反馈：用户明说的「这节看不懂 / 有建议」
create table if not exists hab_feedback (
  id          bigserial primary key,
  created_at  timestamptz not null default now(),
  lesson      text    default '',      -- 课件文件名，服务端已校验存在性；空=没挂到具体某节
  kind        text    not null,        -- hard | confusing | error | suggest
  note        text    not null,        -- 一句话转述对方原意
  visitor     text    default '',      -- 匿名访客 id（track.js 的 hab_vid，不含个人信息）
  source      text    default 'chat'   -- chat=对话中被模型捕获 / direct=模型挂了走直投
);
create index if not exists hab_feedback_lesson_idx on hab_feedback (lesson, created_at desc);

-- 难度信号：行为侧，用户一个字都不用说
create table if not exists hab_signal (
  id          bigserial primary key,
  created_at  timestamptz not null default now(),
  lesson      text    not null,
  dwell_s     integer not null default 0,   -- 实际停留秒数（已扣掉切后台的时间）
  kind        text    not null default 'stuck',
  visitor     text    default ''
);
create index if not exists hab_signal_lesson_idx on hab_signal (lesson, created_at desc);

-- RLS：只写不读。读一律走后端。
alter table hab_feedback enable row level security;
alter table hab_signal   enable row level security;

drop policy if exists hab_feedback_insert on hab_feedback;
drop policy if exists hab_signal_insert   on hab_signal;
create policy hab_feedback_insert on hab_feedback for insert to anon, authenticated with check (true);
create policy hab_signal_insert   on hab_signal   for insert to anon, authenticated with check (true);
