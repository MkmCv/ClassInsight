"""
课表相关的 Pydantic 模式
"""
from datetime import datetime, date as DateType, time as TimeType
from typing import Optional, List
from pydantic import BaseModel, Field


class ScheduleBase(BaseModel):
    """课表基础模式"""
    course_name: str = Field(..., max_length=50, description="课程名称")
    class_name: str = Field(..., max_length=50, description="班级名称")
    day_of_week: int = Field(..., ge=0, le=6, description="星期几，0=周一，6=周日")
    start_time: TimeType = Field(..., description="开始时间")
    end_time: TimeType = Field(..., description="结束时间")


class ScheduleCreate(ScheduleBase):
    """创建课表请求"""
    user_id: Optional[int] = Field(None, description="教师ID，管理员创建时必填")


class ScheduleUpdate(BaseModel):
    """更新课表请求"""
    course_name: Optional[str] = Field(None, max_length=50)
    class_name: Optional[str] = Field(None, max_length=50)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[TimeType] = None
    end_time: Optional[TimeType] = None


class ScheduleResponse(ScheduleBase):
    """课表响应"""
    id: int
    user_id: int
    teacher_name: Optional[str] = None  # 关联的教师名称
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ScheduleWithStatus(ScheduleResponse):
    """带状态的课表响应（用于首页日历）"""
    status: str = "upcoming"  # finished, ongoing, upcoming
    schedule_date: Optional[DateType] = None  # 具体日期（用于周视图）


class WeekScheduleRequest(BaseModel):
    """获取周课表请求"""
    target_date: DateType = Field(..., description="周内任意一天的日期")


class DayScheduleResponse(BaseModel):
    """某天的课表响应"""
    date: DateType
    day_of_week: int
    day_name: str  # 星期一、星期二...
    schedules: List[ScheduleWithStatus]


class WeekScheduleResponse(BaseModel):
    """周课表响应"""
    week_start: DateType  # 周一日期
    week_end: DateType    # 周日日期
    days: List[DayScheduleResponse]
