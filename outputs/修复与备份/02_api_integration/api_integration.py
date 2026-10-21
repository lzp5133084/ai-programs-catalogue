"""
信用卡管理系统 - 外部API集成模块

提供标准化的RESTful API接口，供外部应用程序和系统集成调用。
支持用户认证、数据查询、操作执行等功能，采用OAuth2.0标准协议。
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
import jwt
import datetime
from functools import wraps
import logging
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 创建API蓝图
api_integration = Blueprint('api_integration', __name__, url_prefix='/api/v1')
CORS(api_integration, origins=['*'], allow_headers=['Authorization', 'Content-Type'])

# API密钥配置（生产环境应该从环境变量或安全存储中获取）
API_KEYS = {
    'test_client_1': 'test_secret_key_1',
    'test_client_2': 'test_secret_key_2'
}

# JWT配置
JWT_SECRET = 'your_jwt_secret_key'  # 生产环境应该使用强密钥并从环境变量获取
JWT_EXPIRATION = 3600  # 1小时


def verify_api_key(api_key: str) -> bool:
    """验证API密钥"""
    return api_key in API_KEYS.values()


def generate_token(client_id: str) -> str:
    """生成JWT令牌"""
    payload = {
        'client_id': client_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("令牌已过期")
        return None
    except jwt.InvalidTokenError:
        logger.warning("无效的令牌")
        return None


def token_required(f):
    """API认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # 检查令牌是否存在
        if not token:
            return jsonify({
                'error': '认证失败',
                'message': '缺少认证令牌'
            }), 401
        
        # 验证令牌
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'error': '认证失败',
                'message': '无效或过期的令牌'
            }), 401
        
        # 将客户端信息添加到请求上下文
        request.client_id = payload['client_id']
        
        return f(*args, **kwargs)
    
    return decorated


# ------------ 认证相关API ------------

@api_integration.route('/auth/token', methods=['POST'])
def get_token():
    """
    获取访问令牌
    
    客户端认证并获取API访问令牌
    
    请求参数:
        - client_id: 客户端ID
        - client_secret: 客户端密钥
    
    返回:
        - token: JWT访问令牌
        - expires_in: 令牌有效期（秒）
    """
    try:
        data = request.get_json()
        
        if not data or 'client_id' not in data or 'client_secret' not in data:
            return jsonify({
                'error': '参数错误',
                'message': '缺少client_id或client_secret参数'
            }), 400
        
        client_id = data['client_id']
        client_secret = data['client_secret']
        
        # 验证客户端凭证
        if client_id not in API_KEYS or API_KEYS[client_id] != client_secret:
            return jsonify({
                'error': '认证失败',
                'message': '无效的客户端凭证'
            }), 401
        
        # 生成令牌
        token = generate_token(client_id)
        
        return jsonify({
            'token': token,
            'expires_in': JWT_EXPIRATION,
            'token_type': 'Bearer'
        }), 200
    
    except Exception as e:
        logger.error(f"生成令牌时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '生成令牌时发生错误'
        }), 500


# ------------ 用户相关API ------------

@api_integration.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id: int):
    """
    获取用户信息
    
    根据用户ID获取用户详细信息
    
    参数:
        - user_id: 用户ID
    
    返回:
        - 用户详细信息
    """
    try:
        # 从服务层获取用户信息（这里使用模拟数据）
        # 实际应用中应该调用UserService
        user_data = {
            'id': user_id,
            'name': '张伟',
            'email': 'zhangwei@example.com',
            'phone': '13800138000',
            'created_at': '2023-01-15T08:30:00Z',
            'status': 'active'
        }
        
        return jsonify({
            'success': True,
            'data': user_data
        }), 200
    
    except Exception as e:
        logger.error(f"获取用户信息时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '获取用户信息时发生错误'
        }), 500


# ------------ 信用卡相关API ------------

