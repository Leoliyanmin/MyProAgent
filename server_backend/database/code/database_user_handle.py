from database.code.database_user_operations import ServerUserOperations


class ServerUserHandle:
    """服务端用户功能调用入口"""

    def __init__(self):
        self.operations = ServerUserOperations()

    def register_user(self, email: str, username: str, password: str) -> dict:
        """注册用户入口"""
        # 验证输入
        if not email or not username or not password:
            return {'ok': False, 'status': 400, 'message': '邮箱、用户名和密码不能为空'}
        
        # 检查用户是否已存在
        existing_user = self.operations.get_user_by_email(email)
        if existing_user:
            return {'ok': False, 'status': 409, 'message': '用户已存在'}
        
        try:
            # 使用邮箱作为 user_id
            self.operations.create_user(user_id=email, email=email, username=username, password=password)
            return {'ok': True, 'status': 201, 'message': '用户注册成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'注册失败: {str(e)}'}

    def login_user(self, email: str, password: str) -> dict:
        """登录用户入口"""
        # 验证输入
        if not email or not password:
            return {'ok': False, 'status': 400, 'message': '邮箱和密码不能为空'}
        
        try:
            # 获取用户
            user = self.operations.get_user_by_email(email)
            if not user:
                return {'ok': False, 'status': 401, 'message': '邮箱或密码错误'}
            
            # 验证密码
            if not self.operations.verify_password(user, password):
                return {'ok': False, 'status': 401, 'message': '邮箱或密码错误'}
            
            # 更新登录时间
            self.operations.update_user(user['user_id'], {})
            
            return {
                'ok': True,
                'status': 200,
                'data': {
                    'user_id': user['user_id'],
                    'email': user['user_email'],
                    'username': user['username']
                }
            }
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'登录失败: {str(e)}'}

    def get_user(self, user_id: str = None, email: str = None) -> dict:
        """获取用户入口"""
        if not user_id and not email:
            return {'ok': False, 'status': 400, 'message': '必须提供 user_id 或 email'}
        
        try:
            if user_id:
                user = self.operations.get_user_by_id(user_id)
            else:
                user = self.operations.get_user_by_email(email)
            
            if not user:
                return {'ok': False, 'status': 404, 'message': '用户不存在'}
            
            # 过滤敏感信息
            user_data = {k: v for k, v in user.items() if k not in ['user_password_hash', 'user_salt']}
            
            return {'ok': True, 'status': 200, 'data': user_data}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取用户失败: {str(e)}'}

    def delete_user(self, user_id: str) -> dict:
        """删除用户入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        # 检查用户是否存在
        existing_user = self.operations.get_user_by_id(user_id)
        if not existing_user:
            return {'ok': False, 'status': 404, 'message': '用户不存在'}
        
        try:
            self.operations.delete_user_by_id(user_id)
            return {'ok': True, 'status': 200, 'message': '用户删除成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'删除用户失败: {str(e)}'}