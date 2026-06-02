# ClassInsight 文档中心

> 课堂行为智能分析系统 —— 文档导航

## 目录结构

```
docs/
├── README.md              # 本文档索引
├── super-admin.md         # 超级管理员系统说明
├── database.md            # 数据库总览（ER 关系、表说明）
├── backend/               # 后端文档
│   ├── api.md             # REST API 接口文档
│   ├── database-design.md # 数据库详细设计
│   └── requirements.md    # 后端功能与依赖说明
├── frontend/              # 前端文档
│   ├── architecture.md    # 前端架构
│   ├── interface.md       # 前端与后端接口约定
│   ├── tech-summary.md    # 前端技术选型总结
│   ├── admin-page-spec.md # 管理员页面规格
│   └── user-guide.md      # 用户使用指南
└── behavior/              # 行为分析算法文档
    ├── analysis-flow.md   # 行为分析整体流程
    ├── classifier.md      # 行为分类器实现
    ├── correlation.md     # 相关性与模式分析
    └── microteaching.md   # 微格教学分析
```

## 快速导航

### 新成员入门
1. 阅读根目录 [README.md](../README.md) 了解项目概况与启动方式
2. 后端接口参考 [backend/api.md](./backend/api.md)
3. 数据库结构参考 [database.md](./database.md) 与 [backend/database-design.md](./backend/database-design.md)

### 按主题查阅
- **行为分析算法**：见 [behavior/](./behavior/) 目录
- **前端开发**：见 [frontend/](./frontend/) 目录
- **超级管理员系统**：见 [super-admin.md](./super-admin.md)

> 说明：视觉算法（YOLO-vHeat）已拆分为独立项目维护；论文与答辩材料不纳入本仓库。
