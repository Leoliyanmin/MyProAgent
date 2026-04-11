from database.code.database_user_operations import UserOperations


class UserHandle:
    """用户功能调用入口"""

    def __init__(self):
        self.operations = UserOperations()

    def create_user(self, email: str, username: str) -> dict:
        """创建用户入口"""
        # 验证输入
        if not email or not username:
            return {'ok': False, 'status': 400, 'message': '邮箱和用户名不能为空'}
        
        # 检查用户是否已存在
        existing_user = self.operations.get_user_by_email(email)
        if existing_user:
            return {'ok': False, 'status': 409, 'message': '用户已存在'}
        
        try:
            # 使用邮箱作为 user_id
            self.operations.create_user(user_id=email, email=email, username=username)
            return {'ok': True, 'status': 201, 'message': '用户创建成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'创建用户失败: {str(e)}'}

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
            
            return {'ok': True, 'status': 200, 'data': user}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取用户失败: {str(e)}'}

    def update_user(self, user_id: str, update_data: dict) -> dict:
        """更新用户入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        # 检查用户是否存在
        existing_user = self.operations.get_user_by_id(user_id)
        if not existing_user:
            return {'ok': False, 'status': 404, 'message': '用户不存在'}
        
        try:
            self.operations.update_user(user_id, update_data)
            return {'ok': True, 'status': 200, 'message': '用户更新成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'更新用户失败: {str(e)}'}

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