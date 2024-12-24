import os
import socket
import pytest
from unittest.mock import Mock, patch
from smarch.handler import lambda_handler

@pytest.fixture
def mock_environment():
    """テスト用の環境変数を設定"""
    os.environ['SSM_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_ENDPOINT_URL'] = 'http://localhost:4566'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['SMB_HOST'] = 'samba'  # モックテスト用のホスト名
    yield
    del os.environ['SSM_ENDPOINT_URL']
    del os.environ['S3_ENDPOINT_URL']
    del os.environ['S3_BUCKET_NAME']
    del os.environ['SMB_HOST']



@patch('smarch.handler.boto3.client')
@patch('smarch.handler.SMBConnection')
def test_lambda_handler_smb_connection(mock_smb_connection, mock_boto3_client, mock_environment):
    """SMB接続処理をテスト"""
    def create_mock_ssm():
        mock = Mock()
        mock.get_parameter.side_effect = [
            {'Parameter': {'Value': 'testuser'}},
            {'Parameter': {'Value': 'testpass'}}
        ]
        return mock

    def create_mock_s3():
        return Mock()

    # SMB接続のモック設定
    mock_conn = Mock()
    mock_smb_connection.return_value = mock_conn
    
    # 成功ケース
    mock_boto3_client.side_effect = [create_mock_ssm(), create_mock_s3()]
    mock_conn.connect.return_value = True
    mock_conn.listPath.return_value = []
    result = lambda_handler({}, None)
    assert result['statusCode'] == 200
    
    # 接続失敗ケース（False を返す）
    mock_boto3_client.reset_mock()
    mock_boto3_client.side_effect = [create_mock_ssm(), create_mock_s3()]
    mock_conn.reset_mock()
    mock_conn.connect.return_value = False
    result = lambda_handler({}, None)
    assert result['statusCode'] == 500
    assert 'Failed to connect to SMB share' in result['body']
    
    # 接続エラーケース（socket.error）
    mock_boto3_client.reset_mock()
    mock_boto3_client.side_effect = [create_mock_ssm(), create_mock_s3()]
    mock_conn.reset_mock()
    mock_conn.connect.side_effect = socket.error("Connection refused")
    result = lambda_handler({}, None)
    assert result['statusCode'] == 500
    assert 'Connection refused' in result['body']
    
    # SMBConnectionの初期化パラメータを確認
    mock_smb_connection.assert_called_with(
        'testuser',
        'testpass',
        'lambda_client',
        'samba',
        use_ntlm_v2=True
    )

@patch('smarch.handler.boto3.client')
@patch('smarch.handler.SMBConnection')
def test_lambda_handler_file_operations(mock_smb_connection, mock_boto3_client, mock_environment):
    """ファイル操作をテスト"""
    # SSMのモック設定
    mock_ssm = Mock()
    mock_ssm.get_parameter.side_effect = [
        {'Parameter': {'Value': 'testuser'}},
        {'Parameter': {'Value': 'testpass'}}
    ]
    
    # S3のモック設定
    mock_s3 = Mock()
    
    # boto3.clientのモック設定
    mock_boto3_client.side_effect = [mock_ssm, mock_s3]
    
    # SMB接続のモック設定
    mock_conn = Mock()
    mock_smb_connection.return_value = mock_conn
    mock_conn.connect.return_value = True
    
    # テスト用ファイルのモック
    mock_file1 = Mock()
    mock_file1.filename = 'test1.txt'
    mock_file1.isDirectory = False
    
    mock_file2 = Mock()
    mock_file2.filename = 'test_dir'
    mock_file2.isDirectory = True
    
    mock_conn.listPath.return_value = [mock_file1, mock_file2]
    
    # テスト実行
    result = lambda_handler({}, None)
    
    # アサーション
    assert result['statusCode'] == 200
    assert 'test1.txt' in result['body']
    assert 'test_dir' not in result['body']
    
    # ファイル操作の確認
    mock_conn.retrieveFile.assert_called_once()
    mock_s3.upload_file.assert_called_once()
    mock_conn.deleteFiles.assert_called_once()

@patch('smarch.handler.boto3.client')
@patch('smarch.handler.SMBConnection')
def test_lambda_handler_s3_upload(mock_smb_connection, mock_boto3_client, mock_environment):
    """S3アップロード処理をテスト"""
    # SSMのモック設定
    mock_ssm = Mock()
    mock_ssm.get_parameter.side_effect = [
        {'Parameter': {'Value': 'testuser'}},
        {'Parameter': {'Value': 'testpass'}}
    ]
    
    # S3のモック設定
    mock_s3 = Mock()
    
    # boto3.clientのモック設定
    mock_boto3_client.side_effect = [mock_ssm, mock_s3]
    
    # SMB接続のモック設定
    mock_conn = Mock()
    mock_smb_connection.return_value = mock_conn
    mock_conn.connect.return_value = True
    
    # テスト用ファイルのモック
    mock_file = Mock()
    mock_file.filename = 'test.txt'
    mock_file.isDirectory = False
    mock_conn.listPath.return_value = [mock_file]
    
    # テスト実行
    result = lambda_handler({}, None)
    
    # S3アップロードの確認
    mock_s3.upload_file.assert_called_once()
    args = mock_s3.upload_file.call_args[0]
    assert args[0].endswith('test.txt')  # ローカルファイルパス
    assert args[1] == 'test-bucket'      # バケット名
    assert 'archives/' in args[2]         # S3キー
    assert 'test.txt' in args[2]         # ファイル名

@patch('smarch.handler.boto3.client')
def test_lambda_handler_error_handling(mock_boto3_client, mock_environment):
    """エラーハンドリングをテスト"""
    # SSMエラーのケース
    mock_ssm = Mock()
    mock_ssm.get_parameter.side_effect = Exception('SSM Error')
    mock_boto3_client.return_value = mock_ssm
    
    result = lambda_handler({}, None)
    assert result['statusCode'] == 500
    assert 'Error: Exception: SSM Error' in result['body']
    
    # S3エラーのケース
    mock_ssm.reset_mock()
    mock_ssm.get_parameter.side_effect = [
        {'Parameter': {'Value': 'testuser'}},
        {'Parameter': {'Value': 'testpass'}}
    ]
    mock_s3 = Mock()
    mock_s3.upload_file.side_effect = Exception('S3 Error')
    mock_boto3_client.side_effect = [mock_ssm, mock_s3]
    
    with patch('smarch.handler.SMBConnection') as mock_smb_connection:
        mock_conn = Mock()
        mock_smb_connection.return_value = mock_conn
        mock_conn.connect.return_value = True
        
        mock_file = Mock()
        mock_file.filename = 'test.txt'
        mock_file.isDirectory = False
        mock_conn.listPath.return_value = [mock_file]
        
        result = lambda_handler({}, None)
        assert result['statusCode'] == 500
        assert 'Error: Exception: S3 Error' in result['body']
