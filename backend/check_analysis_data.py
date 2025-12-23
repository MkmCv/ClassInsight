"""
检查分析数据脚本
运行: python check_analysis_data.py
"""
import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('storage/classinsight.db')

print("=" * 60)
print("📊 ClassInsight 分析数据检查")
print("=" * 60)

# 1. 查看所有视频
print("\n【1. 视频列表】")
videos = conn.execute('''
    SELECT id, filename, duration, status, total_frames, fps 
    FROM videos 
    ORDER BY id DESC
''').fetchall()

if videos:
    for v in videos:
        print(f"  ID: {v[0]} | 文件: {v[1]} | 时长: {v[2]:.1f}秒 | 状态: {v[3]} | 帧数: {v[4]} | FPS: {v[5]}")
else:
    print("  (无视频数据)")

# 2. 查看最新视频的汇总数据
print("\n【2. 最新视频的汇总统计】")
summary = conn.execute('''
    SELECT v.id, v.filename, s.summary_json, s.total_detections, 
           s.interaction_rate, s.attention_rate, s.engagement_score
    FROM videos v
    JOIN analysis_summary s ON v.id = s.video_id
    ORDER BY v.id DESC
    LIMIT 1
''').fetchone()

if summary:
    print(f"  视频ID: {summary[0]}")
    print(f"  文件名: {summary[1]}")
    print(f"  总检测数: {summary[3]}")
    print(f"  互动率: {summary[4]*100:.1f}%")
    print(f"  专注度: {summary[5]*100:.1f}%")
    print(f"  参与度: {summary[6]*100:.1f}%")
    
    print("\n  行为统计明细:")
    summary_json = json.loads(summary[2]) if summary[2] else {}
    behavior_summary = summary_json.get('behavior_summary', {})
    
    for behavior, stats in sorted(behavior_summary.items(), key=lambda x: x[1].get('count', 0), reverse=True):
        count = stats.get('count', 0)
        duration = stats.get('total_duration', 0)
        pct = stats.get('percentage', 0)
        print(f"    {behavior:20s} | 检测次数: {count:5d} | 出现时长: {duration:4d}秒 | 占比: {pct:5.1f}%")
else:
    print("  (无汇总数据)")

# 3. 查看时间线数据（前20条）
print("\n【3. 时间线数据（前20个时间窗口）】")
timeline = conn.execute('''
    SELECT timestamp, window_size, behavior_counts
    FROM analysis_timeline
    ORDER BY video_id DESC, timestamp ASC
    LIMIT 20
''').fetchall()

if timeline:
    print(f"  {'时间(秒)':<10} | {'窗口大小':<8} | 检测行为")
    print("  " + "-" * 70)
    for t in timeline:
        ts = t[0]
        ws = t[1]
        behaviors = json.loads(t[2]) if t[2] else {}
        behavior_str = ", ".join([f"{k}:{v}" for k, v in behaviors.items() if v > 0])
        print(f"  {ts:<10} | {ws:<8} | {behavior_str}")
else:
    print("  (无时间线数据)")

# 4. 查看异常事件
print("\n【4. 异常事件】")
anomalies = conn.execute('''
    SELECT start_time, end_time, anomaly_type, severity, description
    FROM analysis_anomalies
    ORDER BY video_id DESC, start_time ASC
''').fetchall()

if anomalies:
    for a in anomalies:
        print(f"  [{a[3].upper():6s}] {a[0]//60}:{a[0]%60:02d} - {a[1]//60}:{a[1]%60:02d} | {a[2]}: {a[4]}")
else:
    print("  (无异常事件)")

# 5. 查看原始检测数据样本
print("\n【5. 原始检测框数据样本（最近一条）】")
detections = conn.execute('''
    SELECT timestamp, detections
    FROM analysis_timeline
    WHERE detections IS NOT NULL
    ORDER BY video_id DESC, timestamp ASC
    LIMIT 1
''').fetchone()

if detections and detections[1]:
    print(f"  时间戳: {detections[0]}秒")
    det_list = json.loads(detections[1])
    print(f"  检测框数量: {len(det_list)}")
    print("  样本数据:")
    for i, det in enumerate(det_list[:5]):  # 只显示前5个
        print(f"    [{i+1}] {json.dumps(det, ensure_ascii=False)}")
    if len(det_list) > 5:
        print(f"    ... 还有 {len(det_list)-5} 条")
else:
    print("  (无检测框数据)")

conn.close()

print("\n" + "=" * 60)
print("检查完成!")
print("=" * 60)




