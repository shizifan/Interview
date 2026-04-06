from fastapi import Request
from fastapi.responses import JSONResponse


class BusinessError(Exception):
    """业务逻辑错误，返回HTTP 200但code为600+"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# 具体业务错误码
ERR_DAILY_LIMIT = 601        # 每日面试次数已达上限
ERR_RECOVERY_EXPIRED = 602   # 面试恢复窗口已过期
ERR_INTERVIEW_STATUS = 603   # 面试状态不正确
ERR_JOB_NOT_ACTIVE = 604     # 岗位未发布
ERR_CANDIDATE_NOT_APPROVED = 605  # 候选人未通过审核
ERR_DOC_VALIDATION = 606     # 材料校验失败
ERR_NO_QUESTIONS = 607       # 题库为空
ERR_PHONE_EXISTS = 608       # 手机号已存在
ERR_AUTH_INVALID = 609       # 认证无效或已过期
ERR_LOGIN_FAILED = 611       # 用户名或密码错误


async def business_error_handler(_request: Request, exc: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None},
    )