@api_integration.route('/users/<int:user_id>/cards', methods=['GET'])
@token_required
def get_user_cards(user_id: int):
    """
    获取用户信用卡列表
    
    获取指定用户的所有信用卡信息
    
    参数:
        - user_id: 用户ID
    
    查询参数:
        - status: 可选，卡片状态过滤
    
    返回:
        - 信用卡列表
    """
    try:
        status_filter = request.args.get('status')
        
        # 从服务层获取信用卡信息（这里使用模拟数据）
        # 实际应用中应该调用CreditCardService
        cards_data = [
            {
                'id': 1,
                'user_id': user_id,
                'bank_name': '招商银行',
                'card_type': '白金信用卡',
                'card_number': '****8629',
                'total_limit': 50000.0,
                'used_limit': 3250.50,
                'available_limit': 46749.50,
                'status': 'active',
                'expiry_date': '2028-10-31'
            },
            {
                'id': 2,
                'user_id': user_id,
                'bank_name': '中国银行',
                'card_type': '环球通卡',
                'card_number': '****5312',
                'total_limit': 30000.0,
                'used_limit': 5491.80,
                'available_limit': 24508.20,
                'status': 'active',
                'expiry_date': '2027-08-31'
            }
        ]
        
        # 应用状态过滤
        if status_filter:
            cards_data = [card for card in cards_data if card['status'] == status_filter]
        
        return jsonify({
            'success': True,
            'data': cards_data,
            'total': len(cards_data)
        }), 200
    
    except Exception as e:
        logger.error(f"获取信用卡列表时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '获取信用卡列表时发生错误'
        }), 500


# ------------ 交易相关API ------------

@api_integration.route('/cards/<int:card_id>/transactions', methods=['GET'])
@token_required
def get_card_transactions(card_id: int):
    """
    获取信用卡交易记录
    
    获取指定信用卡的交易记录列表
    
    参数:
        - card_id: 信用卡ID
    
    查询参数:
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)
        - page: 页码
        - limit: 每页数量
    
    返回:
        - 交易记录列表
        - 分页信息
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 从服务层获取交易记录（这里使用模拟数据）
        # 实际应用中应该调用TransactionService
        transactions_data = [
            {
                'id': 1,
                'card_id': card_id,
                'amount': 285.00,
                'merchant': '海底捞火锅',
                'category': '餐饮',
                'transaction_date': '2023-06-12T12:30:00Z',
                'status': 'completed'
            },
            {
                'id': 2,
                'card_id': card_id,
                'amount': 799.00,
                'merchant': '京东商城',
                'category': '购物',
                'transaction_date': '2023-06-12T10:15:00Z',
                'status': 'completed'
            },
            {
                'id': 3,
                'card_id': card_id,
                'amount': 35.50,
                'merchant': '滴滴出行',
                'category': '交通',
                'transaction_date': '2023-06-11T19:45:00Z',
                'status': 'completed'
            }
        ]
        
        # 计算分页
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_transactions = transactions_data[start_index:end_index]
        
        return jsonify({
            'success': True,
            'data': paginated_transactions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(transactions_data),
                'total_pages': (len(transactions_data) + limit - 1) // limit
            }
        }), 200
    
    except Exception as e:
        logger.error(f"获取交易记录时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '获取交易记录时发生错误'
        }), 500


# ------------ 账单相关API ------------

@api_integration.route('/cards/<int:card_id>/bills', methods=['GET'])
@token_required
def get_card_bills(card_id: int):
    """
    获取信用卡账单
    
    获取指定信用卡的账单信息
    
    参数:
        - card_id: 信用卡ID
    
    查询参数:
        - year: 年份
        - month: 月份
        - status: 账单状态
    
    返回:
        - 账单信息列表
    """
    try:
        # 获取查询参数
        year = request.args.get('year')
        month = request.args.get('month')
        status = request.args.get('status')
        
        # 从服务层获取账单信息（这里使用模拟数据）
        # 实际应用中应该调用BillService
        bills_data = [
            {
                'id': 1,
                'card_id': card_id,
                'bill_date': '2023-05-25',
                'due_date': '2023-06-15',
                'total_amount': 3250.50,
                'minimum_payment': 325.05,
                'paid_amount': 0.0,
                'status': 'unpaid',
                'year': 2023,
                'month': 5
            }
        ]
        
        return jsonify({
            'success': True,
            'data': bills_data
        }), 200
    
    except Exception as e:
        logger.error(f"获取账单信息时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '获取账单信息时发生错误'
        }), 500


# ------------ 还款推荐API ------------

@api_integration.route('/users/<int:user_id>/recommendations/payment', methods=['GET'])
@token_required
def get_payment_recommendations(user_id: int):
    """
    获取还款推荐
    
    获取智能还款策略推荐
    
    参数:
        - user_id: 用户ID
    
    返回:
        - 还款推荐列表
    """
    try:
        # 从服务层获取推荐信息（这里使用模拟数据）
        # 实际应用中应该调用RecommendationService
        recommendations_data = [
            {
                'id': 1,
                'user_id': user_id,
                'card_id': 1,
                'card_name': '招商银行 - 白金信用卡',
                'recommended_amount': 3250.50,
                'reason': '优先偿还高额账单以减少利息',
                'estimated_interest_saved': 45.50,
                'priority': 'high'
            },
            {
                'id': 2,
                'user_id': user_id,
                'card_id': 2,
                'card_name': '中国银行 - 环球通卡',
                'recommended_amount': 2000.00,
                'reason': '部分还款以降低信用使用率',
                'estimated_interest_saved': 18.20,
                'priority': 'medium'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': recommendations_data
        }), 200
    
    except Exception as e:
        logger.error(f"获取还款推荐时出错: {str(e)}")
        return jsonify({
            'error': '服务器错误',
            'message': '获取还款推荐时发生错误'
        }), 500


# ------------ 健康检查API ------------

@api_integration.route('/health', methods=['GET'])
def health_check():
    """
    API健康检查
    
    用于监控和确认API服务是否正常运行
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'api_version': 'v1.0.0'
    }), 200


