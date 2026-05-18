import pytest
from business.auth_service import AuthService


class TestPasswordValidation:
    def setup_method(self):
        self.auth = AuthService()

    def test_password_too_short(self):
        result = self.auth.validate_password('Ab1')
        assert result['valid'] is False
        assert '8' in result['message']

    def test_password_missing_uppercase(self):
        result = self.auth.validate_password('abcdefgh1')
        assert result['valid'] is False
        assert '大写' in result['message']

    def test_password_missing_lowercase(self):
        result = self.auth.validate_password('ABCDEFGH1')
        assert result['valid'] is False
        assert '小写' in result['message']

    def test_password_missing_digit(self):
        result = self.auth.validate_password('Abcdefgh')
        assert result['valid'] is False
        assert '数字' in result['message']

    def test_valid_password(self):
        result = self.auth.validate_password('Abcdefgh1')
        assert result['valid'] is True


class TestEmailValidation:
    def setup_method(self):
        self.auth = AuthService()

    def test_valid_sustech_email(self):
        assert self.auth.validate_email('student@mail.sustech.edu.cn') is True

    def test_invalid_domain(self):
        assert self.auth.validate_email('student@gmail.com') is False

    def test_no_at_sign(self):
        assert self.auth.validate_email('notanemail') is False


class TestTokenCreationAndDecoding:
    def setup_method(self):
        self.auth = AuthService()

    def test_create_and_decode_token(self):
        token = self.auth.create_access_token(data={'sub': 'user1', 'user_id': 'user1'})
        payload = self.auth.decode_token(token)
        assert payload is not None
        assert payload['sub'] == 'user1'
        assert payload['user_id'] == 'user1'
        assert 'exp' in payload

    def test_decode_invalid_token(self):
        payload = self.auth.decode_token('not.a.real.token')
        assert payload is None


class TestRegisterDataValidation:
    def setup_method(self):
        self.auth = AuthService()

    def test_email_invalid(self):
        result = self.auth.validate_registration_data(
            'bad@gmail.com', 'Abcdefgh1', 'Abcdefgh1', '123456'
        )
        assert result['valid'] is False
        assert '邮箱' in result['message']

    def test_password_mismatch(self):
        result = self.auth.validate_registration_data(
            'test@mail.sustech.edu.cn', 'Abcdefgh1', 'Different1', '123456'
        )
        assert result['valid'] is False
        assert '不一致' in result['message']

    def test_all_valid(self):
        result = self.auth.validate_registration_data(
            'test@mail.sustech.edu.cn', 'Abcdefgh1', 'Abcdefgh1', '123456'
        )
        assert result['valid'] is True


class TestPasswordHashing:
    def setup_method(self):
        self.auth = AuthService()

    def test_hash_and_verify(self):
        hashed = self.auth.get_password_hash('mysecret')
        assert self.auth.verify_password('mysecret', hashed) is True

    def test_wrong_password_fails(self):
        hashed = self.auth.get_password_hash('mysecret')
        assert self.auth.verify_password('wrongsecret', hashed) is False
