"""
API 客户端 - 用于前端与后端 API 通信

使用说明：
1. 将此文件放在 frontend/ 目录下
2. 在页面中用 api_client 替换 mock_data 的导入
3. 示例：from api_client import get_analysis_summary
"""
import os
import requests
from typing import Optional, Dict, Any, List
from datetime import date
import streamlit as st

# API 基础配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class APIClient:
    """API 客户端类"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（包含认证Token）"""
        headers = {"Content-Type": "application/json"}
        
        # 从 session_state 获取 token
        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
        
        return headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        # 如果有文件上传，移除 Content-Type（让 requests 自动设置）
        if files:
            headers.pop("Content-Type", None)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if not files else None,
                data=data if files else None,
                params=params,
                headers=headers,
                files=files,
                timeout=30
            )
            
            # 处理错误响应
            if response.status_code >= 400:
                error_detail = response.json().get("detail", "请求失败")
                raise APIError(response.status_code, error_detail)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.ConnectionError:
            raise APIError(0, "无法连接到服务器，请检查后端服务是否启动")
        except requests.exceptions.Timeout:
            raise APIError(0, "请求超时，请稍后重试")
    
    # ========== 认证模块 ==========
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        response = self._request(
            "POST",
            "/auth/login/json",
            data={"username": username, "password": password}
        )
        
        # 保存 token 到 session_state
        if "access_token" in response:
            st.session_state["access_token"] = response["access_token"]
            st.session_state["user"] = response.get("user", {})
            st.session_state["authentication_status"] = True
        
        return response
    
    def register(self, username: str, email: str, password: str, 
                 role: str = "teacher", unit: str = None, class_name: str = None) -> Dict:
        """用户注册"""
        return self._request(
            "POST",
            "/auth/register",
            data={
                "username": username,
                "email": email,
                "password": password,
                "role": role,
                "unit": unit,
                "class_name": class_name
            }
        )
    
    def get_current_user(self) -> Dict:
        """获取当前用户信息"""
        return self._request("GET", "/auth/me")
    
    # ========== 首页模块 ==========
    
    def get_dashboard_schedule(self) -> Dict:
        """获取今日课程表"""
        return self._request("GET", "/dashboard/schedule")
    
    def get_dashboard_metrics(self) -> Dict:
        """获取首页指标"""
        return self._request("GET", "/dashboard/metrics")
    
    def get_recent_videos(self, limit: int = 5) -> Dict:
        """获取最近视频"""
        return self._request("GET", "/dashboard/recent-videos", params={"limit": limit})
    
    # ========== 视频模块 ==========
    
    def upload_video(
        self, 
        file, 
        class_name: str = None,
        course_name: str = None,
        lesson_date: str = None
    ) -> Dict:
        """上传视频"""
        files = {"file": (file.name, file, "video/mp4")}
        data = {}
        if class_name:
            data["class_name"] = class_name
        if course_name:
            data["course_name"] = course_name
        if lesson_date:
            data["lesson_date"] = lesson_date
        
        return self._request("POST", "/videos/upload", data=data, files=files)
    
    def get_video_list(
        self,
        page: int = 1,
        page_size: int = 20,
        class_name: str = None,
        course_name: str = None,
        status: str = None
    ) -> Dict:
        """获取视频列表"""
        params = {"page": page, "page_size": page_size}
        if class_name:
            params["class_name"] = class_name
        if course_name:
            params["course_name"] = course_name
        if status:
            params["status_filter"] = status
        
        return self._request("GET", "/videos", params=params)
    
    def get_video_detail(self, video_id: int) -> Dict:
        """获取视频详情"""
        return self._request("GET", f"/videos/{video_id}")
    
    def get_video_status(self, video_id: int) -> Dict:
        """获取视频处理状态"""
        return self._request("GET", f"/videos/{video_id}/status")
    
    def delete_video(self, video_id: int) -> None:
        """删除视频"""
        self._request("DELETE", f"/videos/{video_id}")
    
    # ========== 分析模块 ==========
    
    def get_analysis_summary(self, video_id: int) -> Dict:
        """获取整课行为统计"""
        return self._request("GET", f"/analysis/{video_id}/summary")
    
    def get_analysis_timeline(self, video_id: int, window: int = 10) -> Dict:
        """获取时间序列数据"""
        return self._request("GET", f"/analysis/{video_id}/timeline", params={"window": window})
    
    def get_analysis_anomalies(self, video_id: int, threshold: float = 2.0) -> Dict:
        """获取异常时段"""
        return self._request("GET", f"/analysis/{video_id}/anomalies", params={"threshold": threshold})
    
    def get_analysis_causation(self, video_id: int) -> Dict:
        """获取行为成因分析"""
        return self._request("GET", f"/analysis/{video_id}/causation")
    
    # ========== 优化模块 ==========
    
    def get_radar_data(self, video_id: int) -> Dict:
        """获取雷达图数据"""
        return self._request("GET", f"/optimization/{video_id}/radar")
    
    def get_recommendations(self, video_id: int) -> Dict:
        """获取优化建议"""
        return self._request("GET", f"/optimization/{video_id}/recommendations")
    
    def get_highlights(self, video_id: int, min_score: float = 0.8) -> Dict:
        """获取优秀片段"""
        return self._request("GET", f"/optimization/{video_id}/highlights", params={"min_score": min_score})
    
    def compare_videos(self, video_ids: List[int]) -> Dict:
        """跨课次对比"""
        ids_str = ",".join(str(id) for id in video_ids)
        return self._request("GET", "/optimization/compare", params={"video_ids": ids_str})


class APIError(Exception):
    """API 错误"""
    
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


# 创建全局客户端实例
api_client = APIClient()


# ========== 便捷函数（兼容 mock_data 接口）==========

def login(username: str, password: str) -> Dict:
    """用户登录"""
    return api_client.login(username, password)


def get_mock_schedule() -> List[Dict]:
    """获取课程表（兼容旧接口）"""
    try:
        result = api_client.get_dashboard_schedule()
        return result.get("schedule", [])
    except APIError:
        return []


def get_mock_metrics() -> Dict:
    """获取首页指标（兼容旧接口）"""
    try:
        return api_client.get_dashboard_metrics()
    except APIError:
        return {
            "interaction_rate": {"value": "0%", "delta": "0%"},
            "focus_rate": {"value": "0%", "delta": "0%"},
            "pending_videos": 0
        }


def get_mock_summary(video_id: int = 1) -> Dict:
    """获取分析汇总（兼容旧接口）"""
    try:
        return api_client.get_analysis_summary(video_id)
    except APIError:
        return {}


def get_mock_timeline(video_id: int = 1, window: int = 10) -> List[Dict]:
    """获取时间线数据（兼容旧接口）"""
    try:
        result = api_client.get_analysis_timeline(video_id, window)
        return result.get("timeline", [])
    except APIError:
        return []


def get_mock_recommendations(video_id: int = 1) -> List[Dict]:
    """获取优化建议（兼容旧接口）"""
    try:
        result = api_client.get_recommendations(video_id)
        return result.get("recommendations", [])
    except APIError:
        return []


def get_video_list() -> List[Dict]:
    """获取视频列表（兼容旧接口）"""
    try:
        result = api_client.get_video_list()
        return result.get("items", [])
    except APIError:
        return []