# ------------ API文档路由 ------------

@api_integration.route('/docs', methods=['GET'])
def api_docs():
    """
    API文档
    
    返回API使用说明和文档
    """
    docs = {
        'api_name': '信用卡管理系统API',
        'version': 'v1.0.0',
        'description': '提供信用卡管理系统的外部集成接口',
        'endpoints': [
            {
                'path': '/api/v1/auth/token',
                'method': 'POST',
                'description': '获取访问令牌',
                'requires_auth': False
            },
            {
                'path': '/api/v1/users/{user_id}',
                'method': 'GET',
                'description': '获取用户信息',
                'requires_auth': True
            },
            {
                'path': '/api/v1/users/{user_id}/cards',
                'method': 'GET',
                'description': '获取用户信用卡列表',
                'requires_auth': True
            },
            {
                'path': '/api/v1/cards/{card_id}/transactions',
                'method': 'GET',
                'description': '获取信用卡交易记录',
                'requires_auth': True
            },
            {
                'path': '/api/v1/cards/{card_id}/bills',
                'method': 'GET',
                'description': '获取信用卡账单',
                'requires_auth': True
            },
            {
                'path': '/api/v1/users/{user_id}/recommendations/payment',
                'method': 'GET',
                'description': '获取还款推荐',
                'requires_auth': True
            },
            {
                'path': '/api/v1/health',
                'method': 'GET',
                'description': 'API健康检查',
                'requires_auth': False
            }
        ],
        'authentication': {
            'type': 'OAuth 2.0 Bearer Token',
            'endpoint': '/api/v1/auth/token',
            'expires_in': 3600
        },
        'rate_limiting': '每IP每分钟最多60次请求',
        'contact': 'support@example.com'
    }
    
    return jsonify(docs), 200


def register_api_routes(app):
    """
    注册API路由到Flask应用
    """
    app.register_blueprint(api_integration)
    logger.info("API集成模块已注册")


# API使用示例代码
API_EXAMPLE_CODE = '''
# Python SDK 示例代码

import requests
import json

class CreditCardAPIClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "http://localhost:5000/api/v1"
        self.token = None
        self.token_expiry = None
    
    def _get_token(self):
        """获取访问令牌"""
        url = f"{self.base_url}/auth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.token_expiry = time.time() + data['expires_in']
            return True
        return False
    
    def _ensure_token(self):
        """确保令牌有效"""
        if not self.token or time.time() >= self.token_expiry - 300:  # 提前5分钟刷新
            return self._get_token()
        return True
    
    def get_user(self, user_id):
        """获取用户信息"""
        if not self._ensure_token():
            return None
        
        url = f"{self.base_url}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_user_cards(self, user_id, status=None):
        """获取用户信用卡列表"""
        if not self._ensure_token():
            return None
        
        url = f"{self.base_url}/users/{user_id}/cards"
        params = {} if status is None else {"status": status}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None

# 使用示例
if __name__ == "__main__":
    import time
    
    # 初始化客户端
    client = CreditCardAPIClient("test_client_1", "test_secret_key_1")
    
    # 获取用户信息
    user_info = client.get_user(1)
    if user_info:
        print("用户信息:", json.dumps(user_info, indent=2, ensure_ascii=False))
    
    # 获取用户信用卡列表
    cards = client.get_user_cards(1)
    if cards:
        print("信用卡列表:", json.dumps(cards, indent=2, ensure_ascii=False))
'''

# API响应格式定义
API_RESPONSE_FORMATS = {
    "success": {
        "success": True,
        "data": "响应数据对象或数组",
        "pagination": {"optional": "分页信息对象"}
    },
    "error": {
        "error": "错误类型",
        "message": "错误描述"
    }
}