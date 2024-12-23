import pytest
from smarch.handler import lambda_handler

def test_lambda_handler_success():
    """
    正常系のテストケース
    """
    # TODO: SMBとS3のモックを実装
    event = {}
    context = None
    
    result = lambda_handler(event, context)
    
    assert result['statusCode'] == 200
    assert 'Processed files' in result['body']

def test_lambda_handler_smb_connection_error():
    """
    SMB接続エラーのテストケース
    """
    # TODO: SMB接続エラーのモックを実装
    event = {}
    context = None
    
    result = lambda_handler(event, context)
    
    assert result['statusCode'] == 500
    assert 'Failed to connect' in result['body']
